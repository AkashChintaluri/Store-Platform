import { useState } from 'react'
import { useStore } from '../state/useStore'
import { useAuth } from '../state/useAuth'

// Define the Store type locally to avoid import issues
type Store = {
  id: string
  name: string
  engine: 'woocommerce' | 'medusa'
  status: 'PROVISIONING' | 'READY' | 'FAILED'
  url?: string
  created_at: string
  error?: string
  namespace?: string
  password?: string
  creator_id?: string
  creator_name?: string
}

const formatDate = (value: string) => {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return date.toLocaleString()
}

const statusLabel: Record<Store['status'], string> = {
  PROVISIONING: 'Provisioning',
  READY: 'Ready',
  FAILED: 'Failed',
}

type FilterOption = 'me' | 'all'

export default function StoreTable() {
  const stores = useStore((state) => state.stores)
  const loading = useStore((state) => state.loading)
  const deleteStore = useStore((state) => state.deleteStore)
  const { user } = useAuth()
  const [expandedStore, setExpandedStore] = useState<string | null>(null)
  const [filter, setFilter] = useState<FilterOption>('me')

  const toggleExpand = (storeId: string) => {
    setExpandedStore(expandedStore === storeId ? null : storeId)
  }

  const getAdminUrl = (store: Store) => {
    if (!store.url) return null
    const baseUrl = store.url.replace('/shop/', '')
    return `${baseUrl}/wp-admin`
  }

  const onDelete = async (store: Store) => {
    const confirmed = window.confirm(
      `Delete store "${store.name}"? This cannot be undone.`,
    )
    if (!confirmed) {
      return
    }
    try {
      await deleteStore(store.id)
    } catch (err) {
      // Keep UI minimal; polling will refresh status
    }
  }

  // Filter stores based on selected filter
  const filteredStores = stores.filter((store) => {
    if (filter === 'me') {
      return store.creator_id === user?.id
    }
    // 'all' shows all stores (currently backend only returns user's stores)
    return true
  })

  return (
    <div className="table-card">
      <div className="table-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <h3>Stores</h3>
          <span style={{ fontSize: '14px', color: '#999' }}>
            ({filteredStores.length} {filter === 'me' ? 'your stores' : 'total'})
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '14px', color: '#666' }}>Filter:</span>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => setFilter('me')}
              style={{
                padding: '6px 12px',
                fontSize: '14px',
                backgroundColor: filter === 'me' ? '#007bff' : '#f0f0f0',
                color: filter === 'me' ? 'white' : '#333',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                transition: 'all 0.2s',
              }}
            >
              Created by Me
            </button>
            <button
              onClick={() => setFilter('all')}
              style={{
                padding: '6px 12px',
                fontSize: '14px',
                backgroundColor: filter === 'all' ? '#007bff' : '#f0f0f0',
                color: filter === 'all' ? 'white' : '#333',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                transition: 'all 0.2s',
              }}
            >
              All Stores
            </button>
          </div>
          {loading ? <span className="muted">Refreshing…</span> : null}
        </div>
      </div>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Engine</th>
              <th>Status</th>
              <th>Creator</th>
              <th>URL</th>
              <th>Created At</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredStores.length === 0 ? (
              <tr>
                <td colSpan={7} className="empty">
                  {filter === 'me' ? 'You have not created any stores yet.' : 'No stores found.'}
                </td>
              </tr>
            ) : (
              filteredStores.map((store) => (
                <>
                  <tr key={store.id}>
                    <td>
                      {store.creator_id === user?.id && store.status === 'READY' ? (
                        <button
                          type="button"
                          onClick={() => toggleExpand(store.id)}
                          style={{
                            background: 'none',
                            border: 'none',
                            color: '#007bff',
                            cursor: 'pointer',
                            padding: 0,
                            textDecoration: 'underline',
                          }}
                          title="Click to view admin credentials"
                        >
                          {store.name}
                        </button>
                      ) : (
                        <span>{store.name}</span>
                      )}
                    </td>
                    <td className="mono">{store.engine}</td>
                    <td>
                      <span className={`badge status-${store.status.toLowerCase()}`}>
                        {statusLabel[store.status]}
                      </span>
                      {store.status === 'FAILED' && store.error ? (
                        <div className="error-text">{store.error}</div>
                      ) : null}
                    </td>
                    <td>{store.creator_name || 'Unknown'}</td>
                    <td>
                      {store.status === 'READY' && store.url ? (
                        <a href={store.url} target="_blank" rel="noreferrer">
                          {store.url}
                        </a>
                      ) : (
                        <span className="muted">-</span>
                      )}
                    </td>
                    <td>{formatDate(store.created_at)}</td>
                    <td>
                      {store.creator_id === user?.id ? (
                        <button
                          type="button"
                          className="danger-button"
                          onClick={() => onDelete(store)}
                        >
                          Delete
                        </button>
                      ) : (
                        <span className="muted" style={{ fontSize: '13px' }}>-</span>
                      )}
                    </td>
                  </tr>
                  {expandedStore === store.id && 
                   store.status === 'READY' && 
                   store.creator_id === user?.id && (
                    <tr key={`${store.id}-details`}>
                      <td colSpan={7} style={{ backgroundColor: '#f8f9fa', padding: '15px' }}>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                          <div style={{ marginBottom: '8px', color: '#666', fontSize: '13px' }}>
                            <strong>🔒 Admin Credentials</strong> (visible only to you)
                          </div>
                          <div>
                            <strong>Admin Panel:</strong>{' '}
                            <a href={getAdminUrl(store) || '#'} target="_blank" rel="noreferrer">
                              {getAdminUrl(store)}
                            </a>
                          </div>
                          <div>
                            <strong>Username:</strong> <code>user</code>
                          </div>
                          <div>
                            <strong>Password:</strong>{' '}
                            {store.password ? (
                              <code>{store.password}</code>
                            ) : (
                              <em style={{ color: '#666' }}>Loading...</em>
                            )}
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
