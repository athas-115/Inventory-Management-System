import axios from 'axios'

const API_BASE_URL = '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Types
export interface User {
  id: number
  github_id: number
  username: string
  email: string | null
  avatar_url: string | null
  display_name: string | null
  is_active: boolean
  is_admin: boolean
  created_at: string
  last_login: string | null
}

export interface Product {
  id: number
  name: string
  description: string | null
  category: string | null
  brand: string | null
  unit: string
  barcode: string | null
  min_threshold: number
  created_at: string
  updated_at: string
}

export interface Location {
  id: number
  name: string
  description: string | null
  created_at: string
}

export interface InventoryBatch {
  id: number
  product_id: number
  location_id: number
  quantity: number
  original_quantity: number
  status: 'SEALED' | 'ACTIVE' | 'DEPLETED'
  expiry_date: string | null
  purchase_date: string | null
  opened_date: string | null
  notes: string | null
  purchase_price: number | null
  created_at: string
  updated_at: string
  product?: Product
  location?: Location
}

export interface StockReportItem {
  product_id: number
  product_name: string
  category: string | null
  location_id: number
  location_name: string
  total_quantity: number
  sealed_quantity: number
  active_quantity: number
  earliest_expiry: string | null
  batch_count: number
}

export interface StockReport {
  items: StockReportItem[]
  total_products: number
  total_items: number
  low_stock_count: number
}

export interface LowStockItem {
  product_id: number
  product_name: string
  current_quantity: number
  min_threshold: number
  deficit: number
}

// Auth API
export const authApi = {
  getMe: () => api.get<User>('/auth/me'),
  generateApiKey: () => api.post<{ api_key: string }>('/auth/api-key'),
  revokeApiKey: () => api.delete('/auth/api-key'),
}

// Products API
export const productsApi = {
  list: (params?: { search?: string; category?: string }) =>
    api.get<Product[]>('/products', { params }),
  get: (id: number) => api.get<Product>(`/products/${id}`),
  create: (data: Partial<Product>) => api.post<Product>('/products', data),
  update: (id: number, data: Partial<Product>) =>
    api.put<Product>(`/products/${id}`, data),
  delete: (id: number) => api.delete(`/products/${id}`),
  getCategories: () => api.get<string[]>('/products/categories'),
}

// Locations API
export const locationsApi = {
  list: () => api.get<Location[]>('/locations'),
  get: (id: number) => api.get<Location>(`/locations/${id}`),
  create: (data: Partial<Location>) => api.post<Location>('/locations', data),
  update: (id: number, data: Partial<Location>) =>
    api.put<Location>(`/locations/${id}`, data),
  delete: (id: number) => api.delete(`/locations/${id}`),
}

// Inventory API
export const inventoryApi = {
  list: (params?: {
    product_id?: number
    location_id?: number
    status?: string
    include_depleted?: boolean
  }) => api.get<InventoryBatch[]>('/inventory', { params }),
  get: (id: number) => api.get<InventoryBatch>(`/inventory/${id}`),
  add: (data: {
    product_id: number
    location_id: number
    quantity: number
    expiry_date?: string
    purchase_date?: string
    notes?: string
    purchase_price?: number
  }) => api.post<InventoryBatch>('/inventory', data),
  update: (id: number, data: Partial<InventoryBatch>) =>
    api.put<InventoryBatch>(`/inventory/${id}`, data),
  delete: (id: number) => api.delete(`/inventory/${id}`),
  consume: (data: {
    batch_id: number
    quantity: number
    action: 'DEPLETE' | 'OPEN'
    target_location_id?: number
    notes?: string
  }) => api.post<InventoryBatch>('/inventory/consume', data),
  move: (data: {
    batch_id: number
    to_location_id: number
    quantity?: number
    notes?: string
  }) => api.post<InventoryBatch>('/inventory/move', data),
}

// Reports API
export const reportsApi = {
  getStockReport: (params?: {
    product_id?: number
    location_id?: number
    category?: string
    expiring_before?: string
  }) => api.get<StockReport>('/reports/stock', { params }),
  getLowStock: () => api.get<LowStockItem[]>('/reports/low-stock'),
  getExpiring: (days?: number) =>
    api.get<InventoryBatch[]>('/reports/expiring', { params: { days } }),
}

export default api
export const aiApi = {
  ask: (message: string) =>
    api.post('/ai/ask', { message }),
}