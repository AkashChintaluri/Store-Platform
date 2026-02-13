import { create } from 'zustand'
import { useAuth } from './useAuth'
import { API_BASE } from '../config'

export interface Store {
  id: string
  name: string
  engine: 'woocommerce' | 'medusa'
  status: 'PROVISIONING' | 'READY' | 'FAILED'
  url?: string
  password?: string
  created_at: string
  error?: string
  creator_id?: string
  creator_name?: string
}

type CreateStorePayload = {
  name: string
  engine: Store['engine']
}

type StoreState = {
  stores: Store[]
  loading: boolean
  fetchStores: () => Promise<void>
  createStore: (payload: CreateStorePayload) => Promise<void>
  deleteStore: (id: string) => Promise<void>
}

const STORES_BASE = `${API_BASE}/stores`

const getAuthHeaders = () => {
  const token = useAuth.getState().token
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
}

export const useStore = create<StoreState>((set) => ({
  stores: [],
  loading: false,
  fetchStores: async () => {
    set({ loading: true })
    try {
      const response = await fetch(STORES_BASE, {
        headers: getAuthHeaders(),
      })
      if (!response.ok) {
        throw new Error('Failed to fetch stores')
      }
      const data = (await response.json()) as Store[]
      set({ stores: data })
    } finally {
      set({ loading: false })
    }
  },
  createStore: async (payload) => {
    const response = await fetch(STORES_BASE, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    })
    if (!response.ok) {
      const errorBody = (await response.json().catch(() => null)) as
        | { detail?: string }
        | null
      throw new Error(errorBody?.detail ?? 'Failed to create store')
    }
    const data = (await response.json()) as Store
    set((state) => ({ stores: [data, ...state.stores] }))
  },
  deleteStore: async (id) => {
    const response = await fetch(`${STORES_BASE}/${id}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    })
    if (!response.ok) {
      throw new Error('Failed to delete store')
    }
    set((state) => ({ stores: state.stores.filter((store) => store.id !== id) }))
  },
}))
