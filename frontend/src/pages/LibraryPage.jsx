import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  FileText, Image, RefreshCw, Download, Trash2, MessageSquare,
  BookOpen, FileStack, Percent, Hash
} from 'lucide-react'
import { fetchDocuments, deleteDocument, getDownloadUrl, downloadDocument } from '../api/client'

function StatusBadge({ status }) {
  const map = {
    pending:    { label: 'Pending',    cls: 'badge-pending' },
    processing: { label: 'Processing', cls: 'badge-processing' },
    completed:  { label: 'Completed',  cls: 'badge-completed' },
    failed:     { label: 'Failed',     cls: 'badge-failed' },
  }
  const s = map[status] || map.pending
  return (
    <span className={`badge ${s.cls}`}>
      {status === 'processing' && <span className="pulse-dot" />}
      {s.label}
    </span>
  )
}

function DocIcon({ fileType }) {
  if (fileType === '.pdf') return <FileText size={20} />
  return <Image size={20} />
}

function timeAgo(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime()
  const m = Math.floor(diff / 60000)
  if (m < 1)   return 'just now'
  if (m < 60)  return `${m}m ago`
  if (m < 1440)return `${Math.floor(m/60)}h ago`
  return `${Math.floor(m/1440)}d ago`
}

export default function LibraryPage() {
  const [docs,    setDocs]    = useState([])
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)
  const navigate = useNavigate()

  const load = async () => {
    setLoading(true); setError(null)
    try {
      const data = await fetchDocuments()
      setDocs(data.documents)
    } catch {
      setError('Failed to load documents.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // Auto-refresh to pick up processing completions
    const id = setInterval(() => {
      if (document.hasFocus()) load()
    }, 50000)
    return () => clearInterval(id)
  }, [])

  const handleDelete = async (e, id) => {
    e.stopPropagation()
    if (!confirm('Delete this document and all its chunks?')) return
    await deleteDocument(id)
    setDocs(prev => prev.filter(d => d.id !== id))
  }

  const handleDownload = async (e, id, filename) => {
    e.stopPropagation()
    try {
      const blob = await downloadDocument(id)
      const url = window.URL.createObjectURL(new Blob([blob]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${filename.split('.')[0]}_searchable.pdf`)
      document.body.appendChild(link)
      link.click()
      link.parentNode.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Download failed:', err)
      alert('Failed to download document.')
    }
  }

  return (
    <main className="page-content">
      <div className="library-header">
        <h1><BookOpen size={22} style={{verticalAlign:'middle', marginRight:8}} />Document Library</h1>
        <div style={{display:'flex', gap:10}}>
          <button className="btn btn-ghost" onClick={load} disabled={loading}>
            <RefreshCw size={14} className={loading ? 'spin' : ''} />
            Refresh
          </button>
          <button className="btn btn-primary" onClick={() => navigate('/upload')}>
            + Upload
          </button>
        </div>
      </div>

      {error && (
        <div style={{padding:'16px',background:'rgba(239,68,68,0.1)',border:'1px solid rgba(239,68,68,0.25)',borderRadius:'var(--radius-md)',color:'var(--accent-danger)',marginBottom:20}}>
          {error}
        </div>
      )}

      {loading && docs.length === 0 ? (
        <div className="empty-state">
          <div className="typing-dots" style={{justifyContent:'center', marginBottom:16}}>
            <div className="typing-dot" /><div className="typing-dot" /><div className="typing-dot" />
          </div>
          <p>Loading documents…</p>
        </div>
      ) : docs.length === 0 ? (
        <div className="empty-state">
          <FileStack size={56} className="empty-state-icon" />
          <h3>No documents yet</h3>
          <p>Upload your first document to get started.</p>
          <button className="btn btn-primary" style={{marginTop:20}} onClick={() => navigate('/upload')}>
            Upload Document
          </button>
        </div>
      ) : (
        <div className="docs-grid">
          {docs.map(doc => (
            <div className="doc-card" key={doc.id}>
              <div className="doc-card-header">
                <div className={`doc-card-icon ${doc.file_type === '.pdf' ? 'pdf' : 'img'}`}>
                  <DocIcon fileType={doc.file_type} />
                </div>
                <StatusBadge status={doc.status} />
              </div>

              <div className="doc-card-name" title={doc.original_filename}>
                {doc.original_filename}
              </div>

              <div className="doc-card-meta">
                <span><Hash size={11} /> {doc.chunk_count} chunks</span>
                <span><FileStack size={11} /> {doc.page_count} pages</span>
                {doc.ocr_confidence_avg > 0 && (
                  <span><Percent size={11} /> {doc.ocr_confidence_avg.toFixed(0)}% conf</span>
                )}
              </div>
              <div style={{fontSize:'0.72rem', color:'var(--text-muted)', marginTop:6}}>
                {timeAgo(doc.created_at)}
              </div>

              {doc.status === 'failed' && doc.error_message && (
                <div style={{
                  marginTop: 12,
                  padding: '8px 12px',
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.2)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.75rem',
                  color: 'var(--accent-danger)',
                  lineHeight: '1.4'
                }}>
                  <strong>Extraction Failed:</strong> {doc.error_message}
                </div>
              )}

              <div className="doc-card-actions">
                {doc.status === 'completed' && (
                  <>
                    <button
                      className="btn btn-ghost"
                      style={{flex:1, fontSize:'0.8rem', padding:'7px 12px'}}
                      onClick={e => handleDownload(e, doc.id, doc.original_filename)}
                    >
                      <Download size={13} /> PDF
                    </button>
                    <button
                      className="btn btn-primary"
                      style={{flex:1, fontSize:'0.8rem', padding:'7px 12px'}}
                      onClick={() => navigate('/chat')}
                    >
                      <MessageSquare size={13} /> Query
                    </button>
                  </>
                )}
                <button
                  className="btn btn-danger"
                  style={{padding:'7px 10px'}}
                  onClick={e => handleDelete(e, doc.id)}
                  title="Delete document"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  )
}
