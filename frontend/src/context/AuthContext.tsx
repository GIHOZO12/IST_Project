import React, { createContext, useContext, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiRequest } from '../api/client'

export type UserRole = 'staff' | 'manager_1' | 'manager_2' | 'finance' | null

interface AuthState {
  username: string | null
  role: UserRole
  accessToken: string | null
  refreshToken: string | null
}

interface LoginPayload {
  username: string
  password: string
}

interface AuthContextValue extends AuthState {
  loading: boolean
  error: string | null
  login: (payload: LoginPayload) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const navigate = useNavigate()
  const [state, setState] = useState<AuthState>(() => {
    const accessToken = localStorage.getItem('access_token')
    const refreshToken = localStorage.getItem('refresh_token')
    const username = localStorage.getItem('username')
    const role = (localStorage.getItem('user_role') as UserRole) || null

    if (accessToken && username && role) {
      return { accessToken, refreshToken, username, role }
    }

    return {
      username: null,
      role: null,
      accessToken: null,
      refreshToken: null,
    }
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const login = async ({ username, password }: LoginPayload) => {
    setLoading(true)
    setError(null)
    try {
      const data = await apiRequest<{
        refresh: string
        access: string
        message: string
        user: string
        role: string
      }>('/accounts/login/', {
        method: 'POST',
        body: { username, password },
      })

      localStorage.setItem('access_token', data.access)
      localStorage.setItem('refresh_token', data.refresh)
      localStorage.setItem('username', data.user)
      localStorage.setItem('user_role', data.role)

      const role = data.role as UserRole

      setState({
        username: data.user,
        role,
        accessToken: data.access,
        refreshToken: data.refresh,
      })

      if (role === 'staff') {
        navigate('/dashboard/staff', { replace: true })
      } else if (role === 'manager_1' || role === 'manager_2') {
        navigate('/dashboard/approver', { replace: true })
      } else if (role === 'finance') {
        navigate('/dashboard/finance', { replace: true })
      } else {
        navigate('/', { replace: true })
      }
    } catch (err: any) {
      setError(err.message || 'Login failed')
      throw err
    } finally {
      setLoading(false)
    }
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('username')
    localStorage.removeItem('user_role')
    setState({ username: null, role: null, accessToken: null, refreshToken: null })
    navigate('/login', { replace: true })
  }

  return (
    <AuthContext.Provider
      value={{
        ...state,
        loading,
        error,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return ctx
}
