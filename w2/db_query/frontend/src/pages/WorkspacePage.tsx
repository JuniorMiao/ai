import { DeleteOutlined, ReloadOutlined } from '@ant-design/icons'
import {
  App as AntApp,
  Button,
  Empty,
  Form,
  Input,
  Popconfirm,
  Select,
  Space,
  Spin,
  Tooltip,
  Typography,
} from 'antd'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import SchemaCatalog from '../components/SchemaCatalog'
import {
  deleteDatabase,
  getDatabaseMetadata,
  listDatabases,
  putDatabase,
  refreshDatabaseMetadata,
  type DatabaseMetadataResponse,
  type RegisteredDatabaseListItem,
} from '../api/databases'
import SqlQueryPage from './query/SqlQueryPage'

const { Text } = Typography

function inferBackendKindFromUrl(url: string): string | undefined {
  const u = url.trim().toLowerCase()
  if (u.startsWith('mysql://') || u.startsWith('mysql+pymysql://') || u.startsWith('mariadb://')) {
    return 'mysql'
  }
  if (u.startsWith('postgres://') || u.startsWith('postgresql://')) {
    return 'postgres'
  }
  return undefined
}

type MetadataPayload = {
  schemas?: string[]
  tables?: {
    schema: string
    name: string
    type: string
    columns: {
      name: string
      dataType: string
      nullable: boolean
      comment?: string
    }[]
  }[]
}

