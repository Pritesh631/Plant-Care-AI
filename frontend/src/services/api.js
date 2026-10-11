import axios from 'axios'

export const MAX_UPLOAD_MB = 5
export const ALLOWED_TYPES = ['image/jpeg', 'image/png']

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api',
  timeout: 60000,
})

/** Turn any axios failure into a readable message. */
export function errorMessage(err) {
  if (err?.response?.data?.error) return err.response.data.error
  if (err?.code === 'ECONNABORTED') return 'The request timed out. Please try again.'
  if (err?.request && !err.response) return 'Cannot reach the server. Check that the backend is running.'
  return err?.message || 'Something went wrong.'
}

export function validateImage(file) {
  if (!file) return 'No file selected.'
  if (!ALLOWED_TYPES.includes(file.type)) return 'Please choose a JPG, JPEG or PNG image.'
  if (file.size > MAX_UPLOAD_MB * 1024 * 1024) return `Image is larger than ${MAX_UPLOAD_MB} MB.`
  return null
}

export const getHealth = () => client.get('/health').then((r) => r.data)
export const getDiseases = () => client.get('/diseases').then((r) => r.data)
export const getHistory = () => client.get('/history').then((r) => r.data.items)
export const getAnalytics = () => client.get('/analytics').then((r) => r.data)
export const deleteHistoryItem = (id) => client.delete(`/history/${id}`).then((r) => r.data)
export const clearHistory = () => client.delete('/history').then((r) => r.data)

export function predictImage(file) {
  const form = new FormData()
  form.append('image', file)
  return client.post('/predict', form).then((r) => r.data)
}
