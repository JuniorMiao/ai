import {
  Alert,
  App as AntApp,
  Button,
  Dropdown,
  Empty,
  Table,
  Typography,
} from 'antd'
import type { MenuProps } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { DownloadOutlined } from '@ant-design/icons'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { listLlmSettings, type LlmSettings } from '../../api/natural'
import { executeQuery, type QueryResult } from '../../api/query'
import SqlEditor from '../../components/SqlEditor'
import {
  buildExportBasename,
  exportQueryResultToCsv,
  exportQueryResultToExcel,
} from '../../utils/exportQueryResult'
import { validateSelectableSql } from '../../utils/validateSelectableSql'
import NaturalQueryPanel, { NL_LLM_CHOICE_KEY } from './NaturalQueryPanel'

const { Text } = Typography

type Props = {
  /** Current logical database; null disables run / NL. */
  selectedDb: string | null
}

/**
 * Read-only SQL workspace: NL panel, Monaco editor, run, results table (Phase 4 / T031).
 * Composed from the main column of the full workspace layout.
 */
export default function SqlQueryPage({ selectedDb }: Props) {
  const { message } = AntApp.useApp()
  const [sql, setSql] = useState('SELECT 1 AS ok;')
  const [sqlSyntaxError, setSqlSyntaxError] = useState<string | null>(null)
  const [queryLoading, setQueryLoading] = useState(false)
  const [exportLoading, setExportLoading] = useState(false)
  const [querySnapshot, setQuerySnapshot] = useState<{
    db: string
    result: QueryResult
  } | null>(null)
  const [nlReady, setNlReady] = useState(false)
  const [llmItems, setLlmItems] = useState<LlmSettings[]>([])
  const [explicitLlmId, setExplicitLlmId] = useState<number | undefined>(undefined)

  const applyStoredLlmChoice = useCallback((items: LlmSettings[]) => {
    try {
      const raw = localStorage.getItem(NL_LLM_CHOICE_KEY)
      if (raw === 'default' || !raw) {
        setExplicitLlmId(undefined)
        return
      }
      const id = Number(raw)
      if (items.some((i) => i.id === id)) setExplicitLlmId(id)
      else setExplicitLlmId(undefined)
    } catch {
      setExplicitLlmId(undefined)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    void listLlmSettings()
      .then((r) => {
        if (cancelled) return
        setNlReady(r.hasResolvableKey)
        setLlmItems(r.items)
        applyStoredLlmChoice(r.items)
      })
      .catch(() => {
        if (!cancelled) {
          setNlReady(false)
          setLlmItems([])
        }
      })
    return () => {
      cancelled = true
    }
  }, [applyStoredLlmChoice])

  const displayQuery =
    selectedDb && querySnapshot?.db === selectedDb ? querySnapshot.result : null

  const runQuery = useCallback(async () => {
    if (!selectedDb) {
      message.warning('请先选择一个数据库连接')
      return
    }
    const trimmed = sql.trim()
    if (!trimmed) {
      message.warning('请输入 SQL')
      return
    }
    const syntax = validateSelectableSql(trimmed)
    if (!syntax.ok) {
      setSqlSyntaxError(syntax.message)
      message.error(syntax.message)
      return
    }
    setSqlSyntaxError(null)
    setQueryLoading(true)
    try {
      const res = await executeQuery(selectedDb, trimmed)
      setQuerySnapshot({ db: selectedDb, result: res })
    } catch (e) {
      message.error(e instanceof Error ? e.message : '查询失败')
    } finally {
      setQueryLoading(false)
    }
  }, [message, selectedDb, sql])

  const resultColumns: ColumnsType<Record<string, unknown>> = useMemo(() => {
    if (!displayQuery?.columns.length) return []
    return displayQuery.columns.map((col: string) => ({
      title: col,
      dataIndex: col,
      key: col,
      ellipsis: true,
      render: (v: unknown) =>
        v === null || v === undefined ? <span className="text-slate-400">∅</span> : String(v),
    }))
  }, [displayQuery])

  const resultRows = useMemo(() => {
    if (!displayQuery) return []
    return displayQuery.rows.map((row: unknown[], i: number) => {
      const rec: Record<string, unknown> = { key: i }
      displayQuery.columns.forEach((c: string, j: number) => {
        rec[c] = row[j]
      })
      return rec
    })
  }, [displayQuery])

  const handleExport = useCallback(
    async (format: 'csv' | 'xlsx') => {
      if (!displayQuery || !selectedDb) return
      const base = buildExportBasename(selectedDb)
      setExportLoading(true)
      try {
        if (format === 'csv') {
          exportQueryResultToCsv(displayQuery.columns, displayQuery.rows, base)
          message.success('已导出 CSV')
        } else {
          await exportQueryResultToExcel(displayQuery.columns, displayQuery.rows, base)
          message.success('已导出 Excel')
        }
      } catch (e) {
        message.error(e instanceof Error ? e.message : '导出失败')
      } finally {
        setExportLoading(false)
      }
    },
    [displayQuery, message, selectedDb],
  )

  const exportMenuItems: MenuProps['items'] = useMemo(
    () => [
      {
        key: 'csv',
        label: '导出 CSV',
        onClick: () => void handleExport('csv'),
      },
      {
        key: 'xlsx',
        label: '导出 Excel (.xlsx)',
        onClick: () => void handleExport('xlsx'),
      },
    ],
    [handleExport],
  )

  return (
    <>
        <section className="shrink-0 border-b border-slate-200 px-4 py-3">
            <NaturalQueryPanel
              dbName={selectedDb}
              nlReady={nlReady}
              llmItems={llmItems}
              explicitLlmId={explicitLlmId}
              onExplicitLlmIdChange={setExplicitLlmId}
              onApplySql={(next) => {
                setSql(next)
                setSqlSyntaxError(null)
              }}
            />
        </section>
      <section className="flex min-h-[240px] shrink-0 flex-col border-b border-slate-200 px-4 py-3">
        <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
          <div>
            <span className="text-sm font-medium text-slate-800">SQL 查询</span>
            <Text type="secondary" className="ml-2 text-xs">
              单条 SELECT · 点击「执行查询」时校验
            </Text>
          </div>
          <Button
            type="primary"
            size="small"
            loading={queryLoading}
            disabled={!selectedDb}
            onClick={() => void runQuery()}
          >
            执行查询
          </Button>
        </div>
        {sqlSyntaxError ? (
          <Alert type="error" showIcon className="mb-2" title={sqlSyntaxError} />
        ) : (
          <Alert
            type="info"
            showIcon
            className="mb-2 py-1 text-xs [&_.ant-alert-title]:text-xs"
            title="仅允许一条 SELECT；点击「执行查询」时在前端校验，通过后请求后端（后端仍会再次校验）。"
          />
        )}
        <SqlEditor
          value={sql}
          onChange={(next: string) => {
            setSql(next)
            setSqlSyntaxError(null)
          }}
        />
      </section>

      <section className="flex min-h-0 flex-1 flex-col">
        <div className="shrink-0 border-b border-slate-100 px-4 py-2 flex flex-wrap items-center justify-between gap-2">
          <span className="text-sm font-medium text-slate-800">查询结果</span>
          <Dropdown menu={{ items: exportMenuItems }} disabled={!displayQuery} trigger={['click']}>
            <Button
              size="small"
              icon={<DownloadOutlined />}
              loading={exportLoading}
              disabled={!displayQuery}
            >
              导出
            </Button>
          </Dropdown>
        </div>
        <div className="min-h-0 flex-1 overflow-auto p-2">
          {!displayQuery ? (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="执行查询成功后，在此显示结果" />
          ) : (
            <>
              {displayQuery.truncated ? (
                <Alert
                  type="info"
                  showIcon
                  className="mb-2"
                  title={`结果已截断至最多 ${displayQuery.maxRows} 行（truncated）`}
                />
              ) : null}
              <Table<Record<string, unknown>>
                size="small"
                bordered
                scroll={{ x: 'max-content' }}
                columns={resultColumns}
                dataSource={resultRows}
                pagination={{ pageSize: 50, showSizeChanger: true, pageSizeOptions: [20, 50, 100] }}
              />
            </>
          )}
        </div>
      </section>
    </>
  )
}
