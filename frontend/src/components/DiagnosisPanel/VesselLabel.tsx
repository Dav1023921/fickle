import Box from '@mui/material/Box';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import TextField from '@mui/material/TextField';
import Vessel from './Vessel'

const VesselLabel = () => {
    return(
        <Box>
        <List sx={{ width: '100%', maxWidth: 360, bgcolor: 'background.paper' }}>
            <ListItem>
                <Vessel label = "Vein 1 Length"/>
            </ListItem>
            <ListItem>
                <Vessel label = "Artery 1 Length"/>
            </ListItem>
            <ListItem>
                <Vessel label = "Artery 2 Length"/>
            </ListItem>
            
        </List>
        </Box>
    )
}

export default VesselLabel;