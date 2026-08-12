# Prompt Validator Diagnostics Protocol

This repository can consume a structured snapshot of diagnostics from the VS Code prompt validator. The producer is an optional companion VS Code extension; `promptValidator` is an internal diagnostic source, not a public MCP server or standalone CLI.

## Purpose

The bridge gives an agent or CI adapter the same diagnostic records that VS Code exposes to extensions through `vscode.languages.getDiagnostics(uri)`. It removes the need to scrape editor hover text while keeping the Python analyzer independent of VS Code internals.

The protocol is deliberately a snapshot format. It reports what the editor currently knows for each URI; it does not claim that validation has just run. The producer should revalidate or save the document before exporting when freshness matters.

## Contract

The version 1 schema is [prompt-validator-diagnostics.schema.json](prompt-validator-diagnostics.schema.json). A payload contains:

- `schemaVersion`: the integer protocol version. Version 1 is required by the current Python consumer.
- `generatedAt`: an optional ISO 8601 timestamp for the export operation, not proof of diagnostic freshness.
- `files`: one record per URI, with a `diagnostics` array.
- Each diagnostic contains `message` and a zero-based `range`; `source`, `code`, `severity`, and future metadata are preserved when available.

Example:

```json
{
  "schemaVersion": 1,
  "generatedAt": "2026-08-12T22:40:00Z",
  "files": [
    {
      "uri": "file:///workspace/.github/agents/github.agent.md",
      "diagnostics": [
        {
          "source": "promptValidator",
          "code": "unknownExtensionOrMcpServerReference",
          "message": "Unknown tool 'github.create_issue' will be ignored.",
          "range": {
            "start": {"line": 3, "character": 4},
            "end": {"line": 3, "character": 25}
          }
        }
      ]
    }
  ]
}
```

A clean export is represented by an empty `diagnostics` array. An export with no selected files uses an empty `files` array. A producer must not omit a file to mean clean if that file was selected for validation.

## Producer workflow

The companion extension should:

1. Select workspace `.agent.md` files explicitly.
2. Read diagnostics for each file URI through `vscode.languages.getDiagnostics(uri)`.
3. Preserve the diagnostic source, code, message, severity, and zero-based range when present.
4. Sort file records by URI and diagnostics by range, then message, for deterministic output.
5. Write `.vscode/prompt-diagnostics.json` or provide the same payload through a future transport.

The first implementation should export a workspace artifact. An MCP or stdout adapter can be added later without changing the diagnostic collection or schema.

## Consumer workflow

The Python consumer exposes `unknown_extension_references_from_json(payload)` in `host_selector_resolution.py`. It validates the required version and envelope, extracts diagnostic messages, and reuses `unknown_extension_references()` so structured and legacy text inputs have the same selector semantics.

Malformed structured input raises `ValueError`; it must not be interpreted as a clean validation result. The current text-based diagnostic path remains supported for headless or portable workflows.

## Boundaries

This protocol reports host diagnostics. It does not:

- implement or expose the internal `promptValidator` service;
- infer valid selectors from telemetry or VS Code bundle scraping;
- rewrite `.agent.md` files;
- guarantee that diagnostics are current when an editor has not revalidated a document;
- include unrelated Problems-panel diagnostics unless the producer deliberately selects them.

The companion extension owns VS Code integration and future transport. This repository owns the schema, documentation, and Python consumer.
