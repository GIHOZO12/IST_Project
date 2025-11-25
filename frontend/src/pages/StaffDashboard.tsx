import React, { useEffect, useState } from 'react'
import { apiRequest, API_BASE_URL } from '../api/client'
import { useAuth } from '../context/AuthContext'

interface PurchaseRequest {
  id: number
  title: string
  description: string
  amount: string
  status: string
  created_at: string
  proforma: string | null
}

interface RequestItem {
  description: string
  quantity: number
  unit_price: number
}

const StaffDashboard: React.FC = () => {
  const { username, logout } = useAuth()
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [amount, setAmount] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [requests, setRequests] = useState<PurchaseRequest[]>([])
  const [editingId, setEditingId] = useState<number | null>(null)
  const [activeTab, setActiveTab] = useState<'new' | 'list'>('new')

  const [items, setItems] = useState<RequestItem[]>([
    { description: '', quantity: 1, unit_price: 0 },
  ])
  const [proformaFile, setProformaFile] = useState<File | null>(null)
  const [uploadingReceipt, setUploadingReceipt] = useState<number | null>(null)

  const startEdit = (request: PurchaseRequest) => {
    if (request.status !== 'pending') return
    setTitle(request.title)
    setDescription(request.description)
    setAmount(request.amount)
    setEditingId(request.id)
    setActiveTab('new')
  }

  const handleItemChange = (index: number, field: keyof RequestItem, value: string) => {
    setItems((prev) => {
      const copy = [...prev]
      if (field === 'quantity' || field === 'unit_price') {
        // basic number parsing; fallback to 0
        copy[index] = { ...copy[index], [field]: value === '' ? 0 : Number(value) }
      } else {
        copy[index] = { ...copy[index], [field]: value }
      }
      return copy
    })
  }

  const addItem = () => {
    setItems((prev) => [...prev, { description: '', quantity: 1, unit_price: 0 }])
  }

  const removeItem = (index: number) => {
    setItems((prev) => (prev.length <= 1 ? prev : prev.filter((_, i) => i !== index)))
  }

  // Compute current total from items (used for display in Amount field)
  const totalAmount = items.reduce(
    (sum, item) => sum + item.quantity * item.unit_price,
    0
  )

  const fetchRequests = async () => {
    try {
      setError(null)
      const data = await apiRequest<PurchaseRequest[]>('/api/v1/Get-purchase-request/', {
        method: 'GET',
        auth: true,
      })
      setRequests(data)
    } catch (err: unknown) {
      setError(err instanceof Error?err.message : 'Failed to load requests')
    }
  }

  useEffect(() => {
    fetchRequests()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    setLoading(true)

    try {
      const payloadItems = items.map((item) => ({
        description: item.description,
        quantity: item.quantity,
        unit_price: item.unit_price,
      }))

      if (editingId) {
        const formData = new FormData()
        formData.append('title', title)
        formData.append('description', description)
        formData.append('amount', amount)
        formData.append('items', JSON.stringify(payloadItems))
        if (proformaFile) {
          formData.append('proforma', proformaFile)
        }

        await apiRequest(`/api/v1/update-purchase-request/${editingId}/`, {
          method: 'PUT',
          auth: true,
          body: formData,
          isFormData: true,
        })
        setSuccess('Purchase request updated')
      } else {
        const formData = new FormData()
        formData.append('title', title)
        formData.append('description', description)
        formData.append('amount', amount)
        formData.append('items', JSON.stringify(payloadItems))
        if (proformaFile) {
          formData.append('proforma', proformaFile)
        }

        await apiRequest('/api/v1/purchase-request/', {
          method: 'POST',
          auth: true,
          body: formData,
          isFormData: true,
        })
        setSuccess('Purchase request created')
      }

      setTitle('')
      setDescription('')
      setAmount('')
      setEditingId(null)
      setItems([{ description: '', quantity: 1, unit_price: 0 }])
      setProformaFile(null)
      fetchRequests()
    } catch (err: unknown) {
      setError(err instanceof Error?err.message : 'Failed to create request')
    } finally {
      setLoading(false)
    }
  }

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
      setError(err instanceof Error?err.message : 'Failed to download file')
    }
  }

  const handleReceiptUpload = async (requestId: number) => {
    const fileInput = document.createElement('input')
    fileInput.type = 'file'
    fileInput.accept = '.pdf,.png,.jpg,.jpeg'
    fileInput.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0]
      if (!file) return

      setUploadingReceipt(requestId)
      setError(null)

      try {
        const formData = new FormData()
        formData.append('receipt_file', file)

        const response = await apiRequest(`/api/v1/submit-receipt/${requestId}/`, {
          method: 'POST',
          auth: true,
          body: formData,
          isFormData: true,
        }) as { validation?: { validated?: boolean, discrepancies?: { message: string }[] } }

        if (response.validation?.validated) {
          setSuccess('Receipt submitted and validated successfully!')
        } else {
          setError(`Receipt submitted but has discrepancies: ${response.validation?.discrepancies?.map((d: any) => d.message).join(', ')}`)
        }
        fetchRequests()
      } catch (err: unknown) {
        setError(err instanceof Error?err.message : 'Failed to upload receipt')
      } finally {
        setUploadingReceipt(null)
      }
    }
    fileInput.click()
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 flex flex-col md:flex-row">
      <aside className="w-56 border-r border-slate-800 bg-slate-950/80 p-4 hidden md:block">
        <h2 className="text-sm font-semibold text-slate-300 mb-4">Staff Menu</h2>
        <ul className="space-y-1 text-sm">
          <li>
            <button
              onClick={() => setActiveTab('new')}
              className={`w-full text-left px-3 py-2 rounded-md transition-colors ${
                activeTab === 'new'
                  ? 'bg-emerald-600 text-white'
                  : 'text-slate-300 hover:bg-slate-800'
              }`}
            >
              New Request
            </button>
          </li>
          <li>
            <button
              onClick={() => setActiveTab('list')}
              className={`w-full text-left px-3 py-2 rounded-md transition-colors ${
                activeTab === 'list'
                  ? 'bg-emerald-600 text-white'
                  : 'text-slate-300 hover:bg-slate-800'
              }`}
            >
              My Requests
            </button>
          </li>
        </ul>
      </aside>


  
