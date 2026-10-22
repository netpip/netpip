#!/usr/bin/env python3
"""Run every project check for netpip in one go.

Usage (from the project folder):
    python scripts/check_all.py            full check (tests, build, clean install)
    python scripts/check_all.py --quick    skip the build and clean-install steps

Nothing is uploaded anywhere. Exit code is 0 when nothing FAILED
(warnings are allowed), otherwise 1.
"""

import argparse
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = []

REQUIRED_FILES = [
    "README.md",
    "LICENSE",
    "pyproject.toml",
    ".gitignore",
    "src/netpip/__init__.py",
    "src/netpip/__main__.py",
    "src/netpip/cli.py",
    "src/netpip/report.py",
    "src/netpip/includes.py",
    "src/netpip/rules/__init__.py",
    "src/netpip/rules/base.py",
    "src/netpip/rules/grid.py",
    "src/netpip/rules/martingale.py",
    "src/netpip/rules/no_stop_loss.py",
    "src/netpip/rules/stop_loss_input.py",
    "src/netpip/rules/webrequest.py",
]

# Sample EA file -> risk score netpip should report for it.
EXPECTED_SCORES = {
    "safe_ok.mq5": 0,
    "martingale_bad.mq5": 70,
    "no_sl_bad.mq5": 30,
    "webrequest_bad.mq5": 15,
    "grid_bad.mq5": 35,
    "with_include.mq5": 40,
}

SECRET = re.compile(
    r"pypi-[A-Za-z0-9_\-]{40,}|ghp_[A-Za-z0-9]{30,}"
    r"|github_pat_[A-Za-z0-9_]{30,}|sk-[A-Za-z0-9\-]{30,}"
)
PLACEHOLDER = re.compile(r"NAMA_KAMU\w*|Nama Kamu|Your Name|Test Author")


# ---------------------------------------------------------------- helpers

def record(status, name, detail=""):
    RESULTS.append(status)
    line = f"[{status}] {name}"
    if detail:
        line += f" - {detail}"
    print(line)


def run(cmd, cwd=ROOT, timeout=600):
    try:
        done = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return done.returncode, (done.stdout or "") + (done.stderr or "")
    except (OSError, subprocess.TimeoutExpired) as error:
        return 1, str(error)


def tail(text, count=8):
    lines = [line for line in text.splitlines() if line.strip()]
    return "\n".join("        " + line for line in lines[-count:])


def load_text(path):
    """Read a text file. Returns (text, problem). problem is '' when fine."""
    data = path.read_bytes()
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16"), "saved as UTF-16 (should be UTF-8)"
    if b"\x00" in data:
        return data.decode("utf-8", errors="replace"), "contains NUL bytes"
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("utf-8", errors="replace"), "not valid UTF-8"
    problem = "starts with a BOM" if data.startswith(b"\xef\xbb\xbf") else ""
    return text, problem


def outline(text):
    """Return [(line number, level, title)] for markdown headings."""
    result, in_fence = [], False
    for number, line in enumerate(text.splitlines(), start=1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        match = re.match(r"(#{1,6})\s+(\S.*)$", line)
        if match and not in_fence:
            result.append((number, len(match.group(1)), match.group(2).strip()))
    return result


def normalize(text):
    return text.replace("\r\n", "\n").strip()


def is_junk(path):
    parts = path.replace("\\", "/").split("/")
    if any(p in ("dist", "build", "__pycache__", ".pytest_cache") for p in parts[:-1]):
        return True
    if any(p.endswith(".egg-info") for p in parts):
        return True
    return parts[-1] in (".env", ".pypirc") or parts[-1].endswith(".pyc")


# ----------------------------------------------------------------- checks

def check_files():
    missing = [f for f in REQUIRED_FILES if not (ROOT / f).is_file()]
    if missing:
        record("FAIL", "Project files", "missing: " + ", ".join(missing))
    else:
        record("PASS", "Project files", f"{len(REQUIRED_FILES)} required files present")
    empty = [
        str(p.relative_to(ROOT))
        for p in (ROOT / "src").rglob("*.py")
        if p.stat().st_size == 0
    ]
    if empty:
        record("FAIL", "Empty source files", ", ".join(empty))
    else:
        record("PASS", "Empty source files", "none")


def check_metadata():
    path = ROOT / "pyproject.toml"
    if not path.is_file():
        return None
    text, problem = load_text(path)
    if problem:
        record("WARN" if "BOM" in problem else "FAIL", "pyproject.toml encoding", problem)

    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.M)
    version = match.group(1) if match else None
    init_path = ROOT / "src/netpip/__init__.py"
    init_text = load_text(init_path)[0] if init_path.is_file() else ""
    match = re.search(r'__version__\s*=\s*"([^"]+)"', init_text)
    init_version = match.group(1) if match else None
    if version and version == init_version:
        record("PASS", "Version", f"{version} in pyproject.toml and __init__.py")
    else:
        record("FAIL", "Version", f"pyproject.toml={version}, __init__.py={init_version}")

    match = re.search(r"^authors\s*=.*$", text, re.M)
    authors = match.group(0) if match else ""
    if not authors:
        record("WARN", "Author", "no authors line in pyproject.toml")
    elif PLACEHOLDER.search(authors):
        record("WARN", "Author", "still a placeholder: " + authors.strip())
    else:
        record("PASS", "Author", authors.strip())

    if 'license = "Apache-2.0"' in text:
        record("PASS", "License field", "Apache-2.0")
    else:
        record("WARN", "License field", 'expected license = "Apache-2.0"')
    if 'netpip = "netpip.cli:main"' in text:
        record("PASS", "Command entry", "netpip -> netpip.cli:main")
    else:
        record("FAIL", "Command entry", "[project.scripts] netpip entry not found")
    return version


def check_license():
    path = ROOT / "LICENSE"
    if not path.is_file():
        return
    text = load_text(path)[0]
    if "Apache License" in text and "Version 2.0" in text and len(text) >= 10000:
        record("PASS", "LICENSE text", f"full Apache 2.0 text ({len(text)} characters)")
    else:
        record("WARN", "LICENSE text", "looks short or incomplete; use the official Apache 2.0 text")


def check_readme():
    path = ROOT / "README.md"
    if not path.is_file():
        record("FAIL", "README.md", "file not found")
        return None
    text, problem = load_text(path)
    if problem:
        record("WARN" if "BOM" in problem else "FAIL", "README.md encoding", problem)
    lines = text.splitlines()
    if len(text.strip()) < 50:
        record("FAIL", "README.md readable", "empty or almost empty")
        return text
    record("PASS", "README.md readable", f"{len(lines)} lines, {len(text)} characters")

    heads = outline(text)
    print("      README outline:")
    for number, level, title in heads:
        print(f"        line {number:>3}  {'  ' * (level - 1)}{title}")

    body = text.strip()
    half = len(body) // 2
    if len(body) > 200 and body[:half].strip() == body[len(body) - half:].strip():
        record("FAIL", "README doubled", "the whole README is written twice; delete one copy")
        return text

    problems = 0
    counts = Counter(title for _, _, title in heads)
    for title, count in counts.items():
        if count > 1:
            where = [str(n) for n, _, t in heads if t == title]
            level = next(lv for _, lv, t in heads if t == title)
            status = "FAIL" if level == 1 else "WARN"
            record(status, "Duplicate heading", f'"{title}" appears {count} times (lines {", ".join(where)})')
            problems += 1

    paragraphs = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", text)]
    repeated = [p for p, c in Counter(paragraphs).items() if c > 1 and len(p) >= 40]
    if repeated:
        record("WARN", "Repeated paragraphs", f'{len(repeated)} found, for example: "{repeated[0][:50]}..."')
        problems += 1

    fences = sum(1 for line in lines if line.strip().startswith("```"))
    if fences % 2:
        record("WARN", "Code blocks", "a ``` code block is never closed")
        problems += 1

    broken = []
    for target in re.findall(r"\]\(([^)\s]+)\)", text):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        local = target.split("#")[0]
        if local and not (ROOT / local).exists():
            broken.append(target)
    if broken:
        record("WARN", "README links", "relative link target not found: " + ", ".join(broken))
        problems += 1

    if not problems:
        record("PASS", "README structure", "no duplicate headings or repeated text")
    return text


