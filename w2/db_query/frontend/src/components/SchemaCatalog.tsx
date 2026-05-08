import { Empty, Spin, Tag, Tree, Typography } from 'antd'
import type { DataNode } from 'antd/es/tree'
import { useMemo } from 'react'

const { Text } = Typography

export type TableMeta = {
  schema: string
  name: string
  type: string
  columns: { name: string; dataType: string; nullable: boolean; comment?: string }[]
}

type Props = {
  loading: boolean
  schemas: string[]
  tables: TableMeta[]
  fetchedAt?: string
}

export default function SchemaCatalog({ loading, schemas, tables, fetchedAt }: Props) {
  const grouped = useMemo(() => {
    const order =
      schemas.length > 0 ? [...schemas].sort() : [...new Set(tables.map((t) => t.schema))].sort()
    const map = new Map<string, TableMeta[]>()
    for (const s of order) map.set(s, [])
    for (const t of tables) {
      const arr = map.get(t.schema) ?? []
      arr.push(t)
      map.set(t.schema, arr)
    }
    return { order, map }
  }, [schemas, tables])

  const treeData: DataNode[] = useMemo(() => {
    return grouped.order.map((schemaName) => {
      const tbls = grouped.map.get(schemaName) ?? []
      return {
        key: `schema:${schemaName}`,
        title: (
          <span className="font-medium text-slate-800 lg:text-[11px] lg:leading-tight">
            {schemaName}
            <Text type="secondary" className="ml-1 align-middle text-[11px] lg:text-[10px]">
              ({tbls.length})
            </Text>
          </span>
        ),
        children: tbls.map((tbl) => ({
          key: `table:${schemaName}:${tbl.name}`,
          title: (
            <span className="inline-flex max-w-full flex-col gap-0.5">
              <span className="flex min-w-0 items-center gap-1">
                <span className="truncate font-mono text-xs text-slate-900 lg:text-[11px]" title={tbl.name}>
                  {tbl.name}
                </span>
                <Tag
                  color={tbl.type === 'VIEW' ? 'blue' : 'green'}
                  className="m-0 shrink-0 px-1 py-0 text-[10px] leading-tight lg:text-[9px]"
                >
                  {tbl.type === 'VIEW' ? '视图' : tbl.type === 'BASE TABLE' ? '表' : tbl.type}
                </Tag>
              </span>
            </span>
          ),
          children: tbl.columns.map((col) => ({
            key: `col:${schemaName}:${tbl.name}:${col.name}`,
            isLeaf: true,
            title: (
              <span className="inline-flex max-w-full flex-col gap-0.5 text-[11px] leading-snug lg:text-[10px]">
                <span className="min-w-0 break-all">
                  <code className="text-slate-900">{col.name}</code>
                  <span className="ml-1 text-slate-600">{col.dataType}</span>
                  <Tag color={col.nullable ? 'gold' : 'default'} className="ml-1 px-1 py-0 text-[10px] lg:text-[9px]">
                    {col.nullable ? 'NULL' : 'NOT NULL'}
                  </Tag>
                </span>
                {col.comment ? (
                  <Text type="secondary" className="block truncate text-[10px] lg:text-[9px]" title={col.comment}>
                    {col.comment}
                  </Text>
                ) : null}
              </span>
            ),
          })),
        })),
      }
    })
  }, [grouped])

  if (!tables.length && !loading) {
    return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无表或视图" />
  }

  return (
    <Spin spinning={loading}>
        <div className="space-y-2 lg:space-y-1">
          {fetchedAt ? (
            <Text type="secondary" className="block text-[11px] leading-tight lg:text-[10px]">
              同步：{fetchedAt}
            </Text>
          ) : null}
          <Text type="secondary" className="block text-[11px] leading-tight lg:hidden">
            Schema → 表/视图 → 字段（含类型、可空、注释）
          </Text>
          <Text type="secondary" className="hidden text-[10px] leading-tight lg:block">
            库 → 表/视图 → 字段
          </Text>
          <Tree
            showLine
            blockNode
            defaultExpandAll
            className="schema-tree bg-transparent text-[12px] lg:text-[11px] [&_.ant-tree-indent-unit]:w-3 lg:[&_.ant-tree-indent-unit]:w-2 [&_.ant-tree-switcher]:leading-6 lg:[&_.ant-tree-switcher]:leading-5"
          treeData={treeData}
        />
      </div>
    </Spin>
  )
}
