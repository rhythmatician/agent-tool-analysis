# Prompt Validator Diagnostics

A small VS Code extension that exports the diagnostics currently published for workspace `.agent.md` files as structured JSON.

## Development

```powershell
npm install
npm test
```

## Use in VS Code

1. Open this project in VS Code.
2. Press `F5` to launch an Extension Development Host.
3. Open the repository containing the `.agent.md` files you want to inspect in that host.
4. Run **Prompt Validator: Export Diagnostics as JSON** from the Command Palette.
5. The extension writes `.vscode/prompt-diagnostics.json` in the opened workspace.

For a normal VS Code profile, run `npm run package` and install the generated
`.vsix` through **Extensions: Install from VSIX...** instead of using an
Extension Development Host.

The export is a snapshot of `vscode.languages.getDiagnostics(uri)`. It does not force VS Code's internal prompt validator to re-run, so save or otherwise revalidate edited files before exporting when freshness matters.

The output follows the parent repository's [protocol](../docs/prompt-validator-protocol.md) and [schema](../docs/prompt-validator-diagnostics.schema.json). The Python consumer can inspect unknown selectors with:

```powershell
C:/Python314/python.exe -c "import json,sys; sys.path.insert(0,'../scripts'); from optimize_agent_tools.host_selector_resolution import unknown_extension_references_from_json; print(unknown_extension_references_from_json(json.load(open('.vscode/prompt-diagnostics.json', encoding='utf-8'))))"
```
