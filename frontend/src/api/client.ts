export const API_BASE_URL = 'https://procure-system.onrender.com'

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

export interface RequestOptions {
  method?: HttpMethod
  body?: any
  auth?: boolean
  isFormData?: boolean
}

export async function apiRequest<T>(
  path: string,
  { method = 'GET', body, auth = false, isFormData = false }: RequestOptions = {}
): Promise<T> {
  const headers: Record<string, string> = {}

  if (!isFormData) {
    headers['Content-Type'] = 'application/json'
  }

  if (auth) {
    const token = localStorage.getItem('access_token')
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body ? (isFormData ? body : JSON.stringify(body)) : undefined,
  })

  const data = await res.json().catch(() => null)

  if (!res.ok) {
    
    if (data && typeof data === 'object' && !data.detail && !data.message) {
      const errorMessages = Object.entries(data)
        .map(([key, value]: [string, any]) => {
          if (Array.isArray(value)) {
            return `${key}: ${value.join(', ')}`
          }
          return `${key}: ${JSON.stringify(value)}`
        })
        .join('; ')
      throw new Error(errorMessages || 'Validation failed')
    }
    const message =
      typeof data === 'string'
        ? data
        : data?.detail || data?.message || 'Request failed'
    throw new Error(message)
  }

  return data as T
}