export default function WorkspacePage() {
  const { message } = AntApp.useApp()
  const [form] = Form.useForm()
  const [searchParams, setSearchParams] = useSearchParams()

  const [listLoading, setListLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [connections, setConnections] = useState<RegisteredDatabaseListItem[]>([])
  const [refreshingName, setRefreshingName] = useState<string | null>(null)
  const [metaState, setMetaState] = useState<{
    db: string
    fetchedAt: string
    payload: MetadataPayload
  } | null>(null)

  const selectedDb = searchParams.get('db')
  const selectedDbRef = useRef<string | null>(selectedDb)

  useEffect(() => {
    selectedDbRef.current = selectedDb
  }, [selectedDb])

  const setSelectedDb = useCallback(
    (name: string | null) => {
      if (name) setSearchParams({ db: name }, { replace: true })
      else setSearchParams({}, { replace: true })
    },
    [setSearchParams],
  )

  const refreshList = useCallback(async () => {
    setListLoading(true)
    try {
      const rows = await listDatabases()
      setConnections(rows)
      return rows
    } catch (e) {
      message.error(e instanceof Error ? e.message : '加载连接失败')
      return []
    } finally {
      setListLoading(false)
    }
  }, [message])

  useEffect(() => {
    let cancelled = false
    listDatabases()
      .then((r: RegisteredDatabaseListItem[]) => {
        if (!cancelled) setConnections(r)
      })
      .catch((e: unknown) => {
        if (!cancelled) message.error(e instanceof Error ? e.message : '加载连接失败')
      })
      .finally(() => {
        if (!cancelled) setListLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [message])

  useEffect(() => {
    if (!connections.length) {
      if (selectedDb) setSelectedDb(null)
      return
    }
    if (selectedDb && connections.some((c) => c.name === selectedDb)) return
    setSelectedDb(connections[0]!.name)
  }, [connections, selectedDb, setSelectedDb])

  const refreshMetadataForDb = useCallback(
    async (name: string) => {
      setRefreshingName(name)
      try {
        const res = await refreshDatabaseMetadata(name)
        message.success('元数据已更新')
        await refreshList()
        if (selectedDbRef.current === name) {
          setMetaState({
            db: name,
            fetchedAt: res.fetchedAt,
            payload: res.metadata as MetadataPayload,
          })
        }
      } catch (e) {
        message.error(e instanceof Error ? e.message : '刷新失败')
      } finally {
        setRefreshingName(null)
      }
    },
    [message, refreshList],
  )

  const removeDatabase = useCallback(
    async (name: string) => {
      try {
        await deleteDatabase(name)
        message.success('已删除连接')
        const rows = await refreshList()
        if (selectedDbRef.current === name) {
          if (rows.length > 0) setSelectedDb(rows[0]!.name)
          else setSelectedDb(null)
        }
      } catch (e) {
        message.error(e instanceof Error ? e.message : '删除失败')
      }
    },
    [message, refreshList, setSelectedDb],
  )

  const displayMeta = useMemo(() => {
    if (!selectedDb || metaState?.db !== selectedDb) return null
    return { fetchedAt: metaState.fetchedAt, payload: metaState.payload }
  }, [selectedDb, metaState])

  const metaStale = Boolean(selectedDb && metaState?.db !== selectedDb)

  useEffect(() => {
    if (!selectedDb) return
    const targetDb = selectedDb
    let cancelled = false
    getDatabaseMetadata(targetDb)
      .then((res: DatabaseMetadataResponse) => {
        if (cancelled) return
        setMetaState({
          db: targetDb,
          fetchedAt: res.fetchedAt,
          payload: res.metadata as MetadataPayload,
        })
      })
      .catch((e: unknown) => {
        if (!cancelled) {
          message.error(e instanceof Error ? e.message : '加载元数据失败')
          setMetaState({
            db: targetDb,
            fetchedAt: '',
            payload: { tables: [] },
          })
        }
      })
    return () => {
      cancelled = true
    }
  }, [selectedDb, message])

  return (
    <div className="flex h-[100dvh] flex-col overflow-hidden bg-slate-100 lg:flex-row">
      <aside className="flex w-full shrink-0 flex-col border-slate-200 bg-white lg:h-full lg:w-[10%] lg:min-w-0 lg:border-r">
        <div className="border-b border-slate-200 px-4 py-3 lg:px-2 lg:py-2">
          <div className="flex flex-wrap items-start justify-between gap-1">
            <div>
              <Text strong className="text-base lg:text-sm">
                db_query
              </Text>
              <div className="mt-0.5 text-xs text-slate-500 lg:text-[10px] lg:leading-tight">
                数据库连接
              </div>
            </div>
            <Link
              to="/settings/llm"
              className="shrink-0 text-[10px] text-blue-600 hover:underline lg:text-[9px]"
            >
              LLM 设置
            </Link>
          </div>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto p-4 lg:p-2">
          <Form
            form={form}
            layout="vertical"
            size="small"
            className="mb-4 lg:mb-2 [&_.ant-form-item]:mb-3 lg:[&_.ant-form-item]:mb-2 [&_.ant-form-item-label>label]:text-sm lg:[&_.ant-form-item-label>label]:text-[11px] lg:[&_.ant-form-item-label]:pb-0"
            onFinish={async (v: {
              logicalName: string
              url: string
              backendKind?: string
            }) => {
              setSubmitting(true)
              try {
                const url = v.url.trim()
                const inferred = inferBackendKindFromUrl(url)
                const bk = inferred ?? v.backendKind?.trim()
                await putDatabase(
                  v.logicalName.trim(),
                  url,
                  bk && bk.length > 0 ? bk : undefined,
                )
                message.success('已保存并拉取元数据')
                const rows = await refreshList()
                const name = v.logicalName.trim()
                if (rows.some((r: RegisteredDatabaseListItem) => r.name === name)) setSelectedDb(name)
              } catch (e) {
                message.error(e instanceof Error ? e.message : '保存失败')
              } finally {
                setSubmitting(false)
              }
            }}
          >
            <Form.Item label="逻辑名称" name="logicalName" rules={[{ required: true }]}>
              <Input placeholder="demo" autoComplete="off" className="lg:text-xs" />
            </Form.Item>
            <Form.Item label="连接串" name="url" rules={[{ required: true }]}>
              <Input.TextArea
                rows={3}
                placeholder="postgres://… 或 mysql://user:pass@host:3306/dbname"
                autoComplete="off"
                className="lg:text-xs"
                onChange={(e) => {
                  const inferred = inferBackendKindFromUrl(e.target.value)
                  if (inferred) form.setFieldValue('backendKind', inferred)
                }}
              />
            </Form.Item>
            <Form.Item label="数据库类型（可选）" name="backendKind">
              <Select
                allowClear
                placeholder="自动识别（按 URL 协议）"
                className="lg:text-xs"
                options={[
                  { value: 'postgres', label: 'PostgreSQL' },
                  { value: 'mysql', label: 'MySQL / MariaDB' },
                ]}
              />
            </Form.Item>
            <Form.Item className="!mb-2">
              <Space wrap>
                <Button type="primary" htmlType="submit" loading={submitting} size="small">
                  保存
                </Button>
                <Button size="small" onClick={() => void refreshList()} loading={listLoading}>
                  刷新列表
                </Button>
              </Space>
            </Form.Item>
          </Form>

          <div className="mb-2 text-xs font-medium text-slate-600 lg:mb-1 lg:text-[10px]">
            已保存的连接
          </div>
          <Spin spinning={listLoading}>
            {connections.length === 0 ? (
              !listLoading ? (
                <Text type="secondary" className="text-sm">
                  暂无连接
                </Text>
              ) : null
            ) : (
              <div className="flex flex-col gap-1">
                {connections.map((item) => (
                  <div
                    key={item.name}
                    className={`flex items-stretch gap-1 rounded transition-colors ${
                      selectedDb === item.name ? 'bg-blue-50 ring-1 ring-blue-200' : 'hover:bg-slate-50'
                    }`}
                  >
                    <div
                      className="min-w-0 flex-1 cursor-pointer px-2 py-2 lg:px-1 lg:py-1"
                      onClick={() => setSelectedDb(item.name)}
                    >
                      <div className="truncate font-medium text-slate-900 lg:text-xs" title={item.name}>
                        {item.name}
                      </div>
                      <div
                        className="truncate text-xs text-slate-400 lg:text-[10px] lg:leading-tight"
                        title={item.updatedAt ?? item.createdAt ?? ''}
                      >
                        {item.backendKind ? `${item.backendKind} · ` : ''}
                        {item.updatedAt ?? item.createdAt}
                      </div>
                    </div>
                    <div className="flex shrink-0 flex-col justify-center gap-0.5 pr-1 lg:pr-0">
                      <Tooltip title="刷新该库的表与视图">
                        <Button
                          type="text"
                          size="small"
                          className="!text-slate-600"
                          icon={<ReloadOutlined />}
                          loading={refreshingName === item.name}
                          onClick={(e) => {
                            e.stopPropagation()
                            void refreshMetadataForDb(item.name)
                          }}
                        />
                      </Tooltip>
                      <Popconfirm
                        title="删除连接"
                        description={`确定删除「${item.name}」？本地缓存的元数据将一并删除。`}
                        okText="删除"
                        cancelText="取消"
                        okButtonProps={{ danger: true }}
                        onConfirm={() => void removeDatabase(item.name)}
                      >
                        <Button
                          type="text"
                          size="small"
                          danger
                          icon={<DeleteOutlined />}
                          onClick={(e) => e.stopPropagation()}
                          aria-label={`删除连接 ${item.name}`}
                        />
                      </Popconfirm>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Spin>
        </div>
      </aside>

      <section className="flex min-h-[36vh] flex-col border-slate-200 bg-white lg:h-full lg:min-h-0 lg:w-[15%] lg:shrink-0 lg:border-r">
        <div className="flex shrink-0 flex-col gap-2 border-b border-slate-100 px-4 py-2 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between lg:gap-1 lg:px-2 lg:py-1.5">
          <div className="min-w-0">
            <span className="text-sm font-medium text-slate-800 lg:text-[11px] lg:leading-tight">
              <span className="lg:hidden">Schema / 表与视图</span>
              <span className="hidden lg:inline" title="Schema / 表与视图">
                Schema
              </span>
            </span>
            {selectedDb ? (
              <Text
                type="secondary"
                className="mt-0.5 block truncate text-xs lg:text-[10px] lg:leading-tight"
                title={selectedDb}
              >
                {selectedDb}
              </Text>
            ) : (
              <Text type="secondary" className="mt-0.5 block text-xs lg:text-[10px] lg:leading-tight">
                <span className="lg:hidden">请选择左侧连接</span>
                <span className="hidden lg:inline">选左侧连接</span>
              </Text>
            )}
          </div>
          <div className="flex shrink-0 justify-end">
            {selectedDb ? (
              <Tooltip title="重新拉取该库的完整结构">
                <Button
                  type="default"
                  size="small"
                  icon={<ReloadOutlined />}
                  loading={refreshingName === selectedDb}
                  onClick={() => void refreshMetadataForDb(selectedDb)}
                  aria-label="刷新结构"
                >
                  <span className="lg:hidden">刷新结构</span>
                </Button>
              </Tooltip>
            ) : null}
          </div>
        </div>
        <div className="min-h-0 flex-1 overflow-auto p-3 lg:p-2">
          {!selectedDb ? (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="选择数据库后显示完整 schema" />
          ) : (
            <SchemaCatalog
              loading={metaStale}
              schemas={displayMeta?.payload.schemas ?? []}
              tables={displayMeta?.payload.tables ?? []}
              fetchedAt={displayMeta?.fetchedAt}
            />
          )}
        </div>
        </section>

        <main className="flex min-h-0 min-w-0 flex-col border-slate-200 bg-white lg:h-full lg:w-[75%] lg:min-w-0 lg:border-l lg:border-slate-200">
          <SqlQueryPage selectedDb={selectedDb} />
        </main>
    </div>
  )
}
