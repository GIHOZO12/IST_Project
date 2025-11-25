import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import StaffDashboard from './pages/StaffDashboard'
import ApproverDashboard from './pages/ApproverDashboard'
import FinanceDashboard from './pages/FinanceDashboard'
import { AuthProvider, useAuth } from './context/AuthContext'
import Activate from './pages/Activate'

type ProtectedRouteProps = {
  children: React.ReactElement
  allowedRoles?: string[]
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, allowedRoles }) => {
  const { accessToken, role } = useAuth()

  if (!accessToken) {
    return <Navigate to="/login" replace />
  }

  if (allowedRoles && (!role || !allowedRoles.includes(role))) {
    return <Navigate to="/login" replace />
  }

  return children
}

const DefaultRedirect: React.FC = () => {
  const { role } = useAuth()

  if (role === 'staff') return <Navigate to="/dashboard/staff" replace />
  if (role === 'manager_1' || role === 'manager_2')
    return <Navigate to="/dashboard/approver" replace />
  if (role === 'finance') return <Navigate to="/dashboard/finance" replace />

  return <Navigate to="/login" replace />
}

const AppRoutes: React.FC = () => (
  <Routes>
    <Route path="/" element={<DefaultRedirect />} />
    <Route path="/login" element={<LoginPage />} />
    <Route path="/register" element={<RegisterPage />} />
    <Route path="/activate" element={<Activate />} />

    <Route
      path="/dashboard/staff"
      element={
        <ProtectedRoute allowedRoles={["staff"]}>
          <StaffDashboard />
        </ProtectedRoute>
      }
    />

    <Route
      path="/dashboard/approver"
      element={
        <ProtectedRoute allowedRoles={["manager_1", "manager_2"]}>
          <ApproverDashboard />
        </ProtectedRoute>
      }
    />

    <Route
      path="/dashboard/finance"
      element={
        <ProtectedRoute allowedRoles={["finance"]}>
          <FinanceDashboard />
        </ProtectedRoute>
      }
    />

    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes>
)

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App