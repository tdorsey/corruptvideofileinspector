import React, { useState, useEffect } from 'react';
import {
  Box,
  List,
  ListItem,
  ListItemText,
  ListItemButton,
  Chip,
  Typography,
  CircularProgress,
  Alert,
} from '@mui/material';
import { apiClient, ScanResponse } from '../api/client';

interface ScanListProps {
  onScanSelected: (scanId: string) => void;
}

const ScanList: React.FC<ScanListProps> = ({ onScanSelected }) => {
  const [scans, setScans] = useState<ScanResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadScans();
    const interval = setInterval(loadScans, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const loadScans = async () => {
    try {
      const data = await apiClient.listScans();
      setScans(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load scans');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'running':
        return 'primary';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  if (scans.length === 0) {
    return (
      <Typography color="text.secondary" align="center" p={4}>
        No scans found. Create a new scan to get started.
      </Typography>
    );
  }

  return (
    <List>
      {scans.map((scan) => (
        <ListItem key={scan.id} disablePadding>
          <ListItemButton onClick={() => onScanSelected(scan.id)}>
            <ListItemText
              primary={scan.directory}
              secondary={
                <>
                  <Typography component="span" variant="body2" color="text.primary">
                    {scan.scan_mode}
                  </Typography>
                  {' — '}
                  {new Date(scan.started_at).toLocaleString()}
                  {scan.completed_at && ` — Completed: ${new Date(scan.completed_at).toLocaleString()}`}
                </>
              }
            />
            <Chip label={scan.status} color={getStatusColor(scan.status)} size="small" />
          </ListItemButton>
        </ListItem>
      ))}
    </List>
  );
};

export default ScanList;
