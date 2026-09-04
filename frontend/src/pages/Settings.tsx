import { useState } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  Alert,
  TextField,
  Snackbar,
} from '@mui/material'
import { ContentCopy as CopyIcon, Key as KeyIcon } from '@mui/icons-material'
import { authApi } from '../services/api'
import { useAuth } from '../contexts/AuthContext'

export default function Settings() {
  const { user } = useAuth()
  const [apiKey, setApiKey] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [snackbar, setSnackbar] = useState(false)

  const handleGenerateApiKey = async () => {
    if (
      apiKey &&
      !window.confirm(
        'This will invalidate your existing API key. Continue?'
      )
    ) {
      return
    }

    try {
      setLoading(true)
      const response = await authApi.generateApiKey()
      setApiKey(response.data.api_key)
    } catch (err) {
      setError('Failed to generate API key')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleRevokeApiKey = async () => {
    if (!window.confirm('Are you sure you want to revoke your API key?')) {
      return
    }

    try {
      setLoading(true)
      await authApi.revokeApiKey()
      setApiKey(null)
    } catch (err) {
      setError('Failed to revoke API key')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleCopyApiKey = () => {
    if (apiKey) {
      navigator.clipboard.writeText(apiKey)
      setSnackbar(true)
    }
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Profile Section */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Profile
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Typography>
              <strong>Username:</strong> {user?.username}
            </Typography>
            <Typography>
              <strong>Display Name:</strong> {user?.display_name || '-'}
            </Typography>
            <Typography>
              <strong>Email:</strong> {user?.email || '-'}
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {/* API Key Section */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            API Key for Agents
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Generate an API key to use with MCP agents or other integrations.
            The key is passed via the <code>x-agent-secret</code> header.
          </Typography>

          {apiKey && (
            <Box sx={{ mb: 2 }}>
              <Alert severity="warning" sx={{ mb: 2 }}>
                Save this key now! It will not be shown again.
              </Alert>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField
                  value={apiKey}
                  fullWidth
                  size="small"
                  InputProps={{ readOnly: true }}
                />
                <Button
                  variant="outlined"
                  onClick={handleCopyApiKey}
                  startIcon={<CopyIcon />}
                >
                  Copy
                </Button>
              </Box>
            </Box>
          )}

          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="contained"
              onClick={handleGenerateApiKey}
              disabled={loading}
              startIcon={<KeyIcon />}
            >
              {apiKey ? 'Regenerate API Key' : 'Generate API Key'}
            </Button>
            {apiKey && (
              <Button
                variant="outlined"
                color="error"
                onClick={handleRevokeApiKey}
                disabled={loading}
              >
                Revoke Key
              </Button>
            )}
          </Box>
        </CardContent>
      </Card>

      <Snackbar
        open={snackbar}
        autoHideDuration={2000}
        onClose={() => setSnackbar(false)}
        message="API key copied to clipboard"
      />
    </Box>
  )
}
