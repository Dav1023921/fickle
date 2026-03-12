import MainPanel from "../components/HomePage";
import Navbar from "../components/Navbar";
import { Box } from '@mui/material';

export default function HomePage() {
  return (
    <>
      <Navbar label={"My Account"}/> 
      <Box sx={{ display: 'flex', flexDirection: 'row', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <MainPanel />
      </Box>
    </>
  )
  ;

}