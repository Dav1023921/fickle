import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';

const Navbar = () => {
  return (
      <AppBar position="sticky" sx={{ bgcolor: "primary.dark" }}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 , fontFamily: "Sans-serif"}}>
            Fickle
          </Typography>
          <Button color="inherit">Upload</Button>
        </Toolbar>
      </AppBar>
  );
}

export default Navbar