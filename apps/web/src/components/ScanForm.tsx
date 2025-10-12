import React, { useState } from 'react';
import {
  Box,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  FormControlLabel,
  Switch,
  Alert,
  CircularProgress,
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import { apiClient, ScanRequest } from '../api/client';

interface ScanFormProps {
  onScanCreated: (scanId: string) => void;
}

const ScanForm: React.FC<ScanFormProps> = ({ onScanCreated }) => {
  const [directory, setDirectory] = useState('');
  const [scanMode, setScanMode] = useState<'quick' | 'deep' | 'hybrid'>('quick');
  const [recursive, setRecursive] = useState(true);
  const [resume, setResume] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const request: ScanRequest = {
        directory,
        scan_mode: scanMode,
        recursive,
        resume,
      };

      const response = await apiClient.createScan(request);
      onScanCreated(response.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create scan');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ maxWidth: 600, mx: 'auto' }}>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <TextField
        fullWidth
        label="Directory Path"
        value={directory}
        onChange={(e) => setDirectory(e.target.value)}
        required
        margin="normal"
        placeholder="/path/to/videos"
        helperText="Enter the absolute path to the directory containing video files"
      />

      <FormControl fullWidth margin="normal">
        <InputLabel>Scan Mode</InputLabel>
        <Select
          value={scanMode}
          label="Scan Mode"
          onChange={(e) => setScanMode(e.target.value as 'quick' | 'deep' | 'hybrid')}
        >
          <MenuItem value="quick">Quick - Fast scan with basic checks</MenuItem>
          <MenuItem value="deep">Deep - Thorough scan with full analysis</MenuItem>
          <MenuItem value="hybrid">Hybrid - Quick first, deep on suspicious files</MenuItem>
        </Select>
      </FormControl>

      <FormControlLabel
        control={<Switch checked={recursive} onChange={(e) => setRecursive(e.target.checked)} />}
        label="Scan subdirectories recursively"
        sx={{ mt: 2, display: 'block' }}
      />

      <FormControlLabel
        control={<Switch checked={resume} onChange={(e) => setResume(e.target.checked)} />}
        label="Resume from previous scan if available"
        sx={{ display: 'block' }}
      />

      <Button
        type="submit"
        variant="contained"
        fullWidth
        size="large"
        disabled={loading || !directory}
        startIcon={loading ? <CircularProgress size={20} /> : <PlayArrowIcon />}
        sx={{ mt: 3 }}
      >
        {loading ? 'Starting Scan...' : 'Start Scan'}
      </Button>
    </Box>
  );
};

export default ScanForm;
