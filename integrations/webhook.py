#!/usr/bin/env python3
"""Minimal, dependency-free webhook forwarder for Cognis findings.

Reads JSON findings on stdin and POSTs them to a URL (SIEM/Slack/Jira bridge).
Usage:  <tool> scan . --format json | python integrations/webhook.py --url URL
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from urllib.error import URLError


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Post JSON findings from stdin to a webhook URL."
    )
    ap.add_argument("--url", required=True, help="Destination URL")
    ap.add_argument("--header", action="append", default=[], help="Key: Value")
    ap.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="HTTP timeout in seconds (default: 15)",
    )
    args = ap.parse_args()

    raw = sys.stdin.read()
    if not raw.strip():
        print("error: no input received on stdin", file=sys.stderr)
        return 2

    # Validate the payload is parseable JSON before we send it.
    try:
        json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"error: stdin is not valid JSON: {exc}", file=sys.stderr)
        return 2

    if args.timeout <= 0:
        print("error: --timeout must be a positive number", file=sys.stderr)
        return 2

    payload = raw.encode("utf-8")
    req = urllib.request.Request(args.url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    for h in args.header:
        k, _, v = h.partition(":")
        if not k.strip():
            print(f"error: malformed --header value: {h!r}", file=sys.stderr)
            return 2
        req.add_header(k.strip(), v.strip())

    try:
        with urllib.request.urlopen(req, timeout=args.timeout) as r:
            print(f"posted {len(payload)} bytes -> {r.status}")
        return 0
    except URLError as exc:
        print(f"webhook error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"webhook error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
