import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';

const Navbar = () => {
  return (
      <AppBar position="sticky" sx={{ bgcolor: "primary.dark" } }>
        <Toolbar sx={{display:'flex', justifyContent:'space-between'}}>
          <Typography variant="h6" sx={{fontFamily: "Sans-serif", flexGrow:0.05}}>
            Fickle
          </Typography>
          <Button color="inherit">Upload</Button>
        </Toolbar>
      </AppBar>
  );
}

export default Navbar