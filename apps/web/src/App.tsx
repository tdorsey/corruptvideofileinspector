import React, { useState } from 'react';
import {
  Container,
  Box,
  AppBar,
  Toolbar,
  Typography,
  Paper,
  Tabs,
  Tab,
} from '@mui/material';
import ScannerIcon from '@mui/icons-material/Scanner';
import ScanForm from './components/ScanForm';
import ScanList from './components/ScanList';
import ScanResults from './components/ScanResults';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

function App() {
  const [tabValue, setTabValue] = useState(0);
  const [selectedScanId, setSelectedScanId] = useState<string | null>(null);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleScanCreated = (scanId: string) => {
    setSelectedScanId(scanId);
    setTabValue(1); // Switch to progress tab
  };

  const handleScanSelected = (scanId: string) => {
    setSelectedScanId(scanId);
    setTabValue(2); // Switch to results tab
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static">
        <Toolbar>
          <ScannerIcon sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Corrupt Video Inspector
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Paper sx={{ width: '100%' }}>
          <Tabs value={tabValue} onChange={handleTabChange} centered>
            <Tab label="New Scan" />
            <Tab label="Scan Progress" />
            <Tab label="Results" />
          </Tabs>

          <TabPanel value={tabValue} index={0}>
            <ScanForm onScanCreated={handleScanCreated} />
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <ScanList onScanSelected={handleScanSelected} />
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            {selectedScanId ? (
              <ScanResults scanId={selectedScanId} />
            ) : (
              <Typography color="text.secondary" align="center">
                No scan selected. Create a new scan or select one from the
                progress tab.
              </Typography>
            )}
          </TabPanel>
        </Paper>
      </Container>
    </Box>
  );
}

export default App;
