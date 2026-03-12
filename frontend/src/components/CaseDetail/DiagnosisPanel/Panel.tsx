import Card from '@mui/material/Card';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import Divider from '@mui/material/Divider';
import Typography from '@mui/material/Typography';
import Diagnosis from './Diagnosis';
import PredictionLabel from './PredictionLabel';
import ArteryLabel from './ArteryLabel';
import VesselLabel from './VesselLabel';

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
      <Diagnosis />
      <Box sx={{ p: 2 , display: 'flex', justifyContent: 'center'}}>
          <PredictionLabel />
      </Box>
      <Divider variant="middle"/>
      <Box sx={{ p: 2 }}>
        <Stack direction="column" spacing={2}>
          <Typography gutterBottom variant="body2">Diagnosis Details</Typography>
          <ArteryLabel label="Number of Arteries" menuItemOne='One' menuItemTwo='Two'/>
          <ArteryLabel label="Presence of vein" menuItemOne='True' menuItemTwo='False'/>
        </Stack>
      </Box>
      <Divider variant="middle"/>
      <Box sx={{ p: 2 }}>
        <Typography gutterBottom variant="body2">
          Vessel Diameters
        </Typography>
        <VesselLabel />
      </Box>
    </Card>
  );
};

export default Panel;

