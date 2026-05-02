import MainPanel from "../components/HomePage";
import Navbar from "../components/Navbar";
import { Box } from '@mui/material';

export default function HomePage() {
  return (
    <>
      <Navbar label={""}/> 
      <Box sx={{ display: 'flex', flexDirection: 'row', justifyContent: 'center', alignItems: 'flex-start', paddingTop: 4 }}>
        <MainPanel />
      </Box>
    </>
  )
  ;

}