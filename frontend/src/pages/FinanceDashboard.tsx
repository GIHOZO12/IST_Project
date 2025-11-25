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
  created_by: string
  created_at: string
  purchase_order: {
    id: number
    po_number: string
    vendor: string
    total_amount: string
    po_file: string | null
  } | null
  approvals?: Approval[]
  items?: Array<{
    description: string
    quantity: number
    unit_price: string
  }>
  proforma?: string
}

const FinanceDashboard: React.FC = () => {
  const { username, logout } = useAuth()
  const [requests, setRequests] = useState<PurchaseRequest[]>([])
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'pending' | 'approved'>('pending')

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
      setError(err instanceof Error ? err.message : 'Failed to download file')
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
      setError(err instanceof Error ? err.message : 'Failed to load requests')
    }
  }

  useEffect(() => {
    fetchRequests()
  }, [])

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 flex flex-col md:flex-row">
      <aside className="w-56 border-r border-slate-800 bg-slate-950/80 p-4 hidden md:block">
        <h2 className="text-sm font-semibold text-slate-300 mb-4">Finance Menu</h2>
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
              Pending Approvals
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
        </ul>
      </aside>




<nav  className='md:hidden border-b  bg-slate-950/80 border-slate-800 px-4 py-2 flex gap-4'>



<button className={`text-slate-300 hover:bg-slate-800 ${activeTab === 'pending' ? 'bg-emerald-600 text-white' : ''}`} onClick={() => setActiveTab('pending')}>Pending Approvals</button>


<button className={`text-slate-300 hover:bg-slate-800 ${activeTab === 'approved' ? 'bg-emerald-600 text-white' : ''}`} onClick={() => setActiveTab('approved')}>Approved Requests</button>






</nav>
      <main className="flex-1 p-6">
        <header className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-semibold">Finance Dashboard</h1>
            <p className="text-xs text-slate-400">Signed in as {username ?? 'finance'}</p>
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
              {activeTab === 'pending' ? 'Pending Approvals' : 'Approved Requests'}
            </h2>
            <button
              onClick={fetchRequests}
              className="text-xs px-2 py-1 rounded-md border border-slate-600 hover:border-emerald-500"
            >
              {/* Refresh */}
            </button>
          </div>

          {error && (
            <div className="mb-3 rounded-md bg-red-500/10 border border-red-500/40 px-3 py-2 text-xs text-red-300">
              {error}
            </div>
          )}

          {requests
            .filter((r) => {
              if (activeTab === 'approved') return r.status === 'approved'

              // Pending tab: only show requests that are still pending
              // AND already have both level 1 and level 2 approved
              if (r.status !== 'pending' || !r.approvals) return false
              const hasLevel1 = r.approvals.some((a) => a.approved && a.level === 1)
              const hasLevel2 = r.approvals.some((a) => a.approved && a.level === 2)
              return hasLevel1 && hasLevel2
            })
            .length === 0 ? (
            <p className="text-xs text-slate-400">
              {activeTab === 'pending' ? 'No pending approvals.' : 'No approved requests yet.'}
            </p>
          ) : (
            <ul className="space-y-2 text-xs">
              {requests
                .filter((r) => {
                  if (activeTab === 'approved') return r.status === 'approved'

                  if (r.status !== 'pending' || !r.approvals) return false
                  const hasLevel1 = r.approvals.some((a) => a.approved && a.level === 1)
                  const hasLevel2 = r.approvals.some((a) => a.approved && a.level === 2)
                  return hasLevel1 && hasLevel2
                })
                .map((r) => (
                  <li
                    key={r.id}
                    className="border border-slate-800 rounded-md px-3 py-2 flex items-center justify-between gap-3"
                  >
                    <div className="flex-1">
                      <p className="font-medium text-slate-100">{r.title}</p>
                      <p className="text-slate-400 max-w-xs break-words text-[11px]">{r.description}</p>
                      <div className="mt-2 space-y-1">
                        <p className="text-emerald-400 font-semibold">${r.amount}</p>
                        <p className="text-[10px] text-slate-500">Request #{r.id} by {r.created_by}</p>
                        {r.items && r.items.length > 0 && (
                          <p className="text-[10px] text-slate-500">{r.items.length} item(s)</p>
                        )}
                        {r.proforma && (
                          <button
                            type="button"
                            onClick={() => {
                              const filename = r.proforma?.split('/').pop() || 'proforma.pdf'
                              handleFileDownload(`${API_BASE_URL}/api/v1/download/proforma/${r.id}/`, filename)
                            }}
                            className="inline-flex items-center text-[10px] text-blue-400 hover:text-blue-300 mt-1"
                          >
                            📎 Download Proforma
                          </button>
                        )}
                      </div>
                      {r.approvals && r.approvals.length > 0 && (
                        <ul className="mt-2 text-[10px] text-slate-400 space-y-0.5">
                          {r.approvals
                            .filter((a) => a.approved)
                            .map((a) => (
                              <li key={a.id}>
                                ✓ Level {a.level} approved by {a.approver}
                              </li>
                            ))}
                        </ul>
                      )}
                    </div>
                    {activeTab === 'approved' ? (
                      <div className="text-right text-[10px] text-slate-400 space-y-2 min-w-[140px]">
                        {r.purchase_order ? (
                          <>
                            <div>
                              <p className="uppercase tracking-wide text-slate-500">PO Number:</p>
                              <p className="text-emerald-400 font-semibold">{r.purchase_order.po_number}</p>
                            </div>
                            {r.purchase_order.vendor && (
                              <div>
                                <p className="text-slate-500">Vendor:</p>
                                <p className="text-slate-300">{r.purchase_order.vendor}</p>
                              </div>
                            )}
                            {r.purchase_order?.po_file && (
                              <button
                                type="button"
                                onClick={() => {
                                  handleFileDownload(
                                    `${API_BASE_URL}/api/v1/download/po/${r.purchase_order!.id}/`,
                                    `PO-${r.purchase_order!.po_number}.pdf`
                                  )
                                }}
                                className="mt-2 inline-flex items-center justify-center rounded-md bg-emerald-600 hover:bg-emerald-500 px-3 py-1.5 text-[10px] text-white font-medium"
                              >
                                📄 Download PO PDF
                              </button>
                            )}
                          </>
                        ) : (
                          <p className="text-slate-500">PO not generated</p>
                        )}
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={async () => {
                            // Ask finance to add an optional comment before approving & generating PO
                            const comment = window.prompt('Add comments for finance approval (optional):', '') ?? ''

                            try {
                              setError(null)
                              await apiRequest(`/api/v1/approve-request/${r.id}/`, {
                                method: 'PATCH',
                                auth: true,
                                body: { comments: comment },
                              })
                              fetchRequests()
                            } catch (err: unknown) {
                              setError(err instanceof Error ? err.message : 'Approval failed')
                            }
                          }}
                          className="text-xs px-3 py-1 rounded-md bg-emerald-600 hover:bg-emerald-500 text-white"
                        >
                          Approve & Generate PO
                        </button>
                      </div>
                    )}
                  </li>
                ))}
            </ul>
          )}
        </div>
      </main>
    </div>
  )
}

export default FinanceDashboard
