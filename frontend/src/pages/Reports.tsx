import { useState, useEffect } from 'react'
import {
  Box,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Alert,
  Tabs,
  Tab,
  Chip,
} from '@mui/material'
import {
  reportsApi,
  productsApi,
  locationsApi,
  StockReportItem,
  LowStockItem,
  Product,
  Location,
} from '../services/api'

interface ExpiringItem {
  batch_id: number
  product_id: number
  product_name: string
  location_id: number
  location_name: string
  quantity: number
  expiry_date: string
  status: string
  days_until_expiry: number
}

export default function Reports() {
  const [activeTab, setActiveTab] = useState(0)
  const [products, setProducts] = useState<Product[]>([])
  const [locations, setLocations] = useState<Location[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Stock Report
  const [stockItems, setStockItems] = useState<StockReportItem[]>([])
  const [filterProduct, setFilterProduct] = useState<number | ''>('')
  const [filterLocation, setFilterLocation] = useState<number | ''>('')

  // Low Stock
  const [lowStockItems, setLowStockItems] = useState<LowStockItem[]>([])

  // Expiring
  const [expiringItems, setExpiringItems] = useState<ExpiringItem[]>([])
  const [expiryDays, setExpiryDays] = useState(7)

  useEffect(() => {
    loadBaseData()
  }, [])

  useEffect(() => {
    if (activeTab === 0) {
      loadStockReport()
    } else if (activeTab === 1) {
      loadLowStock()
    } else {
      loadExpiring()
    }
  }, [activeTab, filterProduct, filterLocation, expiryDays])

  const loadBaseData = async () => {
    try {
      const [productsRes, locationsRes] = await Promise.all([
        productsApi.list(),
        locationsApi.list(),
      ])
      setProducts(productsRes.data)
      setLocations(locationsRes.data)
    } catch (err) {
      console.error(err)
    }
  }

  const loadStockReport = async () => {
    try {
      setLoading(true)
      const response = await reportsApi.getStockReport({
        product_id: filterProduct || undefined,
        location_id: filterLocation || undefined,
      })
      setStockItems(response.data.items)
    } catch (err) {
      setError('Failed to load stock report')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const loadLowStock = async () => {
    try {
      setLoading(true)
      const response = await reportsApi.getLowStock()
      setLowStockItems(response.data)
    } catch (err) {
      setError('Failed to load low stock report')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const loadExpiring = async () => {
    try {
      setLoading(true)
      const response = await reportsApi.getExpiring(expiryDays)
      setExpiringItems(response.data as unknown as ExpiringItem[])
    } catch (err) {
      setError('Failed to load expiring items')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Reports
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Card sx={{ mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={(_, v) => setActiveTab(v)}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="Stock Report" />
          <Tab label="Low Stock" />
          <Tab label="Expiring Items" />
        </Tabs>
      </Card>

      {/* Stock Report Tab */}
      {activeTab === 0 && (
        <>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <FormControl size="small" sx={{ minWidth: 200 }}>
                  <InputLabel>Product</InputLabel>
                  <Select
                    value={filterProduct}
                    label="Product"
                    onChange={(e) =>
                      setFilterProduct(e.target.value as number | '')
                    }
                  >
                    <MenuItem value="">All</MenuItem>
                    {products.map((p) => (
                      <MenuItem key={p.id} value={p.id}>
                        {p.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <FormControl size="small" sx={{ minWidth: 200 }}>
                  <InputLabel>Location</InputLabel>
                  <Select
                    value={filterLocation}
                    label="Location"
                    onChange={(e) =>
                      setFilterLocation(e.target.value as number | '')
                    }
                  >
                    <MenuItem value="">All</MenuItem>
                    {locations.map((l) => (
                      <MenuItem key={l.id} value={l.id}>
                        {l.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Box>
            </CardContent>
          </Card>

          <TableContainer component={Card}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Product</TableCell>
                  <TableCell>Category</TableCell>
                  <TableCell>Location</TableCell>
                  <TableCell align="right">Total</TableCell>
                  <TableCell align="right">Sealed</TableCell>
                  <TableCell align="right">Active</TableCell>
                  <TableCell>Earliest Expiry</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={7} align="center">
                      Loading...
                    </TableCell>
                  </TableRow>
                ) : stockItems.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} align="center">
                      No stock found
                    </TableCell>
                  </TableRow>
                ) : (
                  stockItems.map((item, idx) => (
                    <TableRow key={idx}>
                      <TableCell>{item.product_name}</TableCell>
                      <TableCell>{item.category || '-'}</TableCell>
                      <TableCell>{item.location_name}</TableCell>
                      <TableCell align="right">{item.total_quantity}</TableCell>
                      <TableCell align="right">{item.sealed_quantity}</TableCell>
                      <TableCell align="right">{item.active_quantity}</TableCell>
                      <TableCell>
                        {item.earliest_expiry
                          ? new Date(item.earliest_expiry).toLocaleDateString()
                          : '-'}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </>
      )}

      {/* Low Stock Tab */}
      {activeTab === 1 && (
        <TableContainer component={Card}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Product</TableCell>
                <TableCell align="right">Current</TableCell>
                <TableCell align="right">Minimum</TableCell>
                <TableCell align="right">Deficit</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={4} align="center">
                    Loading...
                  </TableCell>
                </TableRow>
              ) : lowStockItems.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} align="center">
                    All products are adequately stocked
                  </TableCell>
                </TableRow>
              ) : (
                lowStockItems.map((item) => (
                  <TableRow key={item.product_id}>
                    <TableCell>{item.product_name}</TableCell>
                    <TableCell align="right">{item.current_quantity}</TableCell>
                    <TableCell align="right">{item.min_threshold}</TableCell>
                    <TableCell align="right">
                      <Chip
                        label={`-${item.deficit}`}
                        color="warning"
                        size="small"
                      />
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Expiring Tab */}
      {activeTab === 2 && (
        <>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <FormControl size="small" sx={{ minWidth: 150 }}>
                <InputLabel>Days</InputLabel>
                <Select
                  value={expiryDays}
                  label="Days"
                  onChange={(e) => setExpiryDays(e.target.value as number)}
                >
                  <MenuItem value={7}>7 days</MenuItem>
                  <MenuItem value={14}>14 days</MenuItem>
                  <MenuItem value={30}>30 days</MenuItem>
                  <MenuItem value={90}>90 days</MenuItem>
                </Select>
              </FormControl>
            </CardContent>
          </Card>

          <TableContainer component={Card}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Product</TableCell>
                  <TableCell>Location</TableCell>
                  <TableCell align="right">Quantity</TableCell>
                  <TableCell>Expiry Date</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={5} align="center">
                      Loading...
                    </TableCell>
                  </TableRow>
                ) : expiringItems.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} align="center">
                      No items expiring within {expiryDays} days
                    </TableCell>
                  </TableRow>
                ) : (
                  expiringItems.map((item) => (
                    <TableRow key={item.batch_id}>
                      <TableCell>{item.product_name}</TableCell>
                      <TableCell>{item.location_name}</TableCell>
                      <TableCell align="right">{item.quantity}</TableCell>
                      <TableCell>
                        {new Date(item.expiry_date).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={
                            item.days_until_expiry <= 0
                              ? 'Expired'
                              : `${item.days_until_expiry} days`
                          }
                          color={
                            item.days_until_expiry <= 0
                              ? 'error'
                              : item.days_until_expiry <= 3
                              ? 'warning'
                              : 'default'
                          }
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </>
      )}
    </Box>
  )
}
