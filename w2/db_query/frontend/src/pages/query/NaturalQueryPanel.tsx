import { Alert, App as AntApp, Button, Input, Select, Typography } from 'antd'
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { naturalQuery, type LlmSettings } from '../../api/natural'

const { Text } = Typography

const LS_KEY = 'db_query_nl_llm_choice'

function llmShortLabel(provider: string): string {
  return provider === 'qwen' ? '通义千问' : 'OpenAI'
}

type Props = {
  dbName: string | null
  nlReady: boolean
  llmItems: LlmSettings[]
  /** undefined = use server default profile; number = force that profile id */
  explicitLlmId: number | undefined
  onExplicitLlmIdChange: (id: number | undefined) => void
  onApplySql: (sql: string) => void
}

export default function NaturalQueryPanel({
  dbName,
  nlReady,
  llmItems,
  explicitLlmId,
  onExplicitLlmIdChange,
  onApplySql,
}: Props) {
  const { message } = AntApp.useApp()
  const [prompt, setPrompt] = useState('')
  const [loading, setLoading] = useState(false)

  const selectValue = useMemo(() => {
    if (explicitLlmId === undefined) return 'default'
    return String(explicitLlmId)
  }, [explicitLlmId])

  const run = async () => {
    if (!dbName) return
    const p = prompt.trim()
    if (!p) return
    setLoading(true)
    try {
      const res = await naturalQuery(dbName, p, explicitLlmId)
      onApplySql(res.sql)
      message.success('已写入编辑器，可修改后执行查询')
    } catch (e) {
      message.error(e instanceof Error ? e.message : '生成失败')
    } finally {
      setLoading(false)
    }
  }

  if (!nlReady) {
    return (
      <Alert
        type="warning"
        showIcon
        className="mb-3"
        title="未检测到可用的 LLM 配置"
        description={
          <span>
            请在{' '}
            <Link to="/settings/llm" className="font-medium text-blue-600">
              LLM 设置
            </Link>{' '}
            中添加至少一个模型配置，或配置环境变量 OPENAI_API_KEY / DASHSCOPE_API_KEY（通义千问）。
          </span>
        }
      />
    )
  }

  return (
    <div className="mb-3 rounded border border-dashed border-slate-200 bg-slate-50/80 px-3 py-2">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <Text className="text-sm font-medium text-slate-800">自然语言生成 SQL</Text>
        <Link to="/settings/llm" className="text-xs text-blue-600 hover:underline">
          管理 LLM
        </Link>
      </div>
      {llmItems.length > 0 ? (
        <div className="mb-2">
          <Text type="secondary" className="mb-1 block text-xs">
            使用模型
          </Text>
          <Select
            className="w-full min-w-0"
            size="small"
            value={selectValue}
            onChange={(v) => {
              const next = v === 'default' ? undefined : Number(v)
              onExplicitLlmIdChange(next)
              try {
                if (next === undefined) localStorage.setItem(LS_KEY, 'default')
                else localStorage.setItem(LS_KEY, String(next))
              } catch {
                /* ignore */
              }
            }}
            options={[
              { value: 'default', label: '默认（服务端标记为默认的配置）' },
              ...llmItems.map((it) => ({
                value: String(it.id),
                label: `${llmShortLabel(it.provider)} · ${it.model}${it.isDefault ? ' ★' : ''} (#${it.id})`,
              })),
            ]}
          />
        </div>
      ) : null}
      {!dbName ? (
        <Text type="secondary" className="text-xs">
          请先选择左侧数据库连接
        </Text>
      ) : (
        <>
          <Input.TextArea
            autoSize={{ minRows: 2, maxRows: 4 }}
            placeholder="例如：列出用户表中最近注册的 10 条邮箱"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={loading}
            className="mb-2"
          />
          <Button type="primary" loading={loading} disabled={!prompt.trim()} onClick={() => void run()}>
            生成并填入编辑器
          </Button>
        </>
      )}
    </div>
  )
}

export { LS_KEY as NL_LLM_CHOICE_KEY }
