import Editor from '@monaco-editor/react'

type Props = {
  value: string
  onChange: (value: string) => void
  /** CSS height, e.g. `188px` */
  height?: string
}

/** Thin Monaco wrapper for SQL editing (Phase 4 / T030). */
export default function SqlEditor({ value, onChange, height = '188px' }: Props) {
  return (
    <div className="min-h-[188px] overflow-hidden rounded border border-slate-200">
      <Editor
        height={height}
        defaultLanguage="sql"
        value={value}
        onChange={(v) => onChange(v ?? '')}
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          scrollBeyondLastLine: false,
          wordWrap: 'on',
        }}
      />
    </div>
  )
}
