import { useEffect, useState } from 'react'
import './App.css'
import Home from './pages/Home'
import Login from './components/Login'
import Signup from './components/Signup'
import { useAuth } from './state/useAuth'

function App() {
  const { user, checkAuth } = useAuth()
  const [showSignup, setShowSignup] = useState(false)

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  // Show login/signup if not authenticated
  if (!user) {
    return showSignup ? (
      <Signup onSwitchToLogin={() => setShowSignup(false)} />
    ) : (
      <Login onSwitchToSignup={() => setShowSignup(true)} />
    )
  }

  // Show main app if authenticated
  return <Home />
}

export default App