<nav className="md:hidden border-b border-slate-800 bg-slate-950/80 px-4 py-2 flex gap-2">
  <button
    onClick={() => setActiveTab('new')}
    className={`flex-1 text-xs px-3 py-2 rounded-md ${
      activeTab === 'new'
        ? 'bg-emerald-600 text-white'
        : 'text-slate-300 border border-slate-700'
    }`}
  >
    New Request
  </button>
  <button
    onClick={() => setActiveTab('list')}
    className={`flex-1 text-xs px-3 py-2 rounded-md ${
      activeTab === 'list'
        ? 'bg-emerald-600 text-white'
        : 'text-slate-300 border border-slate-700'
    }`}
  >
    My Requests
  </button>
</nav>

      <main className="flex-1 p-6">
        <header className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-semibold">Staff Dashboard</h1>
            <p className="text-xs text-slate-400">Signed in as {username ?? 'staff'}</p>
          </div>
          <button
            onClick={logout}
            className="text-xs px-3 py-1 rounded-md border border-slate-600 hover:border-red-500 hover:text-red-400"
          >
            Logout
          </button>
        </header>

        {activeTab === 'new' && (
          <div className="border border-slate-800 rounded-xl p-6 bg-slate-900/60 max-w-2xl">
            <h2 className="text-lg font-semibold mb-4">
              {editingId ? 'Edit Purchase Request' : 'New Purchase Request'}
            </h2>

          {error && (
            <div className="mb-3 rounded-md bg-red-500/10 border border-red-500/40 px-3 py-2 text-xs text-red-300">
              {error}
            </div>
          )}

          {success && (
            <div className="mb-3 rounded-md bg-emerald-500/10 border border-emerald-500/40 px-3 py-2 text-xs text-emerald-300">
              {success}
            </div>
          )}

            <form onSubmit={handleSubmit} className="space-y-3 text-sm">
            <div>
              <label className="block text-slate-200 mb-1">Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                className="w-full rounded-md bg-slate-900 border border-slate-700 px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-slate-200">Items</label>
                <button
                  type="button"
                  onClick={addItem}
                  className="text-[10px] px-2 py-1 rounded-md border border-slate-600 hover:border-emerald-500"
                >
                  Add item
                </button>
              </div>

              <div className="space-y-2">
                {items.map((item, index) => (
                  <div
                    key={index}
                    className="grid grid-cols-1 md:grid-cols-12 gap-2 items-end border border-slate-800 rounded-md p-2"
                  >
                    <div className="md:col-span-6">
                      <label className="block text-[11px] text-slate-300 mb-1">Description</label>
                      <input
                        type="text"
                        value={item.description}
                        onChange={(e) => handleItemChange(index, 'description', e.target.value)}
                        required
                        className="w-full rounded-md bg-slate-900 border border-slate-700 px-2 py-1 text-[11px] focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                      />
                    </div>
                    <div className="md:col-span-3">
                      <label className="block text-[11px] text-slate-300 mb-1">Quantity</label>
                      <input
                        type="number"
                        min="1"
                        value={item.quantity}
                        onChange={(e) => handleItemChange(index, 'quantity', e.target.value)}
                        required
                        className="w-full rounded-md bg-slate-900 border border-slate-700 px-2 py-1 text-[11px] focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                      />
                    </div>
                    <div className="md:col-span-3">
                      <label className="block text-[11px] text-slate-300 mb-1">Unit price</label>
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        value={item.unit_price}
                        onChange={(e) => handleItemChange(index, 'unit_price', e.target.value)}
                        required
                        className="w-full rounded-md bg-slate-900 border border-slate-700 px-2 py-1 text-[11px] focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                      />
                    </div>
                    <div className="md:col-span-12 flex justify-end mt-1">
                      <button
                        type="button"
                        onClick={() => removeItem(index)}
                        className="text-[10px] px-2 py-1 rounded-md border border-slate-600 hover:border-red-500 hover:text-red-400 disabled:opacity-50"
                        disabled={items.length <= 1}
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-slate-200 mb-1">Description</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                required
                className="w-full rounded-md bg-slate-900 border border-slate-700 px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                rows={3}
              />
            </div>

            <div>
              <label className="block text-slate-200 mb-1">Amount</label>
              <input
                type="number"
                min="0"
                step="0.01"
                value={totalAmount.toFixed(2)}
                readOnly
                className="w-full rounded-md bg-slate-900 border border-slate-700 px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-slate-200 mb-1">Proforma Invoice (Optional)</label>
              <input
                type="file"
                accept=".pdf,.png,.jpg,.jpeg"
                onChange={(e) => setProformaFile(e.target.files?.[0] || null)}
                className="w-full rounded-md bg-slate-900 border border-slate-700 px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              />
              {proformaFile && (
                <p className="text-[10px] text-slate-400 mt-1">Selected: {proformaFile.name}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="mt-2 inline-flex justify-center items-center rounded-md bg-emerald-600 hover:bg-emerald-500 px-3 py-2 text-xs font-medium text-white disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {loading ? 'Submitting...' : 'Submit request'}
            </button>
          </form>
          </div>
        )}

        {activeTab === 'list' && (
          <div className="border border-slate-800 rounded-xl p-6 bg-slate-900/60">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold">My Requests</h2>
              <button
                onClick={fetchRequests}
                className="text-xs px-2 py-1 rounded-md border border-slate-600 hover:border-emerald-500"
              >
                Refresh
              </button>
            </div>

            {requests.length === 0 ? (
              <p className="text-xs text-slate-400">No requests yet.</p>
            ) : (
              <ul className="space-y-2 text-xs">
                {requests.map((r) => (
                  <li
                    key={r.id}
                    className="border border-slate-800 rounded-md px-3 py-2 flex items-center justify-between gap-3"
                  >
                    <div className="flex-1">
                      <p className="font-medium text-slate-100">{r.title}</p>
                      <p className="text-slate-400 truncate max-w-xs text-[11px]">{r.description}</p>
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
                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <p className="text-emerald-400 font-semibold">${r.amount}</p>
                        <p className="text-[10px] uppercase tracking-wide text-slate-400">{r.status}</p>
                      </div>
                      <div className="flex flex-col gap-1">
                        {r.status === 'pending' && (
                          <button
                            type="button"
                            onClick={() => startEdit(r)}
                            className="text-[10px] px-2 py-1 rounded-md border border-slate-600 hover:border-emerald-500 hover:text-emerald-400"
                          >
                            Edit
                          </button>
                        )}
                        {r.status === 'approved' && (
                          <button
                            type="button"
                            onClick={() => handleReceiptUpload(r.id)}
                            disabled={uploadingReceipt === r.id}
                            className="text-[10px] px-2 py-1 rounded-md border border-slate-600 hover:border-blue-500 hover:text-blue-400 disabled:opacity-50"
                          >
                            {uploadingReceipt === r.id ? 'Uploading...' : 'Upload Receipt'}
                          </button>
                        )}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </main>
    </div>
  )
}

export default StaffDashboard
