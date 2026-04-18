import Card from '@mui/material/Card';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import Divider from '@mui/material/Divider';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import SaveIcon from '@mui/icons-material/Save';
import ArticleIcon from '@mui/icons-material/Article';

interface ToolPanelProps {
  confidence?: number;
  onSaveDraft?: () => void;
  onGenerateReport?: () => void;
}

const ToolPanel = ({ confidence, onSaveDraft, onGenerateReport }: ToolPanelProps) => {
  const pct = Math.round((confidence ?? 0) * 100);
  const barColor = pct > 75 ? 'success.main' : pct > 50 ? 'warning.main' : 'error.main';

  return (
    <Card variant="outlined" sx={{
      py: 0,
      width: '100%',
      minWidth: 350,
      maxWidth: 400,
      borderRadius: 2,
      border: '1px solid',
      borderColor: 'divider',
      backgroundColor: 'background.paper',
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
    }}>

      {/* header */}
      <Box sx={{ px: 2.5, py: 1.25, bgcolor: '#1a1a1a' }}>
        <Typography variant="body2" fontWeight={500} sx={{ color: 'white' }}>
          Actions
        </Typography>
      </Box>

      {/* overall confidence */}
      <Box sx={{ px: 2.5, py: 2 }}>
        <Typography variant="caption" fontWeight={600} color="text.secondary"
          sx={{ textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          Overall Confidence
        </Typography>
        <Box sx={{ mt: 1.5, display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Box sx={{ flex: 1, height: 8, bgcolor: 'grey.100', borderRadius: 4, overflow: 'hidden' }}>
            <Box sx={{
              height: '100%',
              width: `${pct}%`,
              bgcolor: barColor,
              borderRadius: 4,
              transition: 'width 0.3s ease',
            }} />
          </Box>
          <Typography variant="body2" fontWeight={600}>{confidence ? `${pct}%` : '—'}</Typography>
        </Box>
      </Box>

      <Divider />

      {/* other findings */}
      <Box sx={{ px: 2.5, py: 2, flex: 1 }}>
        <Typography variant="caption" fontWeight={600} color="text.secondary"
          sx={{ textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          Other Findings
        </Typography>
      </Box>

      <Divider />

      {/* actions */}
      <Box sx={{ px: 2.5, py: 2 }}>
        <Stack spacing={1.5}>
          <Button
            variant="outlined"
            startIcon={<SaveIcon />}
            fullWidth
            onClick={onSaveDraft}
            sx={{ borderRadius: 2, textTransform: 'none', fontWeight: 500 }}
          >
            Save Draft
          </Button>
          <Button
            variant="contained"
            startIcon={<ArticleIcon />}
            fullWidth
            onClick={onGenerateReport}
            sx={{ borderRadius: 2, textTransform: 'none', fontWeight: 500, bgcolor: '#1a1a1a',
              '&:hover': { bgcolor: '#333' }
            }}
          >
            Generate Report
          </Button>
        </Stack>
      </Box>

    </Card>
  );
};

export default ToolPanel;