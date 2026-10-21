"""Tests for following local #include files."""

from pathlib import Path

from netpip.cli import main, read_source
from netpip.includes import collect_sources

SAMPLES = Path(__file__).parent / "samples"


def test_collect_sources_follows_local_includes():
    sources, missing = collect_sources(SAMPLES / "with_include.mq5", read_source)
    names = [name for name, _ in sources]
    assert names == ["with_include.mq5", "Include\\risky.mqh"]
    assert missing == ["Include\\absent.mqh"]


def test_cli_reports_findings_in_include_files(capsys):
    exit_code = main(["check", str(SAMPLES / "with_include.mq5")])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "MARTINGALE" in out
    assert "Include\\risky.mqh" in out
    assert "Include\\absent.mqh" in out


def test_include_cycles_do_not_loop_forever(tmp_path):
    first = tmp_path / "a.mq5"
    second = tmp_path / "b.mqh"
    first.write_text('#include "b.mqh"\n')
    second.write_text('#include "a.mq5"\n')
    sources, missing = collect_sources(first, read_source)
    assert len(sources) == 2
    assert missing == []
