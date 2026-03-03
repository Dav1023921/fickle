import Card from '@mui/material/Card';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Stack from '@mui/material/Stack';
import Divider from '@mui/material/Divider';
import Typography from '@mui/material/Typography';
import Diagnosis from './Diagnosis';
import PredictionLabel from './PredictionLabel';


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

const Panel = () => {
  return (
     <Card variant="outlined" sx={style}>
  
      <Box>
        <Stack spacing={2}>
          <Diagnosis />
          <PredictionLabel />
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
          Select type
        </Typography>
        <Stack direction="row" spacing={1}>
          <Chip color="primary" label="Soft" size="small" />
          <Chip label="Medium" size="small" />
          <Chip label="Hard" size="small" />
        </Stack>
      </Box>
    </Card>
  );
};

export default Panel;

