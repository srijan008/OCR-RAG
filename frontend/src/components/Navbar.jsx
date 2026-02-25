import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { Upload, BookOpen, MessageSquare, Cpu, LogOut, User, Menu, X } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const links = [
  { to: '/upload',  icon: <Upload        size={16} />, label: 'Upload'  },
  { to: '/library', icon: <BookOpen      size={16} />, label: 'Library' },
  { to: '/chat',    icon: <MessageSquare size={16} />, label: 'Chat'    },
]

export default function Navbar() {
  const { user, logout }    = useAuth()
  const navigate            = useNavigate()
  const [isOpen, setIsOpen] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const closeMenu = () => setIsOpen(false)

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <NavLink to="/library" className="navbar-brand" onClick={closeMenu}>
          <div className="navbar-brand-icon"><Cpu size={16} color="white" /></div>
          <span>OCR·RAG</span>
        </NavLink>

        {/* Desktop Links */}
        <div className="navbar-links desktop-only">
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

        <div className="navbar-right">
          <div className="navbar-user desktop-only">
            <div className="user-chip">
              <User size={13} />
              <span>{user?.name?.split(' ')[0] ?? 'You'}</span>
            </div>
            <button className="logout-btn" onClick={handleLogout} title="Sign out">
              <LogOut size={15} />
            </button>
          </div>

          {/* Mobile Toggle */}
          <button className="mobile-toggle" onClick={() => setIsOpen(!isOpen)}>
            {isOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {/* Mobile Menu Overlay */}
      {isOpen && (
        <div className="mobile-menu">
          <div className="mobile-menu-links">
            {links.map(({ to, icon, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) => `mobile-nav-link${isActive ? ' active' : ''}`}
                onClick={closeMenu}
              >
                {icon}{label}
              </NavLink>
            ))}
            <div className="mobile-user-row">
              <div className="user-chip">
                <User size={13} />
                <span>{user?.name ?? 'Account'}</span>
              </div>
              <button className="btn btn-danger" onClick={() => { handleLogout(); closeMenu(); }}>
                <LogOut size={15} /> Sign Out
              </button>
            </div>
          </div>
        </div>
      )}
    </nav>
  )
}
