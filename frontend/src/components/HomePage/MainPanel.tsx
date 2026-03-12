
import Box from '@mui/material/Box';
import UploadBar from './UploadBar';
import { theme } from '../../theme';



const MainPanel = () => {
    return(
        <Box sx={{ minWidth: 275, width:'90%', height:"80%", bgcolor: theme.palette.background.default, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <UploadBar />
            <Box>
                
            </Box>
        </Box>
    )
}   

export default MainPanel;