import { NavLink, useNavigate } from 'react-router-dom'
import { Upload, BookOpen, MessageSquare, Cpu, LogOut, User } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const links = [
  { to: '/upload',  icon: <Upload        size={16} />, label: 'Upload'  },
  { to: '/library', icon: <BookOpen      size={16} />, label: 'Library' },
  { to: '/chat',    icon: <MessageSquare size={16} />, label: 'Chat'    },
]

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate         = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <div className="navbar-brand-icon"><Cpu size={16} color="white" /></div>
        <span>OCR·RAG</span>
      </div>

      <div className="navbar-links">
        {links.map(({ to, icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
          >
            {icon}{label}
          </NavLink>
        ))}
      </div>

      <div className="navbar-user">
        <div className="user-chip">
          <User size={13} />
          <span>{user?.name?.split(' ')[0] ?? 'You'}</span>
        </div>
        <button className="logout-btn" onClick={handleLogout} title="Sign out">
          <LogOut size={15} />
        </button>
      </div>
    </nav>
  )
}
