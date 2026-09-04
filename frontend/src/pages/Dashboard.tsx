import { useState, useEffect } from 'react'
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Alert,
  List,
  ListItem,
  ListItemText,
  Chip,
  Button,
  TextField,
} from '@mui/material'
import {
  Inventory as InventoryIcon,
  Warning as WarningIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material'
import { reportsApi, aiApi, StockReport, LowStockItem } from '../services/api'

interface ExpiringItem {
  batch_id: number
  product_name: string
  location_name: string
  quantity: number
  expiry_date: string
  days_until_expiry: number
}

export default function Dashboard() {
  const [stockReport, setStockReport] = useState<StockReport | null>(null)
  const [lowStock, setLowStock] = useState<LowStockItem[]>([])
  const [expiring, setExpiring] = useState<ExpiringItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [aiInput, setAiInput] = useState('')
  const [aiResponse, setAiResponse] = useState('')
  const [aiLoading, setAiLoading] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [stockRes, lowStockRes, expiringRes] = await Promise.all([
        reportsApi.getStockReport(),
        reportsApi.getLowStock(),
        reportsApi.getExpiring(7),
      ])
      setStockReport(stockRes.data)
      setLowStock(lowStockRes.data)
      setExpiring(expiringRes.data as unknown as ExpiringItem[])
    } catch (err) {
      setError('Failed to load dashboard data')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const askAI = async () => {
    if (!aiInput.trim()) return

    try {
      setAiLoading(true)
      setAiResponse('')

      const response = await aiApi.ask(aiInput)

      setAiResponse(response.data.response)
    } catch (err) {
      console.error(err)
      setAiResponse('Failed to get a response from the AI assistant.')
    } finally {
      setAiLoading(false)
    }
  }

  if (loading) {
    return <Typography>Loading...</Typography>
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      <Grid container spacing={3}>
        {/* Summary Cards */}
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <InventoryIcon color="primary" />
                <Typography variant="h6">Total Items</Typography>
              </Box>
              <Typography variant="h3" sx={{ mt: 2 }}>
                {stockReport?.total_items || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                across {stockReport?.total_products || 0} products
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <WarningIcon color="warning" />
                <Typography variant="h6">Low Stock</Typography>
              </Box>
              <Typography variant="h3" sx={{ mt: 2 }}>
                {lowStock.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                products below threshold
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <ScheduleIcon color="error" />
                <Typography variant="h6">Expiring Soon</Typography>
              </Box>
              <Typography variant="h3" sx={{ mt: 2 }}>
                {expiring.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                items expiring in 7 days
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Low Stock Alert */}
        {lowStock.length > 0 && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Low Stock Alerts
                </Typography>
                <List dense>
                  {lowStock.slice(0, 5).map((item) => (
                    <ListItem key={item.product_id}>
                      <ListItemText
                        primary={item.product_name}
                        secondary={`${item.current_quantity} / ${item.min_threshold} (need ${item.deficit} more)`}
                      />
                      <Chip
                        label="Low"
                        color="warning"
                        size="small"
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Expiring Items */}
        {expiring.length > 0 && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Expiring Soon
                </Typography>
                <List dense>
                  {expiring.slice(0, 5).map((item) => (
                    <ListItem key={item.batch_id}>
                      <ListItemText
                        primary={item.product_name}
                        secondary={`${item.quantity}x at ${item.location_name}`}
                      />
                      <Chip
                        label={
                          item.days_until_expiry <= 0
                            ? 'Expired'
                            : `${item.days_until_expiry}d`
                        }
                        color={item.days_until_expiry <= 0 ? 'error' : 'warning'}
                        size="small"
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
                )}
      </Grid>

      {/* AI Assistant */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            AI Assistant
          </Typography>

          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Ask questions or give commands about your inventory.
          </Typography>

                    <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              fullWidth
              placeholder="Ask a question about your inventory"
              value={aiInput}
              onChange={(e) => setAiInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault()
                  askAI()
                }
              }}
            />

            <Button
              variant="contained"
              disabled={!aiInput.trim() || aiLoading}
              onClick={askAI}
            >
              {aiLoading ? 'Asking...' : 'Ask'}
            </Button>
          </Box>

          {aiResponse && (
            <Alert severity="info" sx={{ mt: 2 }}>
              {aiResponse}
            </Alert>
          )}
                  </CardContent>
      </Card>
    </Box>
  )
}