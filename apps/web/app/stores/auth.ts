import { defineStore } from 'pinia'
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  updateProfile,
  signOut,
  onAuthStateChanged,
  type Auth
} from 'firebase/auth'

export type UserRole = 'teacher' | 'student' | 'admin'

export interface UserProfile {
  uid: string
  email: string
  display_name?: string
  role: UserRole
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: (typeof window !== 'undefined' ? localStorage.getItem('am_token') : null) as string | null,
    user: null as UserProfile | null,
    loading: false,
    initialized: false
  }),

  getters: {
    isAuthenticated: (state) => Boolean(state.token && state.user),
    isTeacher: (state) => state.user?.role === 'teacher' || state.user?.role === 'admin',
    isStudent: (state) => state.user?.role === 'student'
  },

  actions: {
    setToken(newToken: string | null) {
      this.token = newToken
      if (typeof window !== 'undefined') {
        if (newToken) localStorage.setItem('am_token', newToken)
        else localStorage.removeItem('am_token')
      }
    },

    async initAuth() {
      if (this.initialized) return
      const { $auth } = useNuxtApp()
      const auth = $auth as Auth | null

      if (this.token?.startsWith('mock-')) {
        try {
          await this.fetchMe()
        } catch (error) {
          if (extractApiError(error).status !== 401) throw error
        }
        this.initialized = true
        return
      }

      if (!auth) {
        this.initialized = true
        return
      }

      try {
        await new Promise<void>((resolve, reject) => {
          let unsubscribe = () => {}
          unsubscribe = onAuthStateChanged(auth, (fbUser) => {
            unsubscribe()
            void (async () => {
              if (fbUser) {
                const idToken = await fbUser.getIdToken()
                this.setToken(idToken)
                await this.fetchMe()
              } else {
                this.setToken(null)
                this.user = null
              }
              this.initialized = true
            })().then(resolve, reject)
          }, reject)
        })
      } catch (error) {
        if (extractApiError(error).status !== 401) throw error
        this.setToken(null)
        this.user = null
        this.initialized = true
      }
    },

    async fetchMe() {
      if (!this.token) return null
      const { request } = useApi()
      try {
        const user = await request<UserProfile>('/api/v1/auth/me')
        this.user = user
        this.initialized = true
        return user
      } catch (error) {
        if (extractApiError(error).status === 401) {
          this.setToken(null)
          this.user = null
          this.initialized = true
        }
        throw error
      }
    },

    async loginWithEmail(email: string, password: string) {
      this.loading = true
      try {
        const { $auth } = useNuxtApp()
        const auth = $auth as Auth | null
        if (!auth) throw new Error('Firebase Auth no está configurado en .env (usa los botones Demo)')

        const cred = await signInWithEmailAndPassword(auth, email, password)
        const idToken = await cred.user.getIdToken()
        this.setToken(idToken)
        await this.fetchMe()
      } finally {
        this.loading = false
      }
    },

    async registerWithEmail(email: string, password: string, displayName: string, role: 'teacher' | 'student') {
      this.loading = true
      try {
        const { $auth } = useNuxtApp()
        const auth = $auth as Auth | null
        if (!auth) throw new Error('Firebase Auth no está configurado en .env (usa los botones Demo)')

        const cred = await createUserWithEmailAndPassword(auth, email, password)
        if (displayName) await updateProfile(cred.user, { displayName })
        const idToken = await cred.user.getIdToken(true)
        this.setToken(idToken)
        await this.updateRole(role)
      } finally {
        this.loading = false
      }
    },

    async loginMock(role: 'teacher' | 'student') {
      this.loading = true
      try {
        this.setToken(role === 'teacher' ? 'mock-teacher' : 'mock-student')
        await this.fetchMe()
        this.initialized = true
      } finally {
        this.loading = false
      }
    },

    async updateRole(role: 'teacher' | 'student') {
      if (!this.token) return
      const { request } = useApi()
      await request<UserProfile>('/api/v1/auth/role', {
        method: 'PUT',
        body: { role }
      })
      return await this.fetchMe()
    },

    async logout() {
      const { $auth } = useNuxtApp()
      const auth = $auth as Auth | null
      try {
        if (auth) await signOut(auth)
      } finally {
        this.setToken(null)
        this.user = null
        this.initialized = true
      }
    }
  }
})