import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  LinearProgress,
  Paper,
  Grid,
  Card,
  CardContent,
  Alert,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import { apiClient, ProgressUpdate, ScanResponse } from '../api/client';

interface ScanResultsProps {
  scanId: string;
}

const ScanResults: React.FC<ScanResultsProps> = ({ scanId }) => {
  const [scan, setScan] = useState<ScanResponse | null>(null);
  const [progress, setProgress] = useState<ProgressUpdate | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Load initial scan data
    loadScan();

    // Connect to WebSocket for real-time updates
    const ws = apiClient.connectWebSocket(
      scanId,
      (update) => {
        setProgress(update);
        if (update.status === 'completed' || update.status === 'failed') {
          // Refresh scan data when complete
          loadScan();
        }
      },
      (error) => {
        console.error('WebSocket error:', error);
      }
    );

    return () => {
      ws.close();
    };
  }, [scanId]);

  const loadScan = async () => {
    try {
      const data = await apiClient.getScan(scanId);
      setScan(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load scan');
    }
  };

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  if (!scan) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <Typography>Loading scan data...</Typography>
      </Box>
    );
  }

  const progressPercentage = progress?.progress_percentage || 0;
  const isRunning = scan.status === 'running';
  const isCompleted = scan.status === 'completed';
  const isFailed = scan.status === 'failed';

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Scan: {scan.directory}
      </Typography>

      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Status: <strong>{scan.status}</strong>
        </Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Scan Mode: <strong>{scan.scan_mode}</strong>
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Started: {new Date(scan.started_at).toLocaleString()}
        </Typography>
        {scan.completed_at && (
          <Typography variant="body2" color="text.secondary">
            Completed: {new Date(scan.completed_at).toLocaleString()}
          </Typography>
        )}
      </Paper>

      {isRunning && progress && (
        <Paper sx={{ p: 2, mb: 2 }}>
          <Typography variant="h6" gutterBottom>
            Progress
          </Typography>
          <LinearProgress variant="determinate" value={progressPercentage} sx={{ mb: 2 }} />
          <Typography variant="body2">
            {progress.processed_files} / {progress.total_files} files ({progressPercentage.toFixed(1)}%)
          </Typography>
          {progress.current_file && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Current: {progress.current_file}
            </Typography>
          )}
        </Paper>
      )}

      {(isCompleted || (progress && progress.processed_files > 0)) && (
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <CheckCircleIcon color="success" sx={{ mr: 1 }} />
                  <Typography variant="h6">Healthy Files</Typography>
                </Box>
                <Typography variant="h3">
                  {progress?.healthy_count || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <ErrorIcon color="error" sx={{ mr: 1 }} />
                  <Typography variant="h6">Corrupt Files</Typography>
                </Box>
                <Typography variant="h3">
                  {progress?.corrupt_count || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {isFailed && progress?.error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {progress.error}
        </Alert>
      )}
    </Box>
  );
};

export default ScanResults;
