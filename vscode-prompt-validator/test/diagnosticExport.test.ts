import assert from "node:assert/strict";
import test from "node:test";
import type { Diagnostic, Uri } from "vscode";
import { isAgentDocument } from "../src/agentFiles";
import { buildDiagnosticExport } from "../src/diagnosticExport";

function uri(value: string): Uri {
  return { path: value, toString: () => value } as Uri;
}

function diagnostic(message: string, line: number): Diagnostic {
  return {
    message,
    severity: 1,
    source: "promptValidator",
    code: "unknownExtensionOrMcpServerReference",
    range: {
      start: { line, character: 0 },
      end: { line, character: message.length },
    },
  } as Diagnostic;
}

test("buildDiagnosticExport preserves diagnostics and sorts files", () => {
  const result = buildDiagnosticExport(
    [
      {
        uri: uri("file:///workspace/z.agent.md"),
        diagnostics: [diagnostic("Unknown tool 'z'", 2)],
      },
      {
        uri: uri("file:///workspace/a.agent.md"),
        diagnostics: [diagnostic("Unknown tool 'a'", 1)],
      },
    ],
    "2026-08-12T22:40:00.000Z",
  );

  assert.deepEqual(result, {
    schemaVersion: 1,
    generatedAt: "2026-08-12T22:40:00.000Z",
    files: [
      {
        uri: "file:///workspace/a.agent.md",
        diagnostics: [
          {
            source: "promptValidator",
            code: "unknownExtensionOrMcpServerReference",
            message: "Unknown tool 'a'",
            range: {
              start: { line: 1, character: 0 },
              end: { line: 1, character: 16 },
            },
            severity: 1,
          },
        ],
      },
      {
        uri: "file:///workspace/z.agent.md",
        diagnostics: [
          {
            source: "promptValidator",
            code: "unknownExtensionOrMcpServerReference",
            message: "Unknown tool 'z'",
            range: {
              start: { line: 2, character: 0 },
              end: { line: 2, character: 16 },
            },
            severity: 1,
          },
        ],
      },
    ],
  });
});

test("buildDiagnosticExport represents a clean file with no diagnostics", () => {
  const result = buildDiagnosticExport(
    [{ uri: uri("file:///workspace/clean.agent.md"), diagnostics: [] }],
    "2026-08-12T22:40:00.000Z",
  );

  assert.equal(result.files[0]?.diagnostics.length, 0);
});

test("isAgentDocument recognizes agent prompt files case-insensitively", () => {
  assert.equal(isAgentDocument(uri("file:///workspace/.github/agents/tool.agent.md")), true);
  assert.equal(isAgentDocument(uri("file:///workspace/README.md")), false);
  assert.equal(isAgentDocument(uri("file:///workspace/agent.md.bak")), false);
});
