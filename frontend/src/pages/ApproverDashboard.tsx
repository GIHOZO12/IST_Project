import React, { useEffect, useState } from 'react'
import { apiRequest, API_BASE_URL } from '../api/client'
import { useAuth } from '../context/AuthContext'

interface Approval {
  id: number
  approver: string
  level: number
  approved: boolean
  comments: string | null
  created_at: string
}

interface PurchaseRequest {
  id: number
  title: string
  description: string
  amount: string
  status: string
  proforma: string | null
  approvals?: Approval[]
}

const ApproverDashboard: React.FC = () => {
  const { username, role, logout } = useAuth()
  const [requests, setRequests] = useState<PurchaseRequest[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'pending' | 'approved' | 'rejected'>('pending')

  const handleFileDownload = async (url: string, filename: string) => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (!response.ok) {
        throw new Error('Failed to download file')
      }
      
      const blob = await response.blob()
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)
    } catch (err: unknown) {
      setError(err instanceof Error ?err.message : 'Failed to download file');
    }
  }

  const fetchRequests = async () => {
    try {
      setError(null)
      const data = await apiRequest<PurchaseRequest[]>('/api/v1/Get-purchase-request/', {
        method: 'GET',
        auth: true,
      })
      setRequests(data)
    } catch (err: unknown) {
      setError(err  instanceof Error?err.message : 'Failed to load requests')
    }
  }

  useEffect(() => {
    fetchRequests()
  }, [])

  const handleAction = async (id: number, action: 'approve' | 'reject') => {
    // Ask the approver to add an optional comment before submitting
    const comment = window.prompt('Add comments (optional):', '') ?? ''

    setLoading(true)
    setError(null)
    try {
      const path = action === 'approve' ? `/api/v1/approve-request/${id}/` : `/api/v1/reject-request/${id}/`
      await apiRequest(path, {
        method: 'PATCH',
        auth: true,
        body: {
          comments: comment,
        },
      })
      fetchRequests()
    } catch (err: unknown) {
      setError(err instanceof Error?err.message : 'Action failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 flex flex-col md:flex-row">
      <aside className="w-56 border-r border-slate-800 bg-slate-950/80 p-4 hidden md:block">
        <h2 className="text-sm font-semibold text-slate-300 mb-4">Approver Menu</h2>
        <ul className="space-y-1 text-sm">
          <li>
            <button
              onClick={() => setActiveTab('pending')}
              className={`w-full text-left px-3 py-2 rounded-md transition-colors ${
                activeTab === 'pending'
                  ? 'bg-emerald-600 text-white'
                  : 'text-slate-300 hover:bg-slate-800'
              }`}
            >
              Pending Requests
            </button>
          </li>
          <li>
            <button
              onClick={() => setActiveTab('approved')}
              className={`w-full text-left px-3 py-2 rounded-md transition-colors ${
                activeTab === 'approved'
                  ? 'bg-emerald-600 text-white'
                  : 'text-slate-300 hover:bg-slate-800'
              }`}
            >
              Approved Requests
            </button>
          </li>
          <li>
            <button
              onClick={() => setActiveTab('rejected')}
              className={`w-full text-left px-3 py-2 rounded-md transition-colors ${
                activeTab === 'rejected'
                  ? 'bg-emerald-600 text-white'
                  : 'text-slate-300 hover:bg-slate-800'
              }`}
            >
              Rejected Requests
            </button>
          </li>
        </ul>
      </aside>


<nav  className='md:hidden border-b border-slate-800 bg-slate-950/80 px-4 py-2 flex gap-2'>

<button onClick={() => setActiveTab('pending')} className={`text-slate-300 hover:bg-slate-800 ${activeTab === 'pending' ? 'bg-emerald-600 text-white' : ''}`}>Pending Requests</button>
<button onClick={() => setActiveTab('approved')} className={`text-slate-300 hover:bg-slate-800 ${activeTab === 'approved' ? 'bg-emerald-600 text-white' : ''}`}>Approved Requests</button>
<button onClick={() => setActiveTab('rejected')} className={`text-slate-300 hover:bg-slate-800 ${activeTab === 'rejected' ? 'bg-emerald-600 text-white' : ''}`}>Rejected Requests</button>



</nav>





      <main className="flex-1 p-6">
        <header className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-semibold">Approver Dashboard</h1>
            <p className="text-xs text-slate-400">
              Signed in as {username ?? 'approver'} ({role})
            </p>
          </div>
          <button
            onClick={logout}
            className="text-xs px-3 py-1 rounded-md border border-slate-600 hover:border-red-500 hover:text-red-400"
          >
            Logout
          </button>
        </header>

        <div className="border border-slate-800 rounded-xl p-6 bg-slate-900/60">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold">
              {activeTab === 'pending'
                ? 'Pending Requests'
                : activeTab === 'approved'
                ? 'Approved Requests'
                : 'Rejected Requests'}
            </h2>
            <button
              onClick={fetchRequests}
              className="text-xs px-2 py-1 rounded-md border border-slate-600 hover:border-emerald-500"
            >
              Refresh
            </button>
          </div>

          {error && (
            <div className="mb-3 rounded-md bg-red-500/10 border border-red-500/40 px-3 py-2 text-xs text-red-300">
              {error}
            </div>
          )}

          {requests
            .filter((r) =>
              activeTab === 'pending'
                ? r.status === 'pending'
                : activeTab === 'approved'
                ? r.status === 'approved'
                : r.status === 'rejected'
            )
            .length === 0 ? (
            <p className="text-xs text-slate-400">
              {activeTab === 'pending'
                ? 'No pending requests.'
                : activeTab === 'approved'
                ? 'No approved requests.'
                : 'No rejected requests.'}
            </p>
          ) : (
            <ul className="space-y-2 text-xs">
              {requests
                .filter((r) =>
                  activeTab === 'pending'
                    ? r.status === 'pending'
                    : activeTab === 'approved'
                    ? r.status === 'approved'
                    : r.status === 'rejected'
                )
                .map((r) => {
                  const userApproval = r.approvals?.find(
                    (a) => a.approver === username
                  )

                  return (
                    <li
                      key={r.id}
                      className="border border-slate-800 rounded-md px-3 py-2 flex items-center justify-between gap-3"
                    >
                      <div>
                        <p className="font-medium text-slate-100">{r.title}</p>
                        <p className="text-slate-400 max-w-xs break-words">{r.description}</p>
                        <p className="text-emerald-400 font-semibold mt-1">${r.amount}</p>
                        {r.proforma && (
                          <button
                            type="button"
                            onClick={() => {
                              const filename = r.proforma?.split('/').pop() || 'proforma.pdf'
                              handleFileDownload(`${API_BASE_URL}/api/v1/download/proforma/${r.id}/`, filename)
                            }}
                            className="mt-1 inline-flex items-center text-[10px] text-blue-400 hover:text-blue-300"
                          >
                            📎 Download Proforma
                          </button>
                        )}
                      </div>
                      {activeTab === 'pending' && (
                        <div className="flex flex-col items-end gap-1 text-[11px]">
                          {userApproval ? (
                            <span className="text-slate-400">
                              {userApproval.approved
                                ? 'You have approved this request.'
                                : 'You have rejected this request.'}
                            </span>
                          ) : (
                            <>
                              <button
                                disabled={loading}
                                onClick={() => handleAction(r.id, 'approve')}
                                className="text-xs px-3 py-1 rounded-md bg-emerald-600 hover:bg-emerald-500 text-white disabled:opacity-60"
                              >
                                Approve
                              </button>
                              <button
                                disabled={loading}
                                onClick={() => handleAction(r.id, 'reject')}
                                className="text-xs px-3 py-1 rounded-md bg-red-600 hover:bg-red-500 text-white disabled:opacity-60"
                              >
                                Reject
                              </button>
                            </>
                          )}
                        </div>
                      )}
                    </li>
                  )
                })}
            </ul>
          )}
        </div>
      </main>
    </div>
  )
}

export default ApproverDashboard
