import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Container,
  Typography,
  Card,
  CardContent,
  Grid,
  Alert,
  CircularProgress,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
} from '@mui/material'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import ErrorIcon from '@mui/icons-material/Error'
import WarningIcon from '@mui/icons-material/Warning'
import { apiService } from '@/services/api'
import { ScanResultsResponse, ScanResult } from '@/types/api'

export default function ResultsPage() {
  const { scanId } = useParams<{ scanId: string }>()
  const [results, setResults] = useState<ScanResultsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchResults = async () => {
      if (!scanId) return

      try {
        const response = await apiService.getScanResults(scanId)
        setResults(response)
        setError(null)
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load scan results')
      } finally {
        setLoading(false)
      }
    }

    fetchResults()
  }, [scanId])

  if (loading) {
    return (
      <Container>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      </Container>
    )
  }

  if (error || !results) {
    return (
      <Container>
        <Alert severity="error">{error || 'Failed to load results'}</Alert>
      </Container>
    )
  }

  const getStatusIcon = (result: ScanResult) => {
    if (result.is_corrupt) {
      return <ErrorIcon color="error" />
    } else if (result.confidence < 0.8) {
      return <WarningIcon color="warning" />
    } else {
      return <CheckCircleIcon color="success" />
    }
  }

  const getStatusColor = (result: ScanResult) => {
    if (result.is_corrupt) return 'error'
    else if (result.confidence < 0.8) return 'warning'
    else return 'success'
  }

  return (
    <Container maxWidth="xl">
      <Typography variant="h4" gutterBottom>
        Scan Results
      </Typography>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Files
              </Typography>
              <Typography variant="h4">{results.summary.total_files}</Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Healthy
              </Typography>
              <Typography variant="h4" color="success.main">
                {results.summary.healthy_files}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Corrupt
              </Typography>
              <Typography variant="h4" color="error.main">
                {results.summary.corrupt_files}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Suspicious
              </Typography>
              <Typography variant="h4" color="warning.main">
                {results.summary.suspicious_files}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Scan Details
          </Typography>

          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Status</TableCell>
                  <TableCell>File Name</TableCell>
                  <TableCell align="right">Size (MB)</TableCell>
                  <TableCell align="right">Confidence</TableCell>
                  <TableCell>Issues</TableCell>
                  <TableCell align="right">Scan Time (s)</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {results.results.map((result, index) => (
                  <TableRow key={index}>
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={1}>
                        {getStatusIcon(result)}
                        <Chip
                          label={result.is_corrupt ? 'Corrupt' : 'Healthy'}
                          color={getStatusColor(result)}
                          size="small"
                        />
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" noWrap sx={{ maxWidth: 300 }}>
                        {result.file_name}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      {(result.file_size / 1024 / 1024).toFixed(2)}
                    </TableCell>
                    <TableCell align="right">
                      {(result.confidence * 100).toFixed(1)}%
                    </TableCell>
                    <TableCell>
                      {result.issues.length > 0 ? (
                        <Typography variant="caption" color="error">
                          {result.issues.join(', ')}
                        </Typography>
                      ) : (
                        <Typography variant="caption" color="textSecondary">
                          None
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell align="right">{result.scan_time.toFixed(2)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Container>
  )
}
