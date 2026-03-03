import Box from '@mui/material/Box';
import DiagnosisLabel from './DiagnosisLabel';

const Diagnosis = () => {
    return(
        <Box p={1} sx={{bgcolor: 'primary.dark'}}>
            <DiagnosisLabel />
        </Box>
    )
}

export default Diagnosis;

