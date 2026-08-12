## Agent skills

### Coding

Use YAGNI and DRY principles.

### Issue tracker

Issues live in GitHub Issues via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the default five canonical triage labels. See `docs/agents/triage-labels.md`.

### Domain docs

This is a single-context repo. See `docs/agents/domain.md`.

### Optional VS Code companion

This repository owns the prompt-validator diagnostics schema, protocol, and
Python consumer. An optional companion VS Code extension owns live diagnostic
collection through `vscode.languages.getDiagnostics()` and may export the
versioned JSON payload described in `docs/prompt-validator-protocol.md`.
Keep the extension's TypeScript project and VS Code release lifecycle outside
this Python repository. The existing text diagnostic path remains supported.
