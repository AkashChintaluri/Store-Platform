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
                <tr key={store.id}>
                  <td>{store.name}</td>
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
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
