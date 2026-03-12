import Navbar from '../components/Navbar'
import Panel from "../components/CaseDetail/DiagnosisPanel";
import Viewer from "../components/CaseDetail/ImageViewer";
import { Box } from '@mui/material';



export default function CaseDetailPage() {
  return (
    <>
    <Navbar label='Home'/>
    <Box display="flex" flexDirection="row" alignItems="center" gap={2} padding={2}>
      <Viewer />
      <Panel />   
    </Box>
    </>
  )
}