"""Smoke tests for PERSONAGRAPH. No network access."""
import json
import io
import contextlib
import unittest

from personagraph import (
    TOOL_NAME, TOOL_VERSION, classify_identifier, derive_usernames,
    build_dossier, PLATFORMS,
)
from personagraph.cli import main


class TestClassify(unittest.TestCase):
    def test_email(self):
        i = classify_identifier("Ada.Lovelace+jobs@Gmail.com")
        self.assertEqual(i.kind, "email")
        self.assertEqual(i.normalized, "ada.lovelace+jobs@gmail.com")
        self.assertEqual(i.local_part, "ada.lovelace+jobs")
        self.assertEqual(i.domain, "gmail.com")

    def test_username(self):
        i = classify_identifier("ada_lovelace")
        self.assertEqual(i.kind, "username")
        self.assertEqual(i.normalized, "ada_lovelace")

    def test_phone(self):
        i = classify_identifier("+1 (415) 555-0199")
        self.assertEqual(i.kind, "phone")
        self.assertEqual(i.local_part, "14155550199")

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            classify_identifier("   ")


class TestDerive(unittest.TestCase):
    def test_email_splits_dotted_name_and_strips_tag(self):
        i = classify_identifier("ada.lovelace+jobs@gmail.com")
        seeds = derive_usernames(i)
        self.assertIn("adalovelace", seeds)
        self.assertIn("ada", seeds)
        # tagged form should not survive as a clean username variant in seeds
        self.assertNotIn("ada.lovelace+jobs", seeds)

    def test_username_variants_dedup(self):
        i = classify_identifier("the_user")
        seeds = derive_usernames(i)
        self.assertEqual(seeds[0], "the_user")
        self.assertEqual(len(seeds), len(set(seeds)))


class TestDossier(unittest.TestCase):
    def test_structure_and_sorting(self):
        d = build_dossier("ada.lovelace@gmail.com")
        self.assertEqual(d["tool"], "personagraph")
        self.assertTrue(d["candidate_count"] > 0)
        confs = [c["confidence"] for c in d["candidates"]]
        self.assertEqual(confs, sorted(confs, reverse=True))
        for c in d["candidates"]:
            self.assertTrue(0.0 <= c["confidence"] <= 1.0)
            self.assertTrue(c["url"].startswith("http"))

    def test_platform_filter(self):
        d = build_dossier("adalovelace", platforms=["github"])
        self.assertEqual(d["platform_count"], 1)
        self.assertTrue(all(c["platform"] == "github" for c in d["candidates"]))

    def test_unknown_platform_raises(self):
        with self.assertRaises(ValueError):
            build_dossier("adalovelace", platforms=["nope"])

    def test_deterministic(self):
        a = build_dossier("ada.lovelace@gmail.com")
        b = build_dossier("ada.lovelace@gmail.com")
        self.assertEqual(a, b)


class TestCLI(unittest.TestCase):
    def test_resolve_json(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = main(["resolve", "adalovelace", "--format", "json"])
        self.assertEqual(rc, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["tool"], "personagraph")

    def test_resolve_table(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = main(["resolve", "adalovelace"])
        self.assertEqual(rc, 0)
        self.assertIn("PERSONAGRAPH dossier", buf.getvalue())

    def test_platforms_command(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = main(["platforms", "--format", "json"])
        self.assertEqual(rc, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(set(data.keys()), set(PLATFORMS.keys()))

    def test_bad_identifier_nonzero(self):
        rc = main(["resolve", "   "])
        self.assertEqual(rc, 2)

    def test_version_constants(self):
        self.assertEqual(TOOL_NAME, "personagraph")
        self.assertTrue(TOOL_VERSION)


if __name__ == "__main__":
    unittest.main()
