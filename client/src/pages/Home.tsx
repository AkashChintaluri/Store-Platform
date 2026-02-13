import { useEffect, useState } from 'react'
import CreateStoreModal from '../components/CreateStoreModal'
import StoreTable from '../components/StoreTable'
import { useStore } from '../state/useStore'
import { useAuth } from '../state/useAuth'

const POLL_INTERVAL_MS = 5000

export default function Home() {
  const fetchStores = useStore((state) => state.fetchStores)
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)

  useEffect(() => {
    fetchStores().catch(() => undefined)
    const interval = window.setInterval(() => {
      fetchStores().catch(() => undefined)
    }, POLL_INTERVAL_MS)

    return () => window.clearInterval(interval)
  }, [fetchStores])

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">FastAPI Store Control</p>
          <h1>Store Dashboard</h1>
          <p className="subtle">
            Manage store provisioning and check real-time status updates.
          </p>
        </div>
        <div className="header-actions" style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ fontSize: '14px', color: '#666' }}>
            Welcome, <strong>{user?.name}</strong>
          </div>
          <button
            type="button"
            onClick={logout}
            style={{
              padding: '8px 16px',
              backgroundColor: '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Logout
          </button>
          <button type="button" onClick={() => setOpen(true)}>
            Create Store
          </button>
        </div>
      </header>

      <CreateStoreModal open={open} onClose={() => setOpen(false)} />
      <StoreTable />
    </div>
  )
}
