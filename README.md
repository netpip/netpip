# netpip

Command-line risk checks for MetaTrader 5 Expert Advisors (EAs).

netpip reads the source code of an EA (`.mq5`) and looks for risky patterns
before you run it with real money.

**Status:** early release (0.1.0). Only the `check` command exists so far.

## Install

    pipx install netpip

or, with pip:

    python -m pip install netpip

## Usage

    netpip check MyBot.mq5

Example output (shortened):

    netpip check: grid_bad.mq5

    [DANGER] line 2: GRID_NO_LIMIT
        Grid pattern found and no limit on open positions was found.

    Risk score: 35/100 (MEDIUM)

## What it checks

| Rule | Level | What it looks for |
|------|-------|-------------------|
| MARTINGALE | DANGER | Lot size multiplied (for example `lot *= 2`) |
| NO_STOP_LOSS | DANGER | Buy/Sell calls with a stop loss of 0 |
| GRID_NO_LIMIT | DANGER | Grid pattern with no limit on open positions |
| GRID_WITH_LIMIT | WARNING | Grid pattern where the limit should be verified |
| SL_INPUT_ZERO | WARNING | Stop loss input whose default value is 0 |
| WEBREQUEST | WARNING | Use of WebRequest (internet access) |

## Limitations

- netpip is pattern-based. It can produce false positives and false negatives.
- It follows local `#include "..."` files. Library includes (`<...>`) are not
  followed, and missing include files are listed in the report.
- It reads source code (`.mq5`), not compiled files (`.ex5`).
- A low score does not prove an EA is safe or profitable.

## Disclaimer

netpip is an independent project and is not affiliated with MetaQuotes.
It is not financial advice. Trading involves risk. Use at your own risk.

## Contributing

Each rule lives in its own file in `src/netpip/rules/` and has tests in
`tests/`. Contribution guidelines are coming soon.

## License

Apache License 2.0. See [LICENSE](LICENSE).

The name "netpip" is reserved by the project owner and is not licensed
under Apache-2.0.
