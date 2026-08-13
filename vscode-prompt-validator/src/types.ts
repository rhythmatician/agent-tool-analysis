export interface SerializedPosition {
  line: number;
  character: number;
}

export interface SerializedRange {
  start: SerializedPosition;
  end: SerializedPosition;
}

export interface SerializedDiagnostic {
  source: string | null;
  code: string | number | Record<string, unknown> | null;
  message: string;
  range: SerializedRange;
  severity: number;
}

export interface FileDiagnostics {
  uri: string;
  diagnostics: SerializedDiagnostic[];
}

export interface PromptDiagnosticsExport {
  schemaVersion: 1;
  generatedAt: string;
  files: FileDiagnostics[];
}
