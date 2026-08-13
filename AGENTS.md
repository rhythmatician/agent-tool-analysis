## Agent skills

### Coding

Use YAGNI and DRY principles.

### Issue tracker

Issues live in GitHub Issues via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the default five canonical triage labels. See `docs/agents/triage-labels.md`.

### Domain docs

This is a single-context repo. See `docs/agents/domain.md`.

### VS Code companion

This repository owns the prompt-validator diagnostics schema, protocol, and
Python consumer. The companion TypeScript extension lives in
`vscode-prompt-validator/` and owns live diagnostic collection through
`vscode.languages.getDiagnostics()`, exporting the versioned JSON payload
described in `docs/prompt-validator-protocol.md`. Keep its generated build
output and VSIX lifecycle inside that directory. The existing text diagnostic
path remains supported.
