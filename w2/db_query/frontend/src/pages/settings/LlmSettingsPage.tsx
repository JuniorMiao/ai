import { DeleteOutlined, PlusOutlined, StarOutlined } from '@ant-design/icons'
import {
  App as AntApp,
  Button,
  Card,
  Form,
  Input,
  Modal,
  Popconfirm,
  Select,
  Space,
  Switch,
  Table,
  Typography,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  createLlmSettings,
  deleteLlmSettings,
  listLlmProviders,
  listLlmSettings,
  setDefaultLlmProfile,
  updateLlmSettings,
  type LlmProviderCatalogItem,
  type LlmSettings,
} from '../../api/natural'

const { Text } = Typography

type FormValues = {
  provider: string
  baseUrl: string
  model: string
  apiKeyRef: string
  apiKey?: string
  setAsDefault: boolean
}

function providerColumnLabel(p: string, catalog: LlmProviderCatalogItem[]): string {
  return catalog.find((c) => c.id === p)?.shortName ?? p
}

function metaFor(catalog: LlmProviderCatalogItem[], provider: string) {
  return catalog.find((c) => c.id === provider)
}

export default function LlmSettingsPage() {
  const { message } = AntApp.useApp()
  const [rows, setRows] = useState<LlmSettings[]>([])
  const [providerCatalog, setProviderCatalog] = useState<LlmProviderCatalogItem[]>([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<LlmSettings | null>(null)
  const [saving, setSaving] = useState(false)
  const [form] = Form.useForm<FormValues>()
  const [passwordTouched, setPasswordTouched] = useState(false)

  const reload = useCallback(async () => {
    setLoading(true)
    try {
      const [r, provs] = await Promise.all([listLlmSettings(), listLlmProviders()])
      setRows(r.items)
      setProviderCatalog(provs.items)
    } catch (e) {
      message.error(e instanceof Error ? e.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }, [message])

  useEffect(() => {
    queueMicrotask(() => void reload())
  }, [reload])

  const applyProviderDefaults = (provider: string) => {
    const m = metaFor(providerCatalog, provider)
    if (m) {
      form.setFieldsValue({ baseUrl: m.defaultBaseUrl, model: m.defaultModel })
    }
  }

  const openCreate = () => {
    setEditing(null)
    setPasswordTouched(false)
    const first = providerCatalog[0]?.id ?? 'openai'
    const m = metaFor(providerCatalog, first)
    form.setFieldsValue({
      provider: first,
      baseUrl: m?.defaultBaseUrl ?? '',
      model: m?.defaultModel ?? '',
      apiKeyRef: '',
      setAsDefault: rows.length === 0,
    })
    setModalOpen(true)
  }

  const openEdit = (r: LlmSettings) => {
    setEditing(r)
    setPasswordTouched(false)
    const pv = providerCatalog.some((c) => c.id === r.provider)
      ? r.provider
      : (providerCatalog[0]?.id ?? 'openai')
    form.setFieldsValue({
      provider: pv,
      baseUrl: r.baseUrl,
      model: r.model,
      apiKeyRef: r.apiKeyRef ?? '',
    })
    form.setFieldValue('apiKey', undefined)
    setModalOpen(true)
  }

  const submitModal = async () => {
    const v = await form.validateFields()
    setSaving(true)
    try {
      if (editing) {
        const body: Parameters<typeof updateLlmSettings>[1] = {
          provider: v.provider.trim(),
          baseUrl: v.baseUrl.trim(),
          model: v.model.trim(),
          apiKeyRef: v.apiKeyRef.trim() || null,
        }
        if (passwordTouched) {
          body.apiKey = v.apiKey?.trim() ?? ''
        }
        await updateLlmSettings(editing.id, body)
        message.success('已保存')
      } else {
        await createLlmSettings({
          provider: v.provider.trim(),
          baseUrl: v.baseUrl.trim(),
          model: v.model.trim(),
          apiKeyRef: v.apiKeyRef.trim() || null,
          apiKey: v.apiKey?.trim() || null,
          setAsDefault: v.setAsDefault,
        })
        message.success('已添加')
      }
      setModalOpen(false)
      await reload()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '保存失败')
    } finally {
      setSaving(false)
    }
  }

  const columns: ColumnsType<LlmSettings> = [
    { title: 'ID', dataIndex: 'id', width: 56 },
    {
      title: '服务商',
      dataIndex: 'provider',
      width: 120,
      render: (_: unknown, r: LlmSettings) => providerColumnLabel(r.provider, providerCatalog),
    },
    { title: 'Model', dataIndex: 'model', ellipsis: true },
    {
      title: 'Base URL',
      dataIndex: 'baseUrl',
      ellipsis: true,
      responsive: ['md'],
    },
    {
      title: '密钥',
      key: 'key',
      width: 88,
      render: (_, r) => (r.hasApiKey || r.apiKeyRef ? '已配置' : '—'),
    },
    {
      title: '默认',
      key: 'def',
      width: 72,
      render: (_, r) => (r.isDefault ? '★' : ''),
    },
    {
      title: '操作',
      key: 'actions',
      width: 220,
      render: (_, r) => (
        <Space size="small" wrap>
          {!r.isDefault ? (
            <Button
              type="link"
              size="small"
              icon={<StarOutlined />}
              onClick={() => void handleSetDefault(r.id)}
            >
              设默认
            </Button>
          ) : null}
          <Button type="link" size="small" onClick={() => openEdit(r)}>
            编辑
          </Button>
          <Popconfirm title="删除此配置？" onConfirm={() => void handleDelete(r.id)}>
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const handleSetDefault = async (id: number) => {
    try {
      await setDefaultLlmProfile(id)
      message.success('已设为默认')
      await reload()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '操作失败')
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await deleteLlmSettings(id)
      message.success('已删除')
      await reload()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '删除失败')
    }
  }

  return (
    <div className="min-h-[100dvh] bg-slate-100 p-6">
      <div className="mx-auto max-w-5xl">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <Link to="/" className="text-sm text-blue-600 hover:underline">
            ← 返回工作区
          </Link>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={openCreate}
            disabled={providerCatalog.length === 0}
          >
            添加 LLM
          </Button>
        </div>
        <Card title="LLM 配置（可多套切换）">
          <Text type="secondary" className="mb-4 block text-sm">
            支持 OpenAI 与阿里云通义千问（DashScope OpenAI 兼容接口）。API Key 仅存本地 SQLite；也可用环境变量
            OPENAI_API_KEY / DASHSCOPE_API_KEY。工作区下拉里可选具体一套，未指定时使用「默认」。
          </Text>
          <Table<LlmSettings>
            rowKey="id"
            size="small"
            loading={loading}
            columns={columns}
            dataSource={rows}
            pagination={false}
            scroll={{ x: 720 }}
          />
        </Card>
      </div>

      <Modal
        title={editing ? `编辑 LLM #${editing.id}` : '添加 LLM'}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={() => void submitModal()}
        confirmLoading={saving}
        destroyOnClose
        width={520}
      >
        <Form form={form} layout="vertical" className="mt-2">
          {editing ? null : (
            <Form.Item label="保存后设为默认" name="setAsDefault" valuePropName="checked">
              <Switch />
            </Form.Item>
          )}
          <Form.Item label="服务商" name="provider" rules={[{ required: true }]}>
            <Select
              options={providerCatalog.map((c) => ({
                value: c.id,
                label: c.displayName,
              }))}
              onChange={(v: string) => applyProviderDefaults(v)}
              disabled={providerCatalog.length === 0}
            />
          </Form.Item>
          <Form.Item label="Base URL" name="baseUrl" rules={[{ required: true }]}>
            <Input autoComplete="off" />
          </Form.Item>
          <Form.Item label="Model" name="model" rules={[{ required: true }]}>
            <Input autoComplete="off" />
          </Form.Item>
          <Form.Item noStyle shouldUpdate={(prev, cur) => prev.provider !== cur.provider}>
            {() => {
              const p = form.getFieldValue('provider') as string
              const meta = metaFor(providerCatalog, p)
              const ph = meta?.primaryApiKeyEnv ?? 'OPENAI_API_KEY'
              return (
                <Form.Item label="API Key 环境变量名（可选）" name="apiKeyRef">
                  <Input autoComplete="off" placeholder={ph} />
                </Form.Item>
              )
            }}
          </Form.Item>
          <Form.Item noStyle shouldUpdate={(prev, cur) => prev.provider !== cur.provider}>
            {() => {
              const p = form.getFieldValue('provider') as string
              const meta = metaFor(providerCatalog, p)
              const hint = meta?.apiKeyInlineHint ?? ''
              return (
                <Form.Item
                  label="API Key（可选）"
                  name="apiKey"
                  extra={
                    editing?.hasApiKey ? (
                      <span>已存密钥；修改请填写；留空则沿用原密钥</span>
                    ) : (
                      <span>{hint}</span>
                    )
                  }
                >
                  <Input.Password
                    autoComplete="new-password"
                    placeholder={meta?.passwordPlaceholder ?? 'sk-...'}
                    onChange={() => setPasswordTouched(true)}
                  />
                </Form.Item>
              )
            }}
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
