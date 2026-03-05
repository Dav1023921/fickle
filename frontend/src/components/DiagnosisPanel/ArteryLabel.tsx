import Box from '@mui/material/Box';
import { Stack, Typography } from '@mui/material';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';

type ArteryLabelProps = {
  label: string
}


const ArteryLabel = ({ label }: ArteryLabelProps) => {
    return (
       <Box pt={1}>
        <Stack direction={"row"} sx={{justifyContent: "space-between"}}>
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
          <MenuItem value={10}>One</MenuItem>
          <MenuItem value={20}>Two</MenuItem>
        </Select>

            
            
        </Stack>
       </Box>
    )
}

export default ArteryLabel;