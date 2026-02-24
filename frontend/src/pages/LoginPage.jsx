import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Mail, Lock, Cpu, AlertCircle, Eye, EyeOff } from 'lucide-react'
import { login } from '../api/client'
import { useAuth } from '../context/AuthContext'

export default function LoginPage() {
  const [form,    setForm]    = useState({ email: '', password: '' })
  const [error,   setError]   = useState(null)
  const [loading, setLoading] = useState(false)
  const [showPw,  setShowPw]  = useState(false)
  const { saveSession }       = useAuth()
  const navigate              = useNavigate()

  const handle = (e) => setForm(prev => ({ ...prev, [e.target.name]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const data = await login(form.email, form.password)
      saveSession(data)
      navigate('/upload')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Check your credentials.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-brand">
          <div className="navbar-brand-icon" style={{width:44,height:44,borderRadius:14}}>
            <Cpu size={22} color="white" />
          </div>
          <h1>OCR·RAG</h1>
        </div>
        <h2>Welcome back</h2>
        <p className="auth-sub">Sign in to access your personal document library.</p>

        {error && (
          <div className="auth-error">
            <AlertCircle size={14} /> {error}
          </div>
        )}

        <form onSubmit={submit} className="auth-form">
          <div className="form-field">
            <label htmlFor="email">Email</label>
            <div className="input-wrap">
              <Mail size={15} className="input-icon" />
              <input id="email" name="email" type="email" placeholder="you@example.com"
                value={form.email} onChange={handle} required autoComplete="email" autoFocus />
            </div>
          </div>

          <div className="form-field">
            <label htmlFor="password">Password</label>
            <div className="input-wrap">
              <Lock size={15} className="input-icon" />
              <input id="password" name="password" type={showPw ? 'text' : 'password'}
                placeholder="••••••••" value={form.password} onChange={handle} required
                autoComplete="current-password" />
              <button type="button" className="pw-toggle" onClick={() => setShowPw(p => !p)} tabIndex={-1}>
                {showPw ? <EyeOff size={14}/> : <Eye size={14}/>}
              </button>
            </div>
          </div>

          <button className="btn btn-primary" type="submit" disabled={loading} style={{width:'100%',marginTop:4}}>
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <p className="auth-footer">
          Don't have an account? <Link to="/signup">Create one</Link>
        </p>
      </div>
    </div>
  )
}
