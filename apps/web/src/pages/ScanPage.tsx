import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Container,
  Typography,
  Card,
  CardContent,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Button,
  Alert,
  Box,
  LinearProgress,
} from '@mui/material'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import { apiService } from '@/services/api'
import { ScanMode, ScanProgress, WebSocketMessage } from '@/types/api'

export default function ScanPage() {
  const navigate = useNavigate()
  const [directory, setDirectory] = useState('/app/videos')
  const [mode, setMode] = useState<ScanMode>(ScanMode.QUICK)
  const [recursive, setRecursive] = useState(true)
  const [maxWorkers, setMaxWorkers] = useState(8)
  const [scanning, setScanning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [scanId, setScanId] = useState<string | null>(null)
  const [progress, setProgress] = useState<ScanProgress | null>(null)

  useEffect(() => {
    if (!scanId) return

    const ws = apiService.createWebSocket(scanId)

    ws.onmessage = (event) => {
      const message: WebSocketMessage = JSON.parse(event.data)

      if (message.type === 'progress') {
        setProgress(message.data)
      } else if (message.type === 'complete') {
        setScanning(false)
        if (message.data.status === 'completed') {
          navigate(`/results/${scanId}`)
        } else if (message.data.error) {
          setError(message.data.error)
        }
      } else if (message.type === 'error') {
        setError(message.data.message)
        setScanning(false)
      }
    }

    ws.onerror = () => {
      setError('WebSocket connection error')
      setScanning(false)
    }

    return () => {
      ws.close()
    }
  }, [scanId, navigate])

  const handleStartScan = async () => {
    try {
      setError(null)
      setScanning(true)
      setProgress(null)

      const response = await apiService.startScan({
        directory,
        mode,
        recursive,
        max_workers: maxWorkers,
      })

      setScanId(response.scan_id)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start scan')
      setScanning(false)
    }
  }

  return (
    <Container maxWidth="md">
      <Typography variant="h4" gutterBottom>
        New Video Scan
      </Typography>

      <Card>
        <CardContent>
          <Box component="form" sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <TextField
              label="Directory Path"
              value={directory}
              onChange={(e) => setDirectory(e.target.value)}
              disabled={scanning}
              fullWidth
              required
              helperText="Enter the full path to the directory containing video files"
            />

            <FormControl fullWidth disabled={scanning}>
              <InputLabel>Scan Mode</InputLabel>
              <Select value={mode} label="Scan Mode" onChange={(e) => setMode(e.target.value as ScanMode)}>
                <MenuItem value={ScanMode.QUICK}>Quick (Fast, basic checks)</MenuItem>
                <MenuItem value={ScanMode.DEEP}>Deep (Thorough, slower)</MenuItem>
                <MenuItem value={ScanMode.HYBRID}>Hybrid (Quick first, then deep on suspicious files)</MenuItem>
              </Select>
            </FormControl>

            <TextField
              label="Max Workers"
              type="number"
              value={maxWorkers}
              onChange={(e) => setMaxWorkers(parseInt(e.target.value))}
              disabled={scanning}
              inputProps={{ min: 1, max: 32 }}
              helperText="Number of parallel scanning threads (1-32)"
            />

            <FormControlLabel
              control={
                <Checkbox
                  checked={recursive}
                  onChange={(e) => setRecursive(e.target.checked)}
                  disabled={scanning}
                />
              }
              label="Scan subdirectories recursively"
            />

            {error && <Alert severity="error">{error}</Alert>}

            {scanning && progress && (
              <Box>
                <Typography variant="body2" gutterBottom>
                  Scanning: {progress.processed_count} / {progress.total_files} files (
                  {progress.progress_percentage.toFixed(1)}%)
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={progress.progress_percentage}
                  sx={{ mb: 1 }}
                />
                <Typography variant="caption" color="textSecondary">
                  Healthy: {progress.healthy_count} | Corrupt: {progress.corrupt_count} |
                  Suspicious: {progress.suspicious_count}
                </Typography>
                {progress.current_file && (
                  <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                    Current: {progress.current_file}
                  </Typography>
                )}
              </Box>
            )}

            <Button
              variant="contained"
              size="large"
              startIcon={<PlayArrowIcon />}
              onClick={handleStartScan}
              disabled={scanning || !directory}
            >
              {scanning ? 'Scanning...' : 'Start Scan'}
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Container>
  )
}
