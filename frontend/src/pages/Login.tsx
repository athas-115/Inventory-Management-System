import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, Button, Container, Paper, Typography } from '@mui/material'
import { GitHub as GitHubIcon } from '@mui/icons-material'
import { useAuth } from '../contexts/AuthContext'

export default function Login() {
  const { user } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (user) {
      navigate('/')
    }
  }, [user, navigate])

  const handleLogin = () => {
    window.location.href = '/api/auth/login'
  }

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Paper
          elevation={3}
          sx={{
            p: 4,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 3,
          }}
        >
          <Typography variant="h4" component="h1">
            Inventory Management
          </Typography>
          <Typography variant="body1" color="text.secondary" textAlign="center">
            Track your household inventory with ease.
            <br />
            Sign in with GitHub to get started.
          </Typography>
          <Button
            variant="contained"
            size="large"
            startIcon={<GitHubIcon />}
            onClick={handleLogin}
            sx={{ mt: 2 }}
          >
            Sign in with GitHub
          </Button>
        </Paper>
      </Box>
    </Container>
  )
}
