// Deployment-friendly API base resolution.
// Use VITE_API_BASE (set in Amplify/locally); fallback to local dev API.
const rawBase = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000/api'

// Normalize: remove trailing slash but keep leading slash or scheme.
export const API_BASE = rawBase.endsWith('/') && rawBase.length > 1
  ? rawBase.slice(0, -1)
  : rawBase