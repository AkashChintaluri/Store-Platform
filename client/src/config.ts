// Deployment-friendly API base resolution.
// Use VITE_API_BASE for production (e.g., https://api.example.com/api), fallback to dev proxy /api.
const rawBase = import.meta.env.VITE_API_BASE ?? '/api'

// Normalize: remove trailing slash but keep leading slash or scheme.
export const API_BASE = rawBase.endsWith('/') && rawBase.length > 1
  ? rawBase.slice(0, -1)
  : rawBase