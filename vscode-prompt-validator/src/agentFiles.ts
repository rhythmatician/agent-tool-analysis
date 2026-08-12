import type { Uri } from "vscode";

export function isAgentDocument(uri: Uri): boolean {
  return uri.path.toLowerCase().endsWith(".agent.md");
}