def check_tests():
    code, out = run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"])
    if "No module named pytest" in out:
        record("FAIL", "Tests", "pytest is not installed (python -m pip install pytest)")
        return
    passed = re.search(r"(\d+) passed", out)
    failed = re.search(r"(\d+) failed", out)
    if code == 0 and passed:
        record("PASS", "Tests", f"{passed.group(1)} passed")
    else:
        record("FAIL", "Tests", f"{failed.group(1) + ' failed' if failed else 'did not finish'}")
        print(tail(out, 15))


def wheel_description(wheel):
    with zipfile.ZipFile(wheel) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".dist-info/METADATA"))
        raw = archive.read(name).decode("utf-8", errors="replace")
    parts = re.split(r"\r?\n\r?\n", raw, maxsplit=1)
    return parts[1] if len(parts) > 1 else ""


def check_build(version, readme_text):
    tmp = Path(tempfile.mkdtemp(prefix="netpip-check-"))
    try:
        work = tmp / "project"
        shutil.copytree(
            ROOT,
            work,
            ignore=shutil.ignore_patterns(
                ".git", "dist", "build", "*.egg-info", "__pycache__",
                ".pytest_cache", "*.pyc", ".venv", "venv",
            ),
        )
        dist = tmp / "dist"
        code, out = run([sys.executable, "-m", "build", "--outdir", str(dist)], cwd=work)
        if code != 0:
            hint = "" if "No module named build" not in out else " (python -m pip install build)"
            record("FAIL", "Build", "build failed" + hint)
            print(tail(out))
            return
        wheels = sorted(dist.glob("*.whl"))
        sdists = sorted(dist.glob("*.tar.gz"))
        if not wheels or not sdists:
            record("FAIL", "Build", "wheel or sdist is missing")
            return
        record("PASS", "Build", f"{wheels[0].name} and {sdists[0].name}")

        code, out = run([sys.executable, "-m", "twine", "check"] + [str(p) for p in wheels + sdists])
        if "No module named twine" in out:
            record("FAIL", "twine check", "twine is not installed (python -m pip install twine)")
        elif code == 0:
            record("PASS", "twine check", "PASSED for wheel and sdist")
        else:
            record("FAIL", "twine check", "failed")
            print(tail(out))

        wheel = wheels[0]
        with zipfile.ZipFile(wheel) as archive:
            names = archive.namelist()
            entry = [n for n in names if n.endswith("entry_points.txt")]
            entry_text = archive.read(entry[0]).decode() if entry else ""
        wanted = [
            "netpip/" + p.relative_to(ROOT / "src/netpip").as_posix()
            for p in (ROOT / "src/netpip").rglob("*.py")
        ]
        absent = [w for w in wanted if w not in names]
        if absent:
            record("FAIL", "Package contents", "missing in wheel: " + ", ".join(absent))
        else:
            record("PASS", "Package contents", f"{len(wanted)} modules in the wheel")
        if any(n.endswith("LICENSE") for n in names):
            record("PASS", "LICENSE in package", "included")
        else:
            record("FAIL", "LICENSE in package", "not included in the wheel")
        if "netpip = netpip.cli:main" in entry_text:
            record("PASS", "Command in package", "netpip command is registered")
        else:
            record("FAIL", "Command in package", "netpip command is not registered")
        built = re.match(r"netpip-([^-]+)-", wheel.name)
        if version and built and built.group(1) != version:
            record("FAIL", "Built version", f"wheel is {built.group(1)}, pyproject is {version}")

        if readme_text is not None:
            description = wheel_description(wheel)
            if normalize(description) == normalize(readme_text):
                record("PASS", "README in package", "identical to README.md and shown once")
            else:
                inside = len([h for h in outline(description) if h[1] == 1])
                record("FAIL", "README in package", f"differs from README.md ({inside} top-level heading(s) in the package)")

        venv_dir = tmp / "venv"
        code, out = run([sys.executable, "-m", "venv", str(venv_dir)], cwd=tmp)
        folder, exe = ("Scripts", "python.exe") if sys.platform.startswith("win") else ("bin", "python")
        py = venv_dir / folder / exe
        if code != 0 or not py.is_file():
            record("FAIL", "Clean install", "could not create a test environment")
            print(tail(out))
            return
        code, out = run(
            [str(py), "-m", "pip", "install", "--disable-pip-version-check", "--no-deps", "-q", str(wheel)],
            cwd=tmp,
        )
        if code != 0:
            record("FAIL", "Clean install", "pip install of the wheel failed")
            print(tail(out))
            return
        code, out = run([str(py), "-c", "import netpip; print(netpip.__file__)"], cwd=tmp)
        if code == 0 and "site-packages" in out:
            record("PASS", "Clean install", "installed in a fresh environment, imported from site-packages")
        else:
            record("FAIL", "Clean install", "package is not importable from the fresh environment")
            print(tail(out))
            return
        code, out = run([str(py), "-m", "netpip", "--version"], cwd=tmp)
        expected = f"netpip {version}"
        if code == 0 and out.strip() == expected:
            record("PASS", "netpip --version", out.strip())
        else:
            record("FAIL", "netpip --version", f"expected '{expected}', got '{out.strip()}'")

        samples = ROOT / "tests" / "samples"
        wrong = []
        for name, score in EXPECTED_SCORES.items():
            sample = samples / name
            if not sample.is_file():
                wrong.append(f"{name} (file missing)")
                continue
            code, out = run([str(py), "-m", "netpip", "check", str(sample)], cwd=tmp)
            found = re.search(r"Risk score: (\d+)/100", out)
            if not found or int(found.group(1)) != score:
                wrong.append(f"{name} (expected {score}, got {found.group(1) if found else 'no score'})")
        if wrong:
            record("FAIL", "Sample EA files", "; ".join(wrong))
        else:
            record("PASS", "Sample EA files", f"{len(EXPECTED_SCORES)} samples give the expected scores")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_git():
    code, out = run(["git", "rev-parse", "--is-inside-work-tree"])
    if code != 0:
        record("SKIP", "Git", "not a git repository (or git is not installed)")
        return
    code, out = run(["git", "ls-files"])
    tracked = [line.strip() for line in out.splitlines() if line.strip()]
    junk = [p for p in tracked if is_junk(p)]
    if junk:
        record("FAIL", "Git tracked files", "should not be tracked: " + ", ".join(junk[:5]))
    else:
        record("PASS", "Git tracked files", f"{len(tracked)} files, no build or secret files")
    hits = []
    for name in tracked:
        path = ROOT / name
        if path.is_file() and path.stat().st_size < 1_000_000:
            if SECRET.search(path.read_text(encoding="utf-8", errors="ignore")):
                hits.append(name)
    if hits:
        record("FAIL", "Secrets in tracked files", "possible token in: " + ", ".join(hits))
    else:
        record("PASS", "Secrets in tracked files", "none found")
    code, out = run(["git", "status", "--porcelain"])
    changes = [line for line in out.splitlines() if line.strip()]
    if changes:
        record("WARN", "Git status", f"{len(changes)} uncommitted change(s): " + "; ".join(c.strip() for c in changes[:4]))
    else:
        record("PASS", "Git status", "everything is committed")
    code, out = run(["git", "rev-list", "--count", "@{u}..HEAD"])
    if code == 0 and out.strip().isdigit() and int(out.strip()) > 0:
        record("WARN", "Git push", f"{out.strip()} commit(s) not pushed yet")
    elif code == 0:
        record("PASS", "Git push", "up to date with the remote")


# ------------------------------------------------------------------- main

def main():
    parser = argparse.ArgumentParser(description="Run every netpip project check.")
    parser.add_argument("--quick", action="store_true", help="skip build and clean install")
    args = parser.parse_args()

    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass

    print(f"netpip project check | Python {platform.python_version()} | {platform.system()}")
    print(f"Project folder: {ROOT}")
    print("=" * 60)
    check_files()
    version = check_metadata()
    check_license()
    readme = check_readme()
    check_tests()
    if args.quick:
        record("SKIP", "Build and clean install", "skipped (--quick)")
    else:
        check_build(version, readme)
    check_git()

    print("=" * 60)
    print(
        f"PASS: {RESULTS.count('PASS')}   WARN: {RESULTS.count('WARN')}   "
        f"FAIL: {RESULTS.count('FAIL')}   SKIP: {RESULTS.count('SKIP')}"
    )
    if RESULTS.count("FAIL"):
        print("RESULT: NOT READY - fix the FAIL items above.")
        return 1
    if RESULTS.count("WARN"):
        print("RESULT: OK, but read the WARN items above.")
        return 0
    print("RESULT: ALL GOOD. Nothing was uploaded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
