import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Mail, Lock, User, Cpu, AlertCircle, Eye, EyeOff } from 'lucide-react'
import { signup } from '../api/client'
import { useAuth } from '../context/AuthContext'

export default function SignupPage() {
  const [form,    setForm]    = useState({ name: '', email: '', password: '' })
  const [error,   setError]   = useState(null)
  const [loading, setLoading] = useState(false)
  const [showPw,  setShowPw]  = useState(false)
  const { saveSession }       = useAuth()
  const navigate              = useNavigate()

  const handle = (e) => setForm(prev => ({ ...prev, [e.target.name]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    setError(null)
    if (form.password.length < 8) { setError('Password must be at least 8 characters.'); return }
    setLoading(true)
    try {
      const data = await signup(form.name, form.email, form.password)
      saveSession(data)
      navigate('/upload')
    } catch (err) {
      setError(err.response?.data?.detail || 'Signup failed. Please try again.')
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
        <h2>Create your account</h2>
        <p className="auth-sub">Upload, search, and chat with your documents — privately.</p>

        {error && (
          <div className="auth-error">
            <AlertCircle size={14} /> {error}
          </div>
        )}

        <form onSubmit={submit} className="auth-form">
          <div className="form-field">
            <label htmlFor="name">Full name</label>
            <div className="input-wrap">
              <User size={15} className="input-icon" />
              <input id="name" name="name" type="text" placeholder="Jane Smith"
                value={form.name} onChange={handle} required autoComplete="name" />
            </div>
          </div>

          <div className="form-field">
            <label htmlFor="email">Email</label>
            <div className="input-wrap">
              <Mail size={15} className="input-icon" />
              <input id="email" name="email" type="email" placeholder="you@example.com"
                value={form.email} onChange={handle} required autoComplete="email" />
            </div>
          </div>

          <div className="form-field">
            <label htmlFor="password">Password <span style={{color:'var(--text-muted)',fontWeight:400}}>(min 8 chars)</span></label>
            <div className="input-wrap">
              <Lock size={15} className="input-icon" />
              <input id="password" name="password" type={showPw ? 'text' : 'password'}
                placeholder="••••••••" value={form.password} onChange={handle} required
                autoComplete="new-password" />
              <button type="button" className="pw-toggle" onClick={() => setShowPw(p => !p)} tabIndex={-1}>
                {showPw ? <EyeOff size={14}/> : <Eye size={14}/>}
              </button>
            </div>
          </div>

          <button className="btn btn-primary" type="submit" disabled={loading} style={{width:'100%',marginTop:4}}>
            {loading ? 'Creating account…' : 'Create account'}
          </button>
        </form>

        <p className="auth-footer">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
