import { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
  Alert,
  Tabs,
  Tab,
} from '@mui/material'
import {
  Add as AddIcon,
  Remove as RemoveIcon,
  SwapHoriz as MoveIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material'
import { DatePicker } from '@mui/x-date-pickers/DatePicker'
import {
  inventoryApi,
  productsApi,
  locationsApi,
  InventoryBatch,
  Product,
  Location,
} from '../services/api'

export default function Inventory() {
  const [batches, setBatches] = useState<InventoryBatch[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [locations, setLocations] = useState<Location[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filters
  const [filterProduct, setFilterProduct] = useState<number | ''>('')
  const [filterLocation, setFilterLocation] = useState<number | ''>('')
  const [filterStatus, setFilterStatus] = useState<string>('')

  // Add Dialog
  const [addDialogOpen, setAddDialogOpen] = useState(false)
  const [addForm, setAddForm] = useState({
    product_id: 0,
    location_id: 0,
    quantity: 1,
    expiry_date: null as Date | null,
    purchase_date: null as Date | null,
    notes: '',
    purchase_price: '',
  })

  // Consume Dialog
  const [consumeDialogOpen, setConsumeDialogOpen] = useState(false)
  const [consumeBatch, setConsumeBatch] = useState<InventoryBatch | null>(null)
  const [consumeForm, setConsumeForm] = useState({
    quantity: 1,
    action: 'DEPLETE' as 'DEPLETE' | 'OPEN',
    target_location_id: 0,
    notes: '',
  })

  // Move Dialog
  const [moveDialogOpen, setMoveDialogOpen] = useState(false)
  const [moveBatch, setMoveBatch] = useState<InventoryBatch | null>(null)
  const [moveForm, setMoveForm] = useState({
    to_location_id: 0,
    quantity: '',
    notes: '',
  })

  useEffect(() => {
    loadData()
  }, [])

  useEffect(() => {
    loadBatches()
  }, [filterProduct, filterLocation, filterStatus])

  const loadData = async () => {
    try {
      const [productsRes, locationsRes] = await Promise.all([
        productsApi.list(),
        locationsApi.list(),
      ])
      setProducts(productsRes.data)
      setLocations(locationsRes.data)
    } catch (err) {
      setError('Failed to load data')
      console.error(err)
    }
  }

  const loadBatches = async () => {
    try {
      setLoading(true)
      const response = await inventoryApi.list({
        product_id: filterProduct || undefined,
        location_id: filterLocation || undefined,
        status: filterStatus || undefined,
      })
      setBatches(response.data)
    } catch (err) {
      setError('Failed to load inventory')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleAddSubmit = async () => {
    try {
      await inventoryApi.add({
        product_id: addForm.product_id,
        location_id: addForm.location_id,
        quantity: addForm.quantity,
        expiry_date: addForm.expiry_date?.toISOString().split('T')[0],
        purchase_date: addForm.purchase_date?.toISOString().split('T')[0],
        notes: addForm.notes || undefined,
        purchase_price: addForm.purchase_price
          ? parseFloat(addForm.purchase_price)
          : undefined,
      })
      setAddDialogOpen(false)
      setAddForm({
        product_id: 0,
        location_id: 0,
        quantity: 1,
        expiry_date: null,
        purchase_date: null,
        notes: '',
        purchase_price: '',
      })
      loadBatches()
    } catch (err) {
      setError('Failed to add inventory')
      console.error(err)
    }
  }

  const handleConsumeOpen = (batch: InventoryBatch) => {
    setConsumeBatch(batch)
    setConsumeForm({
      quantity: 1,
      action: 'DEPLETE',
      target_location_id: batch.location_id,
      notes: '',
    })
    setConsumeDialogOpen(true)
  }

  const handleConsumeSubmit = async () => {
    if (!consumeBatch) return
    try {
      await inventoryApi.consume({
        batch_id: consumeBatch.id,
        quantity: consumeForm.quantity,
        action: consumeForm.action,
        target_location_id:
          consumeForm.action === 'OPEN'
            ? consumeForm.target_location_id
            : undefined,
        notes: consumeForm.notes || undefined,
      })
      setConsumeDialogOpen(false)
      setConsumeBatch(null)
      loadBatches()
    } catch (err) {
      setError('Failed to consume inventory')
      console.error(err)
    }
  }

  const handleMoveOpen = (batch: InventoryBatch) => {
    setMoveBatch(batch)
    setMoveForm({
      to_location_id: 0,
      quantity: '',
      notes: '',
    })
    setMoveDialogOpen(true)
  }

  const handleMoveSubmit = async () => {
    if (!moveBatch) return
    try {
      await inventoryApi.move({
        batch_id: moveBatch.id,
        to_location_id: moveForm.to_location_id,
        quantity: moveForm.quantity ? parseInt(moveForm.quantity) : undefined,
        notes: moveForm.notes || undefined,
      })
      setMoveDialogOpen(false)
      setMoveBatch(null)
      loadBatches()
    } catch (err) {
      setError('Failed to move inventory')
      console.error(err)
    }
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this batch?')) {
      return
    }
    try {
      await inventoryApi.delete(id)
      loadBatches()
    } catch (err) {
      setError('Failed to delete batch')
      console.error(err)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'SEALED':
        return 'primary'
      case 'ACTIVE':
        return 'success'
      case 'DEPLETED':
        return 'default'
      default:
        return 'default'
    }
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">Inventory</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setAddDialogOpen(true)}
        >
          Add Inventory
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <FormControl size="small" sx={{ minWidth: 200 }}>
              <InputLabel>Product</InputLabel>
              <Select
                value={filterProduct}
                label="Product"
                onChange={(e) => setFilterProduct(e.target.value as number | '')}
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
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Status</InputLabel>
              <Select
                value={filterStatus}
                label="Status"
                onChange={(e) => setFilterStatus(e.target.value)}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="SEALED">Sealed</MenuItem>
                <MenuItem value="ACTIVE">Active</MenuItem>
                <MenuItem value="DEPLETED">Depleted</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </CardContent>
      </Card>

      {/* Inventory Table */}
      <TableContainer component={Card}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Product</TableCell>
              <TableCell>Location</TableCell>
              <TableCell>Quantity</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Expiry</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  Loading...
                </TableCell>
              </TableRow>
            ) : batches.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  No inventory found
                </TableCell>
              </TableRow>
            ) : (
              batches.map((batch) => (
                <TableRow key={batch.id}>
                  <TableCell>{batch.product?.name || batch.product_id}</TableCell>
                  <TableCell>
                    {batch.location?.name || batch.location_id}
                  </TableCell>
                  <TableCell>{batch.quantity}</TableCell>
                  <TableCell>
                    <Chip
                      label={batch.status}
                      color={getStatusColor(batch.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {batch.expiry_date
                      ? new Date(batch.expiry_date).toLocaleDateString()
                      : '-'}
                  </TableCell>
                  <TableCell align="right">
                    {batch.status !== 'DEPLETED' && (
                      <>
                        <IconButton
                          onClick={() => handleConsumeOpen(batch)}
                          title="Consume"
                        >
                          <RemoveIcon />
                        </IconButton>
                        <IconButton
                          onClick={() => handleMoveOpen(batch)}
                          title="Move"
                        >
                          <MoveIcon />
                        </IconButton>
                      </>
                    )}
                    <IconButton
                      onClick={() => handleDelete(batch.id)}
                      title="Delete"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Add Dialog */}
      <Dialog
        open={addDialogOpen}
        onClose={() => setAddDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Add Inventory</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <FormControl fullWidth required>
              <InputLabel>Product</InputLabel>
              <Select
                value={addForm.product_id || ''}
                label="Product"
                onChange={(e) =>
                  setAddForm({ ...addForm, product_id: e.target.value as number })
                }
              >
                {products.map((p) => (
                  <MenuItem key={p.id} value={p.id}>
                    {p.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl fullWidth required>
              <InputLabel>Location</InputLabel>
              <Select
                value={addForm.location_id || ''}
                label="Location"
                onChange={(e) =>
                  setAddForm({ ...addForm, location_id: e.target.value as number })
                }
              >
                {locations.map((l) => (
                  <MenuItem key={l.id} value={l.id}>
                    {l.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              label="Quantity"
              type="number"
              value={addForm.quantity}
              onChange={(e) =>
                setAddForm({ ...addForm, quantity: parseInt(e.target.value) || 1 })
              }
              inputProps={{ min: 1 }}
              required
              fullWidth
            />
            <DatePicker
              label="Expiry Date"
              value={addForm.expiry_date}
              onChange={(date) => setAddForm({ ...addForm, expiry_date: date })}
              slotProps={{ textField: { fullWidth: true } }}
            />
            <DatePicker
              label="Purchase Date"
              value={addForm.purchase_date}
              onChange={(date) =>
                setAddForm({ ...addForm, purchase_date: date })
              }
              slotProps={{ textField: { fullWidth: true } }}
            />
            <TextField
              label="Purchase Price"
              type="number"
              value={addForm.purchase_price}
              onChange={(e) =>
                setAddForm({ ...addForm, purchase_price: e.target.value })
              }
              inputProps={{ min: 0, step: 0.01 }}
              fullWidth
            />
            <TextField
              label="Notes"
              value={addForm.notes}
              onChange={(e) => setAddForm({ ...addForm, notes: e.target.value })}
              multiline
              rows={2}
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleAddSubmit}
            variant="contained"
            disabled={!addForm.product_id || !addForm.location_id}
          >
            Add
          </Button>
        </DialogActions>
      </Dialog>

      {/* Consume Dialog */}
      <Dialog
        open={consumeDialogOpen}
        onClose={() => setConsumeDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Consume Inventory</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <Typography variant="body2" color="text.secondary">
              {consumeBatch?.product?.name} - {consumeBatch?.quantity} available
            </Typography>
            <Tabs
              value={consumeForm.action}
              onChange={(_, v) => setConsumeForm({ ...consumeForm, action: v })}
            >
              <Tab value="DEPLETE" label="Deplete" />
              <Tab value="OPEN" label="Open" />
            </Tabs>
            <TextField
              label="Quantity"
              type="number"
              value={consumeForm.quantity}
              onChange={(e) =>
                setConsumeForm({
                  ...consumeForm,
                  quantity: parseInt(e.target.value) || 1,
                })
              }
              inputProps={{ min: 1, max: consumeBatch?.quantity }}
              required
              fullWidth
            />
            {consumeForm.action === 'OPEN' && (
              <FormControl fullWidth>
                <InputLabel>Target Location</InputLabel>
                <Select
                  value={consumeForm.target_location_id || ''}
                  label="Target Location"
                  onChange={(e) =>
                    setConsumeForm({
                      ...consumeForm,
                      target_location_id: e.target.value as number,
                    })
                  }
                >
                  {locations.map((l) => (
                    <MenuItem key={l.id} value={l.id}>
                      {l.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
            <TextField
              label="Notes"
              value={consumeForm.notes}
              onChange={(e) =>
                setConsumeForm({ ...consumeForm, notes: e.target.value })
              }
              multiline
              rows={2}
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConsumeDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleConsumeSubmit} variant="contained">
            Consume
          </Button>
        </DialogActions>
      </Dialog>

      {/* Move Dialog */}
      <Dialog
        open={moveDialogOpen}
        onClose={() => setMoveDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Move Inventory</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <Typography variant="body2" color="text.secondary">
              {moveBatch?.product?.name} - {moveBatch?.quantity} at{' '}
              {moveBatch?.location?.name}
            </Typography>
            <FormControl fullWidth required>
              <InputLabel>To Location</InputLabel>
              <Select
                value={moveForm.to_location_id || ''}
                label="To Location"
                onChange={(e) =>
                  setMoveForm({
                    ...moveForm,
                    to_location_id: e.target.value as number,
                  })
                }
              >
                {locations
                  .filter((l) => l.id !== moveBatch?.location_id)
                  .map((l) => (
                    <MenuItem key={l.id} value={l.id}>
                      {l.name}
                    </MenuItem>
                  ))}
              </Select>
            </FormControl>
            <TextField
              label="Quantity (leave empty for all)"
              type="number"
              value={moveForm.quantity}
              onChange={(e) =>
                setMoveForm({ ...moveForm, quantity: e.target.value })
              }
              inputProps={{ min: 1, max: moveBatch?.quantity }}
              fullWidth
            />
            <TextField
              label="Notes"
              value={moveForm.notes}
              onChange={(e) =>
                setMoveForm({ ...moveForm, notes: e.target.value })
              }
              multiline
              rows={2}
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMoveDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleMoveSubmit}
            variant="contained"
            disabled={!moveForm.to_location_id}
          >
            Move
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
