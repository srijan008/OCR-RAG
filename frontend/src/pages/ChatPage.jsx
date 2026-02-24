import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, BookOpen, Zap } from 'lucide-react'
import { queryRAG } from '../api/client'
import { useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import { useAuth } from '../context/AuthContext'

function TypingIndicator() {
  return (
    <div className="chat-message">
      <div className="msg-avatar ai"><Bot size={16} /></div>
      <div className="msg-bubble ai">
        <div className="typing-dots">
          <div className="typing-dot" />
          <div className="typing-dot" />
          <div className="typing-dot" />
        </div>
      </div>
    </div>
  )
}

function Message({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <div className={`chat-message ${isUser ? 'user' : ''}`}>
      <div className={`msg-avatar ${isUser ? 'user' : 'ai'}`}>
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>
      <div className={`msg-bubble ${isUser ? 'user' : 'ai'}`}>
        <div className="markdown-content">
          <ReactMarkdown>{msg.content}</ReactMarkdown>
        </div>

        {msg.sources && msg.sources.length > 0 && (
          <div className="msg-sources">
            <div className="msg-sources-title">Sources</div>
            <div>
              {[...new Map(msg.sources.map(s => [s.document_name, s])).values()].map((s, i) => (
                <span key={i} className="source-tag">
                  <BookOpen size={10} />
                  {s.document_name} · p{s.page_number}
                  <span style={{opacity:0.6, marginLeft:3}}>
                    {(s.similarity_score * 100).toFixed(0)}%
                  </span>
                </span>
              ))}
            </div>
          </div>
        )}

        {msg.model && (
          <div style={{marginTop:8, fontSize:'0.72rem', color:'var(--text-muted)', display:'flex', alignItems:'center', gap:4}}>
            <Zap size={10} /> {msg.model}
          </div>
        )}
      </div>
    </div>
  )
}

const WELCOME = {
  role: 'ai',
  content: `Hello! I'm your RAG-powered document assistant backed by Gemini 2.5 Flash.\n\nUpload documents first, then ask me anything about them — I'll retrieve relevant context and give you a grounded answer with source citations.\n\nTry: "Summarize the main topics" or "What does the document say about X?"`,
  id: 'welcome',
}

export default function ChatPage() {
  const { user } = useAuth()
  const storageKey = user ? `chat_history_${user.id}` : 'chat_history_guest'

  const [messages, setMessages] = useState(() => {
    const saved = localStorage.getItem(storageKey)
    return saved ? JSON.parse(saved) : [WELCOME]
  })
  const [input,    setInput]    = useState('')
  const [loading,  setLoading]  = useState(false)
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)
  const navigate = useNavigate()

  useEffect(() => {
    localStorage.setItem(storageKey, JSON.stringify(messages))
  }, [messages, storageKey])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const send = async () => {
    const q = input.trim()
    if (!q || loading) return

    const userMsg = { id: Date.now(), role: 'user', content: q }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const data = await queryRAG(q)
      const aiMsg = {
        id: Date.now() + 1,
        role: 'ai',
        content: data.answer,
        sources: data.sources,
        model: data.model,
      }
      setMessages(prev => [...prev, aiMsg])
    } catch (err) {
      const errMsg = {
        id: Date.now() + 1,
        role: 'ai',
        content: `⚠️ Error: ${err.response?.data?.detail || err.message || 'Query failed. Make sure the backend is running and documents are uploaded.'}`,
      }
      setMessages(prev => [...prev, errMsg])
    } finally {
      setLoading(false)
    }
  }

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  // Auto-resize textarea
  const onInput = (e) => {
    setInput(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 140) + 'px'
  }

  return (
    <div className="chat-layout">
      <div className="chat-header">
        <h1><Bot size={22} style={{verticalAlign:'middle', marginRight:8}} />Document Chat</h1>
        <p>Ask questions about your uploaded documents — powered by Gemini 3 Flash + Cohere RAG</p>
      </div>

      <div className="chat-messages">
        {messages.map(msg => <Message key={msg.id} msg={msg} />)}
        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      <div className="chat-input-area">
        <div className="chat-input-row">
          <textarea
            ref={textareaRef}
            className="chat-input"
            rows={1}
            placeholder="Ask anything about your documents… (Enter to send, Shift+Enter for newline)"
            value={input}
            onChange={onInput}
            onKeyDown={onKeyDown}
            disabled={loading}
            id="chat-input"
          />
          <button
            className="btn btn-primary"
            onClick={send}
            disabled={loading || !input.trim()}
            style={{height: 46, minWidth: 46, padding: '0 16px'}}
            id="send-btn"
          >
            <Send size={16} />
          </button>
        </div>
        <div style={{fontSize:'0.72rem', color:'var(--text-muted)', marginTop:8, textAlign:'center'}}>
          No documents yet?{' '}
          <span
            style={{color:'var(--accent-primary)', cursor:'pointer'}}
            onClick={() => navigate('/upload')}
          >
            Upload one first →
          </span>
        </div>
      </div>
    </div>
  )
}
