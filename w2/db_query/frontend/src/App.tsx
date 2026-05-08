import dataProvider from '@refinedev/simple-rest'
import '@refinedev/antd/dist/reset.css'
import { Refine } from '@refinedev/core'
import routerProvider from '@refinedev/react-router'
import { ConfigProvider, theme } from 'antd'
import Editor from '@monaco-editor/react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'

const apiUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

function Home() {
  return (
    <div className="min-h-screen bg-slate-50 p-6 text-left">
      <h1 className="mb-4 text-2xl font-semibold text-slate-900">db_query</h1>
      <p className="mb-2 text-slate-600">
        Phase 1 scaffold — Refine, Ant Design, Tailwind, Monaco (see{' '}
        <code className="rounded bg-slate-200 px-1">tasks.md</code>).
      </p>
      <div className="overflow-hidden rounded border border-slate-200 bg-white">
        <Editor
          height="160px"
          defaultLanguage="sql"
          defaultValue="SELECT 1 AS ok;"
          options={{ minimap: { enabled: false }, fontSize: 14 }}
        />
      </div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <ConfigProvider theme={{ algorithm: theme.defaultAlgorithm }}>
        <Refine
          routerProvider={routerProvider}
          dataProvider={dataProvider(apiUrl)}
          resources={[]}
        >
          <Routes>
            <Route path="/" element={<Home />} />
          </Routes>
        </Refine>
      </ConfigProvider>
    </BrowserRouter>
  )
}
