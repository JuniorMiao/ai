import { expect, test } from '@playwright/test'

test.describe('db_query workspace', () => {
  test('shows sidebar and three-panel layout', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText('数据库连接', { exact: true })).toBeVisible()
    await expect(page.getByTitle('Schema / 表与视图')).toBeVisible()
    await expect(page.getByText('SQL 查询')).toBeVisible()
    await expect(page.getByRole('button', { name: '执行查询' })).toBeVisible()
    await expect(page.getByText('查询结果')).toBeVisible()
  })
})
