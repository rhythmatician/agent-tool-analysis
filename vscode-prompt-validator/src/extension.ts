import * as vscode from "vscode";
import { isAgentDocument } from "./agentFiles";
import { buildDiagnosticExport } from "./diagnosticExport";
import type { PromptDiagnosticsExport } from "./types";

const COMMAND = "promptValidatorDiagnostics.exportJson";
const OUTPUT_FILE = "prompt-diagnostics.json";
const AUTO_EXPORT_DELAY_MS = 250;

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
  let exportTimer: ReturnType<typeof setTimeout> | undefined;
  let queuedExport = Promise.resolve();

  const queueAutomaticExport = (): void => {
    if (exportTimer) {
      clearTimeout(exportTimer);
    }
    exportTimer = setTimeout(() => {
      exportTimer = undefined;
      queuedExport = queuedExport.then(async () => {
        try {
          await exportPromptDiagnostics();
        } catch (error) {
          console.error("Prompt diagnostics automatic export failed.", error);
        }
      });
    }, AUTO_EXPORT_DELAY_MS);
  };

  const diagnosticsSubscription = vscode.languages.onDidChangeDiagnostics(
    (event) => {
      if (event.uris.some(isAgentDocument)) {
        queueAutomaticExport();
      }
    },
  );
  context.subscriptions.push(diagnosticsSubscription, {
    dispose: () => {
      if (exportTimer) {
        clearTimeout(exportTimer);
      }
    },
  });
  queueAutomaticExport();

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
