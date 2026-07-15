# Contributing

Contributions are welcome for deterministic adapters, safety gates, documentation,
and generic templates. Never submit real interaction logs, generated user profiles,
filled avatar documents, credentials, or private paths.

## Development check

The runtime is Python 3.10+ and uses only the standard library. Install the pinned
development linter, then run the same gates as CI:

```text
python -m pip install ruff==0.15.18
python -m compileall -q scripts tests
python -m unittest discover -s tests -v
ruff check .
```

Adapter changes need synthetic fixtures that cover the source schema, artifact
filtering, context propagation, timestamps, redaction, and fail-closed output. Do
not use personal logs as fixtures. Security reports belong in GitHub Private
Vulnerability Reporting rather than public issues.
