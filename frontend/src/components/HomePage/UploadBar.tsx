import { Box, Typography } from "@mui/material";
import { styled } from '@mui/material/styles';
import Button from '@mui/material/Button';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { Padding } from "@mui/icons-material";

const VisuallyHiddenInput = styled('input')({
  clip: 'rect(0 0 0 0)',
  clipPath: 'inset(50%)',
  height: 1,
  overflow: 'hidden',
  position: 'absolute',
  bottom: 0,
  left: 0,
  whiteSpace: 'nowrap',
  width: 1,
});


const style = {
    width: "100%", 
  backgroundColor: 'background.paper',
  padding: 2,
};

const UploadBar = () => {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', ...style }}>
        <Typography>My Cases</Typography>
         <Button
            component="label"
            role={undefined}
            variant="contained"
            tabIndex={-1}
            startIcon={<CloudUploadIcon />}
            >
            Upload files
      <VisuallyHiddenInput
        type="file"
        multiple
      />
    </Button>
    </Box>
  )
}

export default UploadBar;