import Navbar from '../components/Navbar'
import Panel from "../components/CaseDetail/DiagnosisPanel";
import Viewer from "../components/CaseDetail/ImageViewer";
import { Box } from '@mui/material';
import ToolPanel from '../components/CaseDetail/ToolPanel';
import { useParams } from 'react-router-dom';
import { useCases } from '../CasesContext';

export default function CaseDetailPage() {
  const { id } = useParams()
  const { cases, } = useCases()
  const currentCase = cases.find(c => c.id === id)


  return (
    <>
      <Navbar label='Home'/>
      <Box 
        display="flex" 
        flexDirection="row" 
        gap={2} 
        padding={2}
        sx={{ height: 'calc(100vh - 64px)', overflow: 'hidden' }}
      >
        <Viewer imageUrl={currentCase?.imageUrl} polygons={currentCase?.result?.polygons}/>
        <Panel pipelineOutput={currentCase?.result} />
        <ToolPanel confidence={currentCase?.result?.confidence} onSaveDraft={() => console.log('save draft')}
  onGenerateReport={() => console.log('generate report')}/>
      </Box>
    </>
  )
}