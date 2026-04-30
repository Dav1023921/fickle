import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import type { CordPolygon } from '../../../CasesContext';

type Diagnostic = 'Normal' | 'SUA' | 'Uncertain';
type ReportedCounts = { arteries: number; veins: number };

interface ToolPanelProps {
  polygons?: CordPolygon[];
  reportedCounts?: ReportedCounts[];
  diagnosticOverride?: Diagnostic | null;
  reviewed?: boolean;
  onDiagnosticOverride?: (val: Diagnostic | null) => void;
  onMarkReviewed?: () => void;
  onUnmarkReviewed?: () => void;
  onGoBack?: () => void;
  onGenerateReport?: (diagnosis: Diagnostic) => void;
}

function cordDiagnostic(a: number, v: number): Diagnostic {
  if (a === 2 && v === 1) return 'Normal';
  if (a === 1 && v === 1) return 'SUA';
  return 'Uncertain';
}

function deriveOverall(counts: ReportedCounts[]): Diagnostic {
  if (!counts.length) return 'Uncertain';
  const diags = counts.map(c => cordDiagnostic(c.arteries, c.veins));
  if (diags.some(d => d === 'SUA'))      return 'SUA';
  if (diags.every(d => d === 'Normal'))  return 'Normal';
  return 'Uncertain';
}

const diagBg     = (d: Diagnostic) => d === 'Normal' ? '#dcfce7' : d === 'SUA' ? '#fee2e2' : '#fef9c3';
const diagBorder = (d: Diagnostic) => d === 'Normal' ? '#16a34a' : d === 'SUA' ? '#dc2626' : '#ca8a04';
const diagText   = (d: Diagnostic) => d === 'Normal' ? '#15803d' : d === 'SUA' ? '#b91c1c' : '#a16207';

export default function ToolPanel({
  reportedCounts = [], diagnosticOverride, reviewed = false,
  onMarkReviewed, onUnmarkReviewed, onGoBack
}: ToolPanelProps) {
  const derived  = deriveOverall(reportedCounts);
  const overall: Diagnostic = diagnosticOverride ?? derived;

  return (
    <Box sx={{
      width: '100%', minWidth: 300,
      border: '1px solid', borderColor: 'divider',
      borderRadius: 2, bgcolor: 'background.paper', p: 1.5,
    }}>

      {/* Overall diagnosis */}
      <Stack direction="row" alignItems="center" gap={1} mb={1.25}>
        <Typography fontSize={11} color="text.secondary" sx={{ whiteSpace: 'nowrap' }}>
          Overall diagnosis
        </Typography>
        <Box sx={{
          px: 1, py: 0.25,
          bgcolor: diagBg(overall),
          border: `1px solid ${diagBorder(overall)}`,
          borderRadius: 0.75,
        }}>
          <Typography fontSize={12} fontWeight={700} sx={{ color: diagText(overall) }}>
            {overall}
          </Typography>
        </Box>
      </Stack>


      {/* Actions */}
      <Stack direction="row" gap={1}>
        <Button size="small" variant="outlined" startIcon={<ArrowBackIcon />}
          onClick={onGoBack}
          sx={{ textTransform: 'none', fontSize: 12, flex: 1 }}>
          Back
        </Button>
        <Button size="small" variant={reviewed ? 'contained' : 'outlined'}
          startIcon={<CheckCircleIcon />}
          onClick={reviewed ? onUnmarkReviewed : onMarkReviewed}
          sx={{
            textTransform: 'none', fontSize: 12, flex: 1,
            ...(reviewed
              ? { bgcolor: '#16a34a', color: 'white', '&:hover': { bgcolor: '#15803d' } }
              : { borderColor: '#16a34a', color: '#16a34a' }),
          }}>
          {reviewed ? 'Reviewed' : 'Mark reviewed'}
        </Button>
      </Stack>
    </Box>
  );
}