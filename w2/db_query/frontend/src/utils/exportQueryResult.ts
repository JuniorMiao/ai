/** Export tabular query results to CSV or Excel in the browser. */

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.rel = 'noopener'
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

function escapeCsvCell(value: unknown): string {
  if (value === null || value === undefined) return ''
  const s = String(value)
  if (/[",\r\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`
  return s
}

export function buildExportBasename(dbName: string): string {
  const safe = dbName.replace(/[^\w\u4e00-\u9fff-]+/g, '_').replace(/^_|_$/g, '') || 'query'
  const stamp = new Date().toISOString().slice(0, 19).replace(/[-:T]/g, '')
  return `query_${safe}_${stamp}`
}

export function exportQueryResultToCsv(
  columns: string[],
  rows: unknown[][],
  filenameBase: string,
): void {
  const header = columns.map(escapeCsvCell).join(',')
  const body = rows.map((row) =>
    columns.map((_, i) => escapeCsvCell(row[i])).join(','),
  )
  const csv = `\uFEFF${[header, ...body].join('\r\n')}`
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  downloadBlob(blob, `${filenameBase}.csv`)
}

export async function exportQueryResultToExcel(
  columns: string[],
  rows: unknown[][],
  filenameBase: string,
): Promise<void> {
  const XLSX = await import('xlsx')
  const records = rows.map((row) => {
    const rec: Record<string, unknown> = {}
    columns.forEach((col, i) => {
      rec[col] = row[i] ?? null
    })
    return rec
  })
  const sheet = XLSX.utils.json_to_sheet(records, { header: columns })
  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, sheet, 'Result')
  XLSX.writeFile(workbook, `${filenameBase}.xlsx`)
}
