import { Box,  Typography } from '@mui/material';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';

type ArteryLabelProps = {
  label: string
  menuItemOne: string
  menuItemTwo: string
}


const ArteryLabel = ({ label, menuItemOne, menuItemTwo }: ArteryLabelProps) => {
    return (
        <Box sx={{display: "flex",justifyContent: "space-between", pl:2, pr:2}}>
            <Typography variant="h4">
                   {label}
            </Typography>
        <Select
          sx={{
            height:30,
            width:80,
            fontSize: 12,
             }}
        >
          <MenuItem value={10}>{menuItemOne}</MenuItem>
          <MenuItem value={20}>{menuItemTwo}</MenuItem>
        </Select>

            
            
        </Box>
    )
}

export default ArteryLabel;