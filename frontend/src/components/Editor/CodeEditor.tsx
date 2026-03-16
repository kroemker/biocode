import MonacoEditor from "@monaco-editor/react";

interface Props {
  value: string;
  onChange: (value: string) => void;
  language?: string;
  readOnly?: boolean;
}

/**
 * Wrapper around Monaco Editor.
 * The `language` prop accepts any Monaco-supported language ID or a custom
 * language registered via monaco.languages.register() (e.g. "rulix").
 */
export function CodeEditor({ value, onChange, language = "plaintext", readOnly = false }: Props) {
  return (
    <MonacoEditor
      height="100%"
      language={language}
      value={value}
      onChange={(v) => onChange(v ?? "")}
      options={{
        readOnly,
        minimap: { enabled: false },
        fontSize: 14,
        lineNumbers: "on",
        scrollBeyondLastLine: false,
        automaticLayout: true,
      }}
    />
  );
}
