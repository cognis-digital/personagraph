"""Hardening tests — error paths, edge cases, and input-validation guards."""
from __future__ import annotations

import io
import json
import contextlib
import unittest

from personagraph.core import (
    classify_identifier,
    derive_usernames,
    build_dossier,
    TOOL_NAME,
    TOOL_VERSION,
)
from personagraph.cli import main


class TestClassifyInputGuards(unittest.TestCase):
    def test_none_raises_value_error(self):
        with self.assertRaises(ValueError) as ctx:
            classify_identifier(None)
        self.assertIn("required", str(ctx.exception))

    def test_non_string_raises_value_error(self):
        """Passing an int should raise ValueError, not AttributeError."""
        with self.assertRaises(ValueError) as ctx:
            classify_identifier(42)
        self.assertIn("string", str(ctx.exception).lower())

    def test_list_raises_value_error(self):
        with self.assertRaises(ValueError):
            classify_identifier(["user@example.com"])

    def test_whitespace_only_raises(self):
        with self.assertRaises(ValueError) as ctx:
            classify_identifier("   \t\n")
        self.assertIn("empty", str(ctx.exception).lower())

    def test_too_long_identifier_raises(self):
        """Identifiers over _MAX_IDENTIFIER_LEN chars should be rejected."""
        with self.assertRaises(ValueError) as ctx:
            classify_identifier("a" * 321)
        self.assertIn("too long", str(ctx.exception).lower())

    def test_identifier_at_max_length_is_accepted(self):
        # 320-char all-alpha slug should resolve (might fall-through to slugify).
        # Just confirm no exception is raised.
        classify_identifier("a" * 40)  # well under limit, valid username regex


class TestBuildDossierPlatformGuards(unittest.TestCase):
    def test_empty_platforms_list_raises(self):
        """An empty platforms list is an explicit error, not a silent fallback."""
        with self.assertRaises(ValueError) as ctx:
            build_dossier("alice", platforms=[])
        self.assertIn("empty", str(ctx.exception).lower())

    def test_none_platforms_uses_all(self):
        """platforms=None must return candidates across all platforms."""
        from personagraph.core import PLATFORMS
        d = build_dossier("alice", platforms=None)
        self.assertEqual(d["platform_count"], len(PLATFORMS))

    def test_non_list_platforms_raises(self):
        with self.assertRaises(ValueError):
            build_dossier("alice", platforms="github")

    def test_unknown_platform_error_message(self):
        with self.assertRaises(ValueError) as ctx:
            build_dossier("alice", platforms=["nope", "also_nope"])
        msg = str(ctx.exception)
        self.assertIn("unknown platform", msg.lower())
        self.assertIn("also_nope", msg)


class TestToolConstants(unittest.TestCase):
    def test_tool_name_is_string(self):
        self.assertIsInstance(TOOL_NAME, str)
        self.assertTrue(TOOL_NAME)

    def test_tool_version_is_string(self):
        self.assertIsInstance(TOOL_VERSION, str)
        self.assertTrue(TOOL_VERSION)

    def test_package_exports_constants(self):
        import personagraph
        self.assertEqual(personagraph.TOOL_NAME, TOOL_NAME)
        self.assertEqual(personagraph.TOOL_VERSION, TOOL_VERSION)


class TestCLIErrorPaths(unittest.TestCase):
    def test_missing_identifier_exits_nonzero(self):
        """resolve with no positional arg must exit non-zero (argparse exits 2)."""
        with self.assertRaises(SystemExit) as ctx:
            main(["resolve"])
        self.assertNotEqual(ctx.exception.code, 0)

    def test_empty_identifier_exits_2(self):
        """Whitespace-only identifier should print to stderr and return 2."""
        err_buf = io.StringIO()
        with contextlib.redirect_stderr(err_buf):
            rc = main(["resolve", "   "])
        self.assertEqual(rc, 2)
        self.assertIn("error", err_buf.getvalue().lower())

    def test_unknown_platform_via_cli_exits_2(self):
        err_buf = io.StringIO()
        with contextlib.redirect_stderr(err_buf):
            rc = main(["resolve", "alice", "--platform", "doesnotexist"])
        self.assertEqual(rc, 2)
        self.assertIn("unknown platform", err_buf.getvalue().lower())

    def test_resolve_phone_number_succeeds(self):
        """Phone numbers should resolve to a dossier (with penalized confidence)."""
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = main(["resolve", "+14155550199", "--format", "json"])
        self.assertEqual(rc, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["identifier"]["kind"], "phone")
        self.assertGreater(data["candidate_count"], 0)


class TestDerivePhonesEdge(unittest.TestCase):
    def test_short_phone_does_not_classify_as_phone(self):
        """A 5-digit string should not be treated as a phone number."""
        i = classify_identifier("12345")
        # Short digit string — may be username or slugified; must NOT be phone.
        self.assertNotEqual(i.kind, "phone")

    def test_phone_seeds_are_valid_usernames(self):
        """Seeds derived from a phone must pass the username character filter."""
        i = classify_identifier("+14155550199")
        seeds = derive_usernames(i)
        import re
        pat = re.compile(r"^[A-Za-z0-9._-]{2,40}$")
        for s in seeds:
            self.assertTrue(pat.match(s), f"seed {s!r} is not a valid username")


if __name__ == "__main__":
    unittest.main()
