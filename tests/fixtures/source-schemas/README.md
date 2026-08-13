# Synthetic source-schema fixtures

These files are deliberately invented fixtures for adapter contract tests. They
contain no real interaction data and must never be used as a private corpus.

- `claude-multiblock.jsonl` covers text mixed with known image/document/tool
  blocks and a filtered synthetic reminder.
- `codex-multiblock.jsonl` covers `session_meta`, `turn_context`, the `ts`
  timestamp alias, and an image-only user event.
- `kimi/sessions/.../wire.jsonl` plus `kimi/session_index.jsonl` covers text
  block arrays and steering turns.
- `gemini.json` stores the binary protobuf fields as hex so the fixture remains
  reviewable text; the test materializes a temporary SQLite database.

The expected behavior is asserted in `tests/test_pipeline.py`. If an upstream
source schema changes, extend the smallest relevant fixture and keep the test
fail-closed for unknown shapes.
