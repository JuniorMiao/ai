import dataProvider from '@refinedev/simple-rest'
import '@refinedev/antd/dist/reset.css'
import { Refine } from '@refinedev/core'
import routerProvider from '@refinedev/react-router'
import { App as AntApp, ConfigProvider, theme } from 'antd'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import WorkspacePage from './pages/WorkspacePage'

const apiUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

export default function App() {
  return (
    <BrowserRouter>
      <ConfigProvider theme={{ algorithm: theme.defaultAlgorithm }}>
        <AntApp>
          <Refine
            routerProvider={routerProvider}
            dataProvider={dataProvider(apiUrl)}
            resources={[
              {
                name: 'workspace',
                list: '/',
              },
            ]}
          >
            <Routes>
              <Route path="/" element={<WorkspacePage />} />
            </Routes>
          </Refine>
        </AntApp>
      </ConfigProvider>
    </BrowserRouter>
  )
}
