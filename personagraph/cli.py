"""Command-line interface for PERSONAGRAPH."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from . import TOOL_NAME, TOOL_VERSION
from .core import build_dossier, PLATFORMS


def _render_table(dossier: dict) -> str:
    ident = dossier["identifier"]
    lines: List[str] = []
    lines.append(f"PERSONAGRAPH dossier  v{dossier['version']}")
    lines.append("=" * 60)
    lines.append(f"Input        : {dossier['input']}")
    lines.append(f"Kind         : {ident['kind']}")
    lines.append(f"Normalized   : {ident['normalized']}")
    lines.append(f"Fingerprint  : {dossier['fingerprint']}")
    lines.append(f"Seeds        : {', '.join(dossier['seed_usernames']) or '(none)'}")
    lines.append(f"Candidates   : {dossier['candidate_count']}  "
                 f"(overall confidence {dossier['overall_confidence']:.2f})")
    lines.append("-" * 60)
    lines.append(f"{'CONF':>5}  {'PLATFORM':<12} {'USERNAME':<18} URL")
    lines.append("-" * 60)
    for c in dossier["candidates"]:
        lines.append(f"{c['confidence']:>5.2f}  {c['name']:<12} {c['username']:<18} {c['url']}")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog=TOOL_NAME,
        description="PERSONAGRAPH - cross-platform identity resolution dossier "
                    "for a username, email, or phone number.",
    )
    p.add_argument("--version", action="version",
                   version=f"{TOOL_NAME} {TOOL_VERSION}")
    sub = p.add_subparsers(dest="command", required=True)

    res = sub.add_parser("resolve", help="resolve an identifier into a dossier")
    res.add_argument("identifier", help="username, email, or phone number")
    res.add_argument("--format", choices=["table", "json"], default="table",
                     help="output format (default: table)")
    res.add_argument("--platform", action="append", metavar="KEY",
                     help="restrict to a platform (repeatable); "
                          "see 'platforms' for keys")

    pl = sub.add_parser("platforms", help="list the supported platform catalog")
    pl.add_argument("--format", choices=["table", "json"], default="table")

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "platforms":
            data = {k: {"name": v["name"], "category": v["category"],
                        "weight": v["weight"], "url": v["url"]}
                    for k, v in PLATFORMS.items()}
            if args.format == "json":
                print(json.dumps(data, indent=2))
            else:
                print(f"{'KEY':<12} {'NAME':<12} {'CATEGORY':<10} WEIGHT")
                print("-" * 44)
                for k, v in data.items():
                    print(f"{k:<12} {v['name']:<12} {v['category']:<10} {v['weight']}")
            return 0

        if args.command == "resolve":
            dossier = build_dossier(args.identifier, platforms=args.platform)
            if args.format == "json":
                print(json.dumps(dossier, indent=2))
            else:
                print(_render_table(dossier))
            return 0

    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover - defensive
        print(f"unexpected error: {exc}", file=sys.stderr)
        return 1

    parser.print_help(sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
