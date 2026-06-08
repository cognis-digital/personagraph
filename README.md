# PERSONAGRAPH — Identity resolution dossier — username/email/phone cross-platform

> Part of the **[Cognis Neural Suite](https://github.com/cognis-digital)** by [Cognis Digital](https://cognis.digital)
> MIT License · domain: `osint`

[![PyPI](https://img.shields.io/pypi/v/cognis-personagraph.svg)](https://pypi.org/project/cognis-personagraph/)
[![CI](https://github.com/cognis-digital/personagraph/actions/workflows/ci.yml/badge.svg)](https://github.com/cognis-digital/personagraph/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Identity resolution dossier — username/email/phone cross-platform.

## Install

```bash
pip install cognis-personagraph
```

For local development from this repo:

```bash
pip install -e .
```

## Quick start

```bash
personagraph --version
personagraph scan demos/                          # run against bundled demo
personagraph scan demos/ --format sarif --out r.sarif --fail-on high
personagraph mcp                                   # start as MCP server (Cognis.Studio / Claude Desktop / Cursor)
```

## Built-in demo scenarios

Every scenario folder includes a `SCENARIO.md` describing what it represents and what findings to expect.

- `demos/01-employee-due-diligence/` — see [`SCENARIO.md`](demos/01-employee-due-diligence/SCENARIO.md)
- `demos/02-impersonation-investigation/` — see [`SCENARIO.md`](demos/02-impersonation-investigation/SCENARIO.md)
- `demos/03-vendor-vetting/` — see [`SCENARIO.md`](demos/03-vendor-vetting/SCENARIO.md)

## How it fits the Cognis Neural Suite

This tool is one of 52 in the [Cognis Neural Suite](https://github.com/cognis-digital). The full suite + launcher lives at:

- Suite landing: https://cognis.digital
- All 52 repos: https://github.com/cognis-digital
- Cognis.Studio (Enterprise AI Workforce, MCP host): https://cognis.studio

Every Suite tool ships an MCP server, so Cognis.Studio agents can call them as scoped capabilities.

## License

MIT. See [LICENSE](LICENSE).

## About

**[Cognis Digital](https://cognis.digital)** — Wyoming, USA · *Making Tomorrow Better Today: Advanced Cybersecurity, AI Innovation, and Blockchain Expertise.*
