import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, FileText, Image, X, CheckCircle, AlertCircle, Sparkles } from 'lucide-react'
import { uploadDocument, API_BASE } from '../api/client'

function formatBytes(bytes) {
  if (bytes < 1024)       return `${bytes} B`
  if (bytes < 1048576)    return `${(bytes/1024).toFixed(1)} KB`
  return `${(bytes/1048576).toFixed(1)} MB`
}

function FileIcon({ type }) {
  if (type === 'application/pdf') return <FileText size={22} />
  return <Image size={22} />
}

const STAGES = ['Uploading', 'Preprocessing', 'OCR', 'PDF Generation', 'Embedding', 'Done']

export default function UploadPage() {
  const [files, setFiles]       = useState([])
  const [dragging, setDragging] = useState(false)
  const inputRef                = useRef(null)
  const navigate                = useNavigate()

  const addFiles = (newFiles) => {
    const list = Array.from(newFiles).map(f => ({
      id: `${f.name}-${Date.now()}`,
      file: f,
      progress: 0,
      stage: 'idle', // idle | uploading | processing | done | error
      stageIdx: 0,
      error: null,
      docId: null,
      ocrText: '',
    }))
    setFiles(prev => [...prev, ...list])
    list.forEach(item => startUpload(item))
  }

  const startUpload = async (item) => {
    // Animate through "Uploading" stage
    setFiles(prev => prev.map(f => f.id === item.id
      ? { ...f, stage: 'uploading', stageIdx: 0 }
      : f))

    try {
      const data = await uploadDocument(item.file, (pct) => {
        setFiles(prev => prev.map(f => f.id === item.id ? { ...f, progress: pct } : f))
      })

      // Proceed to processing and connect to SSE
      setFiles(prev => prev.map(f => f.id === item.id
        ? { ...f, stage: 'processing', stageIdx: 1, docId: data.document?.id, progress: 100 }
        : f))

      if (data.document?.id) {
          await listenToEvents(item.id, data.document.id)
      } else {
          setFiles(prev => prev.map(f => f.id === item.id ? { ...f, stage: 'done', stageIdx: 5 } : f))
      }
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Upload failed'
      setFiles(prev => prev.map(f => f.id === item.id
        ? { ...f, stage: 'error', error: msg }
        : f))
    }
  }

  const listenToEvents = async (itemId, docId) => {
    // We now use native EventSource with credentials since the token is in cookies
    const eventSource = new EventSource(`${API_BASE}/documents/${docId}/events`, {
      withCredentials: true
    })

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        const stepIdx = STAGES.indexOf(data.step)
        
        setFiles(prev => prev.map(f => {
          if (f.id !== itemId) return f
          // Keep current status if processing, otherwise jump to done/error
          const newStage = data.status === 'completed' ? 'done' : data.status === 'failed' ? 'error' : 'processing'
          
          return {
            ...f, 
            stage: newStage,
            stageIdx: stepIdx >= 0 ? stepIdx : f.stageIdx,
            ocrText: data.ocr_text || f.ocrText,
            error: data.error || f.error
          }
        }))

        if (data.status === 'completed' || data.status === 'failed') {
          eventSource.close()
        }
      } catch (e) { /* ignore parse error */ }
    }

    eventSource.onerror = (error) => {
      eventSource.close()
      // Only set error if we aren't already done
      setFiles(prev => prev.map(f => {
        if (f.id === itemId && f.stage !== 'done') {
           return { ...f, stage: 'error', error: 'Event stream connection error.' }
        }
        return f
      }))
    }
  }

  const onDrop = (e) => {
    e.preventDefault(); setDragging(false)
    addFiles(e.dataTransfer.files)
  }

  const removeFile = (id) => setFiles(prev => prev.filter(f => f.id !== id))

  return (
    <main className="page-content upload-page">
      <div className="upload-hero">
        <h1>Upload Your Documents</h1>
        <p>Drop handwritten notes, printed text, or PDFs — our pipeline handles OCR, indexing, and AI-ready retrieval automatically.</p>
      </div>

      {/* Drop Zone */}
      <div
        className={`dropzone${dragging ? ' drag-over' : ''}`}
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={e => e.key === 'Enter' && inputRef.current?.click()}
        aria-label="File upload zone"
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".jpg,.jpeg,.png,.tiff,.tif,.pdf"
          onChange={e => { addFiles(e.target.files); e.target.value = '' }}
        />
        <div className="dropzone-icon">
          <Upload size={28} />
        </div>
        <h3>Drag & drop files here</h3>
        <p>or click to browse from your computer</p>
        <div className="formats">
          {['JPG', 'PNG', 'PDF', 'TIFF'].map(f => <span key={f} className="format-chip">{f}</span>)}
        </div>
      </div>

      {/* Upload Queue */}
      {files.length > 0 && (
        <div className="upload-queue">
          {files.map(item => (
            <div className="upload-item" key={item.id}>
              <div className="upload-item-icon">
                <FileIcon type={item.file.type} />
              </div>
              <div className="upload-item-info">
                <div className="upload-item-name">{item.file.name}</div>
                <div className="upload-item-size">{formatBytes(item.file.size)}</div>

                {item.stage === 'uploading' && (
                  <div className="progress-bar-track" style={{marginTop:8}}>
                    <div className="progress-bar-fill" style={{width:`${item.progress}%`}} />
                  </div>
                )}

                {item.stage === 'processing' && (
                  <div style={{marginTop:6, fontSize:'0.78rem', color:'var(--accent-warning)', display:'flex', alignItems:'center', gap:6}}>
                    <span className="pulse-dot" style={{background:'var(--accent-warning)'}} />
                    {STAGES[item.stageIdx]}…
                  </div>
                )}

                {item.stage === 'done' && (
                  <div style={{marginTop:6, fontSize:'0.78rem', color:'var(--accent-success)', display:'flex', alignItems:'center', gap:6}}>
                    <CheckCircle size={13} /> Ready for querying
                  </div>
                )}

                {item.stage === 'error' && (
                  <div style={{marginTop:6, fontSize:'0.78rem', color:'var(--accent-danger)', display:'flex', alignItems:'center', gap:6}}>
                    <AlertCircle size={13} /> {item.error}
                  </div>
                )}
              </div>

              {(item.stage === 'done' || item.stage === 'error') && (
                <button className="btn btn-ghost" style={{padding:'6px'}} onClick={() => removeFile(item.id)}>
                  <X size={15} />
                </button>
              )}
              
              {/* Display intermediate OCR text in real-time as a preview */}
              {item.ocrText && (
                <div style={{ marginTop: 12, padding: 12, background: 'var(--bg-card)', borderRadius: 6, width: '100%', fontSize: '0.85rem' }}>
                  <div style={{color: 'var(--text-muted)', marginBottom: 6, fontWeight: 500}}>Live OCR Preview:</div>
                  <pre style={{ 
                    margin: 0, 
                    whiteSpace: 'pre-wrap', 
                    fontFamily: 'inherit', 
                    color: 'var(--text-primary)',
                    maxHeight: '120px',
                    overflowY: 'auto'
                  }}>
                    {item.ocrText}
                  </pre>
                </div>
              )}
            </div>
          ))}

          {files.some(f => f.stage === 'done') && (
            <button className="btn btn-primary" style={{alignSelf:'flex-end'}} onClick={() => navigate('/chat')}>
              <Sparkles size={15} /> Start querying
            </button>
          )}
        </div>
      )}
    </main>
  )
}
