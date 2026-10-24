export const isUnauthorized = (error) => {
  return error?.response?.status === 401 || error?.response?.data?.code === '4001'
}

export const clearStoredAuth = (storage = globalThis.localStorage) => {
  storage.removeItem('token')
  storage.removeItem('info')
}
