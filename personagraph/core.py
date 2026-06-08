"""Core identity-resolution engine for PERSONAGRAPH.

The engine is deterministic and offline. It:
  1. classifies an input identifier (username / email / phone),
  2. derives a normalized set of candidate usernames,
  3. expands those across a catalog of platforms into target URLs,
  4. scores each candidate target with a confidence heuristic,
  5. assembles a ranked dossier.

No network access is performed here, which makes the logic fully
unit-testable. A caller can take the emitted `url` fields and probe them.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

# --- Platform catalog -------------------------------------------------------
# Each entry: key -> (display name, url template with {u}, category, base_weight)
PLATFORMS: Dict[str, Dict[str, object]] = {
    "github":    {"name": "GitHub",     "url": "https://github.com/{u}",            "category": "dev",    "weight": 0.9},
    "gitlab":    {"name": "GitLab",     "url": "https://gitlab.com/{u}",            "category": "dev",    "weight": 0.8},
    "reddit":    {"name": "Reddit",     "url": "https://www.reddit.com/user/{u}",   "category": "social", "weight": 0.7},
    "twitter":   {"name": "X/Twitter",  "url": "https://x.com/{u}",                 "category": "social", "weight": 0.6},
    "instagram": {"name": "Instagram",  "url": "https://www.instagram.com/{u}",     "category": "social", "weight": 0.6},
    "medium":    {"name": "Medium",     "url": "https://medium.com/@{u}",           "category": "blog",   "weight": 0.7},
    "keybase":   {"name": "Keybase",    "url": "https://keybase.io/{u}",            "category": "identity","weight": 0.95},
    "hackernews":{"name": "Hacker News","url": "https://news.ycombinator.com/user?id={u}","category": "dev","weight": 0.75},
    "pypi":      {"name": "PyPI",       "url": "https://pypi.org/user/{u}/",        "category": "dev",    "weight": 0.8},
    "steam":     {"name": "Steam",      "url": "https://steamcommunity.com/id/{u}", "category": "gaming", "weight": 0.6},
}

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_RE = re.compile(r"[0-9]")
_USERNAME_RE = re.compile(r"^[A-Za-z0-9._-]{2,40}$")
_NONWORD_RE = re.compile(r"[^a-z0-9]+")


@dataclass
class Identifier:
    raw: str
    kind: str            # 'username' | 'email' | 'phone'
    normalized: str
    local_part: Optional[str] = None   # email local part / phone digits
    domain: Optional[str] = None       # email domain

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Candidate:
    platform: str
    name: str
    category: str
    username: str
    url: str
    confidence: float
    rationale: str

    def to_dict(self) -> dict:
        return asdict(self)


def classify_identifier(raw: str) -> Identifier:
    """Detect whether `raw` is an email, phone number, or username."""
    if raw is None:
        raise ValueError("identifier is required")
    s = raw.strip()
    if not s:
        raise ValueError("identifier is empty")

    if _EMAIL_RE.match(s):
        local, domain = s.rsplit("@", 1)
        return Identifier(raw=raw, kind="email", normalized=s.lower(),
                          local_part=local.lower(), domain=domain.lower())

    # Phone: strip formatting; if it's mostly digits and >=7 long, treat as phone.
    digits = re.sub(r"[^0-9]", "", s)
    cleaned = re.sub(r"[\s().+-]", "", s)
    if len(digits) >= 7 and cleaned == digits or (s.startswith("+") and len(digits) >= 7):
        return Identifier(raw=raw, kind="phone", normalized="+" + digits if s.startswith("+") else digits,
                          local_part=digits)

    if _USERNAME_RE.match(s):
        return Identifier(raw=raw, kind="username", normalized=s.lower())

    # Fallback: slugify whatever we got into a username.
    slug = _NONWORD_RE.sub("", s.lower())
    if not slug:
        raise ValueError(f"cannot derive any usable identifier from {raw!r}")
    return Identifier(raw=raw, kind="username", normalized=slug)


def _slug(s: str) -> str:
    return _NONWORD_RE.sub("", s.lower())


def derive_usernames(ident: Identifier) -> List[str]:
    """Produce an ordered, deduplicated list of candidate usernames.

    The first element is the highest-confidence seed.
    """
    seeds: List[str] = []

    def add(u: Optional[str]) -> None:
        if not u:
            return
        u = u.strip().lower()
        if u and u not in seeds and _USERNAME_RE.match(u):
            seeds.append(u)

    if ident.kind == "username":
        base = ident.normalized
        add(base)
        add(_slug(base))
        # common separator-stripped and dotted variants
        add(base.replace("_", ""))
        add(base.replace(".", ""))
        add(base.replace("-", ""))
    elif ident.kind == "email":
        local = ident.local_part or ""
        # strip +tag (gmail-style sub-addressing)
        local_no_tag = local.split("+", 1)[0]
        add(local)
        add(local_no_tag)
        add(_slug(local_no_tag))
        add(local_no_tag.replace(".", ""))
        # firstname.lastname -> firstnamelastname / firstname
        if "." in local_no_tag:
            parts = [p for p in local_no_tag.split(".") if p]
            add("".join(parts))
            if parts:
                add(parts[0])
    elif ident.kind == "phone":
        # phones rarely map to usernames; offer the raw digit string as a weak seed
        digits = ident.local_part or ""
        if len(digits) >= 7:
            add("user" + digits[-7:])
    return seeds


def _confidence(base_weight: float, seed_index: int, ident: Identifier, platform_key: str) -> float:
    """Heuristic confidence in [0, 1].

    - Higher platform base weight => higher confidence.
    - The first derived seed is more trustworthy than later variants.
    - Email-sourced dev platforms get a small boost (devs reuse handles).
    - Phone-sourced seeds are penalized (weak linkage).
    """
    score = base_weight
    score *= max(0.4, 1.0 - 0.18 * seed_index)
    if ident.kind == "email" and PLATFORMS[platform_key]["category"] == "dev":
        score *= 1.08
    if ident.kind == "phone":
        score *= 0.45
    return round(min(1.0, max(0.0, score)), 4)


def build_dossier(raw: str, platforms: Optional[List[str]] = None) -> dict:
    """Build a full identity-resolution dossier for `raw`."""
    ident = classify_identifier(raw)
    seeds = derive_usernames(ident)
    keys = platforms or list(PLATFORMS.keys())

    unknown = [k for k in keys if k not in PLATFORMS]
    if unknown:
        raise ValueError(f"unknown platform(s): {', '.join(unknown)}")

    candidates: List[Candidate] = []
    for i, seed in enumerate(seeds):
        for key in keys:
            spec = PLATFORMS[key]
            url = str(spec["url"]).format(u=seed)
            conf = _confidence(float(spec["weight"]), i, ident, key)
            rationale = f"seed '{seed}' (variant #{i}) on {spec['name']} [{spec['category']}]"
            candidates.append(Candidate(
                platform=key, name=str(spec["name"]), category=str(spec["category"]),
                username=seed, url=url, confidence=conf, rationale=rationale,
            ))

    candidates.sort(key=lambda c: (-c.confidence, c.platform, c.username))

    fingerprint = hashlib.sha256(ident.normalized.encode("utf-8")).hexdigest()[:16]
    overall = round(
        (sum(c.confidence for c in candidates) / len(candidates)) if candidates else 0.0, 4
    )

    return {
        "tool": "personagraph",
        "version": "1.0.0",
        "input": raw,
        "identifier": ident.to_dict(),
        "fingerprint": fingerprint,
        "seed_usernames": seeds,
        "platform_count": len(keys),
        "candidate_count": len(candidates),
        "overall_confidence": overall,
        "candidates": [c.to_dict() for c in candidates],
    }
