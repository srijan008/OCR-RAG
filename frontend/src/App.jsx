import { Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Navbar      from './components/Navbar'
import UploadPage  from './pages/UploadPage'
import LibraryPage from './pages/LibraryPage'
import ChatPage    from './pages/ChatPage'
import LoginPage   from './pages/LoginPage'
import SignupPage  from './pages/SignupPage'

// Redirect unauthenticated users to /login
function Protected({ children }) {
  const { user, loading } = useAuth()
  if (loading) return null
  return user ? children : <Navigate to="/login" replace />
}

// Redirect logged-in users away from auth pages
function AuthOnly({ children }) {
  const { user, loading } = useAuth()
  if (loading) return null
  return user ? <Navigate to="/upload" replace /> : children
}

function AppShell() {
  const { user } = useAuth()
  return (
    <>
      {user && <Navbar />}
      <div className={user ? 'main-content' : ''}>
        <Routes>
          <Route path="/login"  element={<AuthOnly><LoginPage  /></AuthOnly>} />
          <Route path="/signup" element={<AuthOnly><SignupPage /></AuthOnly>} />
          <Route path="/upload"  element={<Protected><UploadPage  /></Protected>} />
          <Route path="/library" element={<Protected><LibraryPage /></Protected>} />
          <Route path="/chat"    element={<Protected><ChatPage    /></Protected>} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </div>
    </>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppShell />
    </AuthProvider>
  )
}
