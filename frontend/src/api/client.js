import axios from 'axios'

export const API_BASE = import.meta.env.VITE_API_URL

const client = axios.create({
    baseURL: API_BASE,
    timeout: 120000,
    withCredentials: true,
})

// Attach JWT token to every request automatically
client.interceptors.request.use((config) => {
    const token = localStorage.getItem('token')
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
})

// Redirect to login on 401 (except for login requests)
client.interceptors.response.use(
    (res) => res,
    (err) => {
        const isLoginReq = err.config?.url?.includes('/auth/login')
        if (err.response?.status === 401 && !isLoginReq) {
            document.cookie = "token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;"
            localStorage.removeItem('token')
            localStorage.removeItem('user')
            window.location.href = '/login'
        }
        return Promise.reject(err)
    }
)

// ── Auth ───────────────────────────────────────────────────────────────────
export const signup = (name, email, password) =>
    client.post('/auth/signup', { name, email, password }).then(r => {
        document.cookie = `token=${r.data.access_token}; path=/; max-age=604800; SameSite=Lax`
        return r.data
    })

export const login = (email, password) =>
    client.post('/auth/login', { email, password }).then(r => {
        document.cookie = `token=${r.data.access_token}; path=/; max-age=604800; SameSite=Lax`
        return r.data
    })

export const getMe = () =>
    client.get('/auth/me').then(r => r.data)

// ── Documents ──────────────────────────────────────────────────────────────
export const fetchDocuments = () => client.get('/documents').then(r => r.data)
export const fetchDocument = (id) => client.get(`/documents/${id}`).then(r => r.data)
export const deleteDocument = (id) => client.delete(`/documents/${id}`).then(r => r.data)
export const getDownloadUrl = (id) => `${API_BASE}/documents/${id}/download`
export const downloadDocument = (id) => client.get(`/documents/${id}/download`, { responseType: 'blob' }).then(r => r.data)

// ── Upload ─────────────────────────────────────────────────────────────────
export const uploadDocument = (file, onProgress) => {
    const formData = new FormData()
    formData.append('file', file)
    return client.post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: e => onProgress && onProgress(Math.round((e.loaded * 100) / e.total)),
    }).then(r => r.data)
}

// ── Query ──────────────────────────────────────────────────────────────────
export const queryRAG = (query, topK = 5, documentIds = null) =>
    client.post('/query', { query, top_k: topK, document_ids: documentIds }).then(r => r.data)

export default client
