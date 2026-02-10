import { create } from 'zustand'

export interface Store {
  id: string
  name: string
  engine: 'woocommerce' | 'medusa'
  status: 'PROVISIONING' | 'READY' | 'FAILED'
  url?: string
  created_at: string
  error?: string
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

const API_BASE = '/api/stores'

export const useStore = create<StoreState>((set) => ({
  stores: [],
  loading: false,
  fetchStores: async () => {
    set({ loading: true })
    try {
      const response = await fetch(API_BASE)
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
    const response = await fetch(API_BASE, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!response.ok) {
      throw new Error('Failed to create store')
    }
  },
  deleteStore: async (id) => {
    const response = await fetch(`${API_BASE}/${id}`, { method: 'DELETE' })
    if (!response.ok) {
      throw new Error('Failed to delete store')
    }
  },
}))
