import { Box, Typography, Button } from "@mui/material";
import { styled } from '@mui/material/styles';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';

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

type Props = {
  onFilesAdded: (files: FileList) => void
}

const UploadBar = ({ onFilesAdded }: Props) => {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', width: '100%', padding: 2, backgroundColor: 'background.paper' }}>
      <Typography>My Cases</Typography>
      <Button component="label" variant="contained" startIcon={<CloudUploadIcon />}>
        Upload Files
        <VisuallyHiddenInput type="file" multiple onChange={e => e.target.files && onFilesAdded(e.target.files)}/>
      </Button>
    </Box>
  )
}

export default UploadBar;