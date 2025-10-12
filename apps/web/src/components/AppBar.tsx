import { AppBar as MuiAppBar, Toolbar, Typography, Button, Box } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import VideoLibraryIcon from '@mui/icons-material/VideoLibrary'

export default function AppBar() {
  const navigate = useNavigate()

  return (
    <MuiAppBar position="fixed">
      <Toolbar>
        <VideoLibraryIcon sx={{ mr: 2 }} />
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Corrupt Video Inspector
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button color="inherit" onClick={() => navigate('/')}>
            Dashboard
          </Button>
          <Button color="inherit" onClick={() => navigate('/scan')}>
            New Scan
          </Button>
        </Box>
      </Toolbar>
    </MuiAppBar>
  )
}
