import { Typography } from '@mui/material';
import LightbulbIcon from "@mui/icons-material/Lightbulb";
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';



const DiagnosisLabel = () => {
    return(
        <Box>
            <Stack direction="row" spacing={1}
            sx={{
            justifyContent: "flex-start",}}>
                <LightbulbIcon fontSize="small" sx={{ color: "#FFFFFF" }} />
                <Typography variant="h4" sx={{ color: "#FFFFFF" }}>Findings</Typography>
            </Stack>
        </Box>   
    )
}

export default DiagnosisLabel;

