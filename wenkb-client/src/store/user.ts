import { defineStore } from 'pinia'
import { localRead, localSave } from '@/libs/tools'
import { clearStoredAuth } from '@/libs/auth-session.js'
const useUserStore = defineStore('user', {
  state: () => ({
    token: localRead('token') || '', // token
    info: localRead('info') || {} // { id, name }
  }),
  getters: {
    getToken (state:any) {
      return state.token
    },
    getInfo (state:any) {
      return state.info
    }
  },
  actions: {
    setToken (token:string) {
      this.token = token
      localSave('token', token)
    },
    setInfo (info:Object) {
      this.info = info
      localSave('info', info)
    },
    clearAuth () {
      this.token = ''
      this.info = {}
      clearStoredAuth()
    }
  }
})
export default useUserStore
