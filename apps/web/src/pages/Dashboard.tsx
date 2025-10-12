import { useEffect, useState } from 'react'
import {
  Container,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  Alert,
  CircularProgress,
  Box,
} from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { apiService } from '@/services/api'
import { HealthResponse } from '@/types/api'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import ErrorIcon from '@mui/icons-material/Error'

export default function Dashboard() {
  const navigate = useNavigate()
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await apiService.healthCheck()
        setHealth(response)
        setError(null)
      } catch (err) {
        setError('Failed to connect to API server')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    checkHealth()
  }, [])

  if (loading) {
    return (
      <Container>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      </Container>
    )
  }

  return (
    <Container maxWidth="lg">
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {health && (
        <>
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    System Status
                  </Typography>
                  <Box display="flex" alignItems="center" gap={1}>
                    {health.status === 'healthy' ? (
                      <CheckCircleIcon color="success" />
                    ) : (
                      <ErrorIcon color="error" />
                    )}
                    <Typography variant="h5">{health.status}</Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    API Version
                  </Typography>
                  <Typography variant="h5">{health.version}</Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    FFmpeg Status
                  </Typography>
                  <Box display="flex" alignItems="center" gap={1}>
                    {health.ffmpeg_available ? (
                      <CheckCircleIcon color="success" />
                    ) : (
                      <ErrorIcon color="error" />
                    )}
                    <Typography variant="h5">
                      {health.ffmpeg_available ? 'Available' : 'Not Found'}
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Button
                  variant="contained"
                  size="large"
                  startIcon={<PlayArrowIcon />}
                  onClick={() => navigate('/scan')}
                  disabled={!health.ffmpeg_available}
                >
                  Start New Scan
                </Button>
              </Box>
              {!health.ffmpeg_available && (
                <Alert severity="warning" sx={{ mt: 2 }}>
                  FFmpeg is required to run scans. Please ensure FFmpeg is installed and available
                  in the system PATH.
                </Alert>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </Container>
  )
}
