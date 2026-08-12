import * as vscode from "vscode";
import { buildDiagnosticExport } from "./diagnosticExport";
import type { PromptDiagnosticsExport } from "./types";

const COMMAND = "promptValidatorDiagnostics.exportJson";
const OUTPUT_FILE = "prompt-diagnostics.json";

export async function exportPromptDiagnostics(): Promise<{
  outputUri: vscode.Uri;
  export: PromptDiagnosticsExport;
}> {
  const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
  if (!workspaceFolder) {
    throw new Error("Open a workspace before exporting prompt diagnostics.");
  }

  const agentUris = await vscode.workspace.findFiles(
    "**/*.agent.md",
    "**/{node_modules,.git}/**",
  );
  const files = agentUris.map((uri) => ({
    uri,
    diagnostics: vscode.languages.getDiagnostics(uri),
  }));
  const diagnosticExport = buildDiagnosticExport(files);
  const outputUri = vscode.Uri.joinPath(
    workspaceFolder.uri,
    ".vscode",
    OUTPUT_FILE,
  );

  await vscode.workspace.fs.createDirectory(vscode.Uri.joinPath(workspaceFolder.uri, ".vscode"));
  await vscode.workspace.fs.writeFile(
    outputUri,
    Buffer.from(JSON.stringify(diagnosticExport, null, 2) + "\n", "utf8"),
  );
  return { outputUri, export: diagnosticExport };
}

export function activate(context: vscode.ExtensionContext): void {
  const disposable = vscode.commands.registerCommand(COMMAND, async () => {
    try {
      const result = await exportPromptDiagnostics();
      vscode.window.showInformationMessage(
        `Exported diagnostics for ${result.export.files.length} agent file(s) to ${result.outputUri.fsPath}.`,
      );
      return result.outputUri;
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      vscode.window.showErrorMessage(`Prompt diagnostics export failed: ${message}`);
      throw error;
    }
  });
  context.subscriptions.push(disposable);
}

export function deactivate(): void {}
