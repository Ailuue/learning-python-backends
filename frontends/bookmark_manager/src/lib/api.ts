import { getToken } from './auth'
import type {
  Bookmark,
  BookmarkInput,
  Category,
  CategoryInput,
  Tag,
  Token,
  User,
} from '../types'

export const API_URL = 'http://localhost:8002'

export class ApiError extends Error {
  status: number
  detail: unknown
  constructor(status: number, detail: unknown, message: string) {
    super(message)
    this.status = status
    this.detail = detail
  }
}

function extractDetail(data: unknown, fallback: string): string {
  if (typeof data === 'object' && data !== null && 'detail' in data) {
    const detail = (data as { detail: unknown }).detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0]
      if (typeof first === 'object' && first && 'msg' in first) {
        return String((first as { msg: unknown }).msg)
      }
    }
  }
  return fallback
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> | undefined),
  }
  if (token) headers['Authorization'] = `Bearer ${token}`
  if (options.body && typeof options.body === 'string' && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json'
  }

  const res = await fetch(`${API_URL}${path}`, { ...options, headers })

  if (res.status === 204) {
    return undefined as T
  }

  const contentType = res.headers.get('content-type') ?? ''
  const data: unknown = contentType.includes('application/json')
    ? await res.json()
    : await res.text()

  if (!res.ok) {
    if (res.status === 401 && getToken()) {
      window.dispatchEvent(new CustomEvent('auth:unauthorized'))
    }
    throw new ApiError(
      res.status,
      data,
      extractDetail(data, `Request failed: ${res.status}`)
    )
  }

  return data as T
}

export const authApi = {
  register(data: { email: string; username: string; password: string }) {
    return request<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  login(username: string, password: string): Promise<Token> {
    const form = new URLSearchParams()
    form.set('username', username)
    form.set('password', password)
    return request<Token>('/auth/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form.toString(),
    })
  },

  me() {
    return request<User>('/auth/me')
  },

  logout() {
    return request<void>('/auth/logout', { method: 'POST' })
  },
}

export const bookmarkApi = {
  list(params: { category_id?: number; favorite?: boolean; tag?: string } = {}) {
    const q = new URLSearchParams()
    if (params.category_id != null) q.set('category_id', String(params.category_id))
    if (params.favorite != null) q.set('favorite', String(params.favorite))
    if (params.tag) q.set('tag', params.tag)
    const path = q.toString() ? `/bookmarks/?${q}` : '/bookmarks/'
    return request<Bookmark[]>(path)
  },

  create(data: BookmarkInput) {
    return request<Bookmark>('/bookmarks/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  update(id: number, data: Partial<BookmarkInput>) {
    return request<Bookmark>(`/bookmarks/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  },

  delete(id: number) {
    return request<void>(`/bookmarks/${id}`, { method: 'DELETE' })
  },

  recordClick(id: number) {
    return request<void>(`/bookmarks/${id}/click`, { method: 'POST' })
  },
}

export const categoryApi = {
  list() {
    return request<Category[]>('/categories/')
  },

  create(data: CategoryInput) {
    return request<Category>('/categories/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  update(id: number, data: Partial<CategoryInput>) {
    return request<Category>(`/categories/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  },

  delete(id: number) {
    return request<void>(`/categories/${id}`, { method: 'DELETE' })
  },
}

export const tagApi = {
  list() {
    return request<Tag[]>('/tags/')
  },

  delete(id: number) {
    return request<void>(`/tags/${id}`, { method: 'DELETE' })
  },
}
