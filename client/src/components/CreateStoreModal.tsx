import { useState, type FormEvent } from 'react'
import { useStore } from '../state/useStore'

const ENGINES = [
  { value: 'woocommerce', label: 'WooCommerce' },
  { value: 'medusa', label: 'Medusa' },
] as const

type Props = {
  open: boolean
  onClose: () => void
}

export default function CreateStoreModal({ open, onClose }: Props) {
  const createStore = useStore((state) => state.createStore)
  const [name, setName] = useState('')
  const [engine, setEngine] = useState<'woocommerce' | 'medusa'>('woocommerce')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  if (!open) {
    return null
  }

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await createStore({ name: name.trim(), engine })
      setName('')
      setEngine('woocommerce')
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create store')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-backdrop">
      <div className="modal">
        <div className="modal-header">
          <h2>Create Store</h2>
          <button type="button" className="ghost-button" onClick={onClose}>
            Close
          </button>
        </div>
        <form className="form" onSubmit={onSubmit}>
          <label className="field">
            <span>Store name</span>
            <input
              type="text"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="my-store"
              required
            />
          </label>
          <label className="field">
            <span>Engine</span>
            <select
              value={engine}
              onChange={(event) =>
                setEngine(event.target.value as 'woocommerce' | 'medusa')
              }
            >
              {ENGINES.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          {error ? <p className="error-text">{error}</p> : null}
          <div className="form-actions">
            <button type="submit" disabled={submitting || name.trim().length < 1}>
              {submitting ? 'Creating…' : 'Create Store'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
