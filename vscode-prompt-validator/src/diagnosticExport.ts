import type { Diagnostic, Uri } from "vscode";
import type {
  FileDiagnostics,
  PromptDiagnosticsExport,
  SerializedDiagnostic,
} from "./types";

export interface DiagnosticFile {
  uri: Uri;
  diagnostics: readonly Diagnostic[];
}

function serializeCode(
  code: Diagnostic["code"],
): SerializedDiagnostic["code"] {
  if (code === undefined) {
    return null;
  }
  if (typeof code === "string" || typeof code === "number") {
    return code;
  }
  return {
    value: code.value,
    target: code.target?.toString() ?? null,
  };
}

export function serializeDiagnostic(
  diagnostic: Diagnostic,
): SerializedDiagnostic {
  return {
    source: diagnostic.source ?? null,
    code: serializeCode(diagnostic.code),
    message: diagnostic.message,
    range: {
      start: {
        line: diagnostic.range.start.line,
        character: diagnostic.range.start.character,
      },
      end: {
        line: diagnostic.range.end.line,
        character: diagnostic.range.end.character,
      },
    },
    severity: diagnostic.severity,
  };
}

function diagnosticSortKey(diagnostic: SerializedDiagnostic): string {
  return [
    diagnostic.range.start.line,
    diagnostic.range.start.character,
    diagnostic.range.end.line,
    diagnostic.range.end.character,
    diagnostic.message,
  ].join(":");
}

export function buildDiagnosticExport(
  files: readonly DiagnosticFile[],
  generatedAt = new Date().toISOString(),
): PromptDiagnosticsExport {
  const serializedFiles: FileDiagnostics[] = files.map(({ uri, diagnostics }) => ({
    uri: uri.toString(),
    diagnostics: diagnostics.map(serializeDiagnostic).sort((left, right) =>
      diagnosticSortKey(left).localeCompare(diagnosticSortKey(right)),
    ),
  }));

  serializedFiles.sort((left, right) => left.uri.localeCompare(right.uri));
  return {
    schemaVersion: 1,
    generatedAt,
    files: serializedFiles,
  };
}
