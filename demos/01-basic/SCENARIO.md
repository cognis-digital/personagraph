# Demo 01 - Basic identity resolution

PERSONAGRAPH takes a single identifier (username, email, or phone) and builds a
cross-platform dossier: it classifies the input, derives candidate usernames,
expands them across a catalog of platforms, and scores each candidate by
confidence. The engine is fully offline and deterministic, so output is
reproducible and unit-testable.

## Input

See `input.txt` for the realistic identifier used in this demo:

```
ada.lovelace+jobs@gmail.com
```

This email exercises the interesting derivation paths:
- `+jobs` sub-address tag is stripped,
- `ada.lovelace` is split into `adalovelace` and `ada`,
- dotted/undotted variants are generated.

## Run it

List the supported platform catalog:

```
python -m personagraph platforms
```

Resolve the demo email to a human-readable dossier:

```
python -m personagraph resolve "$(cat demos/01-basic/input.txt)"
```

Get machine-readable JSON (pipe into jq, store as evidence, etc.):

```
python -m personagraph resolve "ada.lovelace+jobs@gmail.com" --format json
```

Focus on developer platforms only:

```
python -m personagraph resolve "ada.lovelace@gmail.com" --platform github --platform pypi
```

## What to expect

- The `identifier` block shows `kind: email`, normalized form, and split parts.
- `seed_usernames` contains the ranked candidate handles (e.g. `adalovelace`,
  `ada`).
- Each `candidates` entry has a target `url` and a `confidence` in `[0, 1]`.
  Dev-platform candidates from an email seed get a small confidence boost
  because developers tend to reuse handles.
- Take the emitted `url` values to a network probe step to confirm live hits;
  the core never touches the network.
