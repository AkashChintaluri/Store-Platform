import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { API_BASE } from '../config'

export interface User {
  id: string
  email: string
  name: string
  created_at: string
}

interface AuthState {
  user: User | null
  token: string | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (email: string, password: string, name: string) => Promise<void>
  logout: () => void
  checkAuth: () => Promise<void>
}

const AUTH_BASE = `${API_BASE}/auth`

export const useAuth = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      loading: false,

      login: async (email: string, password: string) => {
        set({ loading: true })
        try {
          const response = await fetch(`${AUTH_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
          })

          if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Login failed')
          }

          const data = await response.json()
          set({ user: data.user, token: data.access_token })
        } finally {
          set({ loading: false })
        }
      },

      signup: async (email: string, password: string, name: string) => {
        set({ loading: true })
        try {
          const response = await fetch(`${AUTH_BASE}/signup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password, name }),
          })

          if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Signup failed')
          }

          const data = await response.json()
          set({ user: data.user, token: data.access_token })
        } finally {
          set({ loading: false })
        }
      },

      logout: () => {
        set({ user: null, token: null })
      },

      checkAuth: async () => {
        const token = get().token
        if (!token) {
          set({ user: null })
          return
        }

        try {
          const response = await fetch(`${AUTH_BASE}/me`, {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          })

          if (!response.ok) {
            throw new Error('Auth check failed')
          }

          const user = await response.json()
          set({ user })
        } catch (error) {
          // Token invalid, clear auth
          set({ user: null, token: null })
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
      }),
    }
  )
)
