import Card from '@mui/material/Card';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import Divider from '@mui/material/Divider';
import Typography from '@mui/material/Typography';

const style = {
  py: 0,
  width: '100%',
  minWidth: 350,
  maxWidth: 400,
  borderRadius: 2,
  border: '1px solid',
  borderColor: 'divider',
  backgroundColor: 'background.paper',
};

const ToolPanel = () => {
  return (
     <Card variant="outlined" sx={style}>
  
      <Box>
        <Stack spacing={2}>
          <Typography>Actions</Typography>
          </Stack>
      </Box>
      <Divider variant="middle"/>
      <Box sx={{ p: 2 }}>
        <Stack direction="column" spacing={1}>
          <Typography gutterBottom variant="body2">
          Diagnosis Details
          </Typography>
        </Stack>
      </Box>
      <Divider variant="middle"/>
      <Box sx={{ p: 2 }}>
        <Typography gutterBottom variant="body2">
          Vessel Diameters
        </Typography>
      </Box>
    </Card>
  );
};

export default ToolPanel;

