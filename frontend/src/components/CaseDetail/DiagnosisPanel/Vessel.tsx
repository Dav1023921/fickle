import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import { Typography } from '@mui/material';
import TextField from '@mui/material/TextField';


type VesselLabelProps = {
    label: string
}


const Vessel = ({label}: VesselLabelProps) => {
    return(
<Card variant="outlined">
    <CardContent
    
    sx={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between"
    }}
    >
    <Typography variant="h5" sx={{ width: 180 }}>
        {label}
    </Typography>
    <TextField
        variant = "outlined"
        size="small"
        sx={{ width: 150, "& .MuiOutlinedInput-root": {
        height: 30,
        },
        "& .MuiInputLabel-root": {
        fontSize: 10,
        } }}
    />
    </CardContent>
</Card>
    )
}

export default Vessel