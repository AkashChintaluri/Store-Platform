import { useState } from 'react'
import { useStore } from '../state/useStore'

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

export default function StoreTable() {
  const stores = useStore((state) => state.stores)
  const loading = useStore((state) => state.loading)
  const deleteStore = useStore((state) => state.deleteStore)
  const [expandedStore, setExpandedStore] = useState<string | null>(null)

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
      // eslint-disable-next-line no-console
      console.error(err)
    }
  }

  return (
    <div className="table-card">
      <div className="table-header">
        <h3>Stores</h3>
        {loading ? <span className="muted">Refreshing…</span> : null}
      </div>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Engine</th>
              <th>Status</th>
              <th>URL</th>
              <th>Created At</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {stores.length === 0 ? (
              <tr>
                <td colSpan={6} className="empty">
                  No stores yet.
                </td>
              </tr>
            ) : (
              stores.map((store) => (
                <>
                  <tr key={store.id}>
                    <td>
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
                      >
                        {store.name}
                      </button>
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
                      <button
                        type="button"
                        className="danger-button"
                        onClick={() => onDelete(store)}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                  {expandedStore === store.id && store.status === 'READY' && (
                    <tr key={`${store.id}-details`}>
                      <td colSpan={6} style={{ backgroundColor: '#f8f9fa', padding: '15px' }}>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
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
