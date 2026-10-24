import { test } from 'node:test'
import assert from 'node:assert/strict'
import { clearStoredAuth, isUnauthorized } from '../src/libs/auth-session.js'

test('识别 HTTP 401 和后端无效凭证业务码', () => {
  assert.equal(isUnauthorized({ response: { status: 401, data: {} } }), true)
  assert.equal(isUnauthorized({ response: { status: 400, data: { code: '4001' } } }), true)
  assert.equal(isUnauthorized({ response: { status: 403, data: {} } }), false)
  assert.equal(isUnauthorized({ message: 'network error' }), false)
})

test('清除失效登录凭证及用户信息，不影响其他本地设置', () => {
  const values = new Map([
    ['token', 'expired-token'],
    ['info', '{"id":"user-a"}'],
    ['theme', 'dark']
  ])
  const storage = { removeItem: key => values.delete(key) }

  clearStoredAuth(storage)

  assert.equal(values.has('token'), false)
  assert.equal(values.has('info'), false)
  assert.equal(values.get('theme'), 'dark')
})
