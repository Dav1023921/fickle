import Divider from '@mui/material/Divider';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import IconButton from '@mui/material/IconButton';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import LightbulbIcon from '@mui/icons-material/Lightbulb';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import type { CordPolygon, PipelineResult as PipelineOutput } from '../../../CasesContext';

type ReportedCounts = {
  arteries: number;
  veins: number;
  diagnosticOverride?: 'Normal' | 'SUA' | 'Uncertain' | null;
};

interface PanelProps {
  polygons: CordPolygon[];
  onPolygonsChange: (polygons: CordPolygon[]) => void;
  pipelineOutput?: PipelineOutput;
  hoveredCordIndex: number | null;
  onCordHover: (index: number | null) => void;
  reportedCounts: ReportedCounts[];
  onReportedCountsChange: (counts: ReportedCounts[]) => void;
  onAddCord: () => void;
  onDeleteCord: (index: number) => void;
}

function cordDiagnostic(a: number, v: number): 'Normal' | 'SUA' | 'Uncertain' {
  if (a === 2 && v === 1) return 'Normal';
  if (a === 1 && v === 1) return 'SUA';
  return 'Uncertain';
}

const diagBg    = (d: string) => d === 'Normal' ? '#dcfce7' : d === 'SUA' ? '#fee2e2' : '#fef9c3';
const diagBorder = (d: string) => d === 'Normal' ? '#16a34a' : d === 'SUA' ? '#dc2626' : '#ca8a04';
const diagText  = (d: string) => d === 'Normal' ? '#15803d' : d === 'SUA' ? '#b91c1c' : '#a16207';
const confColor = (c: number) => c >= 80 ? '#15803d' : c >= 50 ? '#b45309' : '#b91c1c';

function Spinner({ label, color, value, onChange }: {
  label: string; color: string; value: number; onChange: (v: number) => void;
}) {
  return (
    <Stack direction="row" alignItems="center" justifyContent="space-between" mb={0.75}>
      <Stack direction="row" alignItems="center" gap={0.75}>
        <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: color }} />
        <Typography fontSize={12}>{label}</Typography>
      </Stack>
      <Stack direction="row" alignItems="center" gap={0.25}>
        <Typography fontWeight={600} fontSize={13} sx={{ minWidth: 20, textAlign: 'center' }}>{value}</Typography>
        <Stack>
          <IconButton size="small" sx={{ p: 0 }} onClick={() => onChange(value + 1)}>
            <KeyboardArrowUpIcon sx={{ fontSize: 14 }} />
          </IconButton>
          <IconButton size="small" sx={{ p: 0 }} onClick={() => onChange(Math.max(0, value - 1))}>
            <KeyboardArrowDownIcon sx={{ fontSize: 14 }} />
          </IconButton>
        </Stack>
      </Stack>
    </Stack>
  );
}

function CordCard({ index, cord, reported, isHovered, onReportedChange, onCordChange, onDelete, onMouseEnter, onMouseLeave }: {
  index: number;
  cord: CordPolygon;
  reported: ReportedCounts;
  isHovered: boolean;
  onReportedChange: (r: ReportedCounts) => void;
  onCordChange: (c: CordPolygon) => void;
  onDelete: () => void;
  onMouseEnter: () => void;
  onMouseLeave: () => void;
}) {
  const isManual   = cord.vessels.length === 0 && cord.polygon.length === 0;
  const aiDiag     = cordDiagnostic(
    cord.vessels.filter(v => v.type === 'Artery').length,
    cord.vessels.filter(v => v.type === 'Vein').length,
  );
  const repDiag    = cordDiagnostic(reported.arteries, reported.veins);
  const activeDiag = reported.diagnosticOverride ?? repDiag;

  return (
    <Box
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      sx={{
        borderLeft: isHovered ? '3px solid #facc15' : '3px solid transparent',
        bgcolor: isHovered ? 'rgba(250,204,21,0.05)' : 'transparent',
        transition: 'background-color 0.15s',
      }}
    >
      {/* Card header */}
      <Stack direction="row" alignItems="center" justifyContent="space-between"
        sx={{ px: 1.5, py: 1, borderBottom: '1px solid', borderColor: 'divider' }}>
        <Typography fontSize={11} fontWeight={700} color="text.secondary" sx={{ textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          Cord {index + 1}{isManual && <span style={{ fontWeight: 400, marginLeft: 4 }}>(manual)</span>}
        </Typography>
        <IconButton size="small" onClick={onDelete} sx={{ color: '#dc2626', p: 0.25 }}>
          <DeleteIcon sx={{ fontSize: 14 }} />
        </IconButton>
      </Stack>

      {/* Two columns */}
      <Stack direction="row" divider={<Divider orientation="vertical" flexItem />}>

        {/* LEFT — AI suggestions (read-only) */}
        <Box sx={{ flex: 1, px: 1.5, py: 1 }}>
          <Typography fontSize={10} color="text.disabled" fontWeight={600}
            sx={{ textTransform: 'uppercase', letterSpacing: '0.06em', mb: 1 }}>
            AI detected
          </Typography>

          {isManual ? (
            <Typography fontSize={11} color="text.disabled">No model data</Typography>
          ) : cord.vessels.length === 0 ? (
            <Typography fontSize={11} color="text.disabled">None detected</Typography>
          ) : (
            cord.vessels.map((v, i) => {
              const conf = v.confidence !== undefined ? Math.round(v.confidence * 100) : null;
              return (
                <Stack key={i} direction="row" alignItems="center" justifyContent="space-between" mb={0.5}>
                  <Stack direction="row" alignItems="center" gap={0.75}>
                    <Box sx={{ width: 7, height: 7, borderRadius: '50%', bgcolor: v.type === 'Artery' ? '#ef4444' : '#3b82f6' }} />
                    <Typography fontSize={11} color="text.secondary">{v.type} {i + 1}</Typography>
                  </Stack>
                  {conf !== null && (
                    <Typography fontSize={11} fontWeight={600} sx={{ color: confColor(conf), fontFamily: 'monospace' }}>
                      {conf}%
                    </Typography>
                  )}
                </Stack>
              );
            })
          )}

          {/* AI suggestion badge */}
          {!isManual && (
            <Box sx={{
              mt: 1, display: 'inline-block',
              px: 0.75, py: 0.25,
              bgcolor: diagBg(aiDiag),
              border: `1px solid ${diagBorder(aiDiag)}`,
              borderRadius: 0.5,
            }}>
              <Typography fontSize={10} fontWeight={700} sx={{ color: diagText(aiDiag) }}>
                {aiDiag}
              </Typography>
            </Box>
          )}
        </Box>

        {/* RIGHT — To be reported (editable) */}
        <Box sx={{ flex: 1, px: 1.5, py: 1 }}>
          <Typography fontSize={10} color="text.disabled" fontWeight={600}
            sx={{ textTransform: 'uppercase', letterSpacing: '0.06em', mb: 1 }}>
            To report
          </Typography>

          <Spinner label="Arteries" color="#ef4444" value={reported.arteries}
            onChange={v => onReportedChange({ ...reported, arteries: v })} />
          <Spinner label="Veins" color="#3b82f6" value={reported.veins}
            onChange={v => onReportedChange({ ...reported, veins: v })} />
            {/* Diameter — read from cord, shown as read-only */}
          {cord.diameter > 0 && (
            <Stack direction="row" alignItems="center" justifyContent="space-between" mt={0.5}>
              <Typography fontSize={12} color="text.secondary">Diameter</Typography>
              <Stack direction="row" alignItems="center" gap={0.5}>
                <Typography fontWeight={600} fontSize={13}>{Math.round(cord.diameter)}</Typography>
                <Typography fontSize={11} color="text.disabled">px</Typography>
              </Stack>
            </Stack>
          )}

          <Select size="small" fullWidth value={activeDiag}
            onChange={e => onReportedChange({
              ...reported,
              diagnosticOverride: e.target.value === repDiag ? null : e.target.value as 'Normal' | 'SUA' | 'Uncertain',
            })}
            sx={{
              mt: 1, fontSize: 11, fontWeight: 700,
              color: diagText(activeDiag),
              bgcolor: diagBg(activeDiag),
              '& .MuiOutlinedInput-notchedOutline': { borderColor: diagBorder(activeDiag) },
            }}
          >
            <MenuItem value="Normal">Normal</MenuItem>
            <MenuItem value="SUA">SUA</MenuItem>
            <MenuItem value="Uncertain">Uncertain</MenuItem>
          </Select>
        </Box>
      </Stack>
    </Box>
  );
}

export default function DiagnosisPanel({
  polygons, onPolygonsChange, hoveredCordIndex, onCordHover,
  reportedCounts, onReportedCountsChange, onAddCord, onDeleteCord,
}: PanelProps) {
  return (
    <Card variant="outlined" sx={{ width: '100%', minWidth: 300, borderRadius: 2, overflow: 'visible', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Stack direction="row" alignItems="center" justifyContent="space-between"
        sx={{ px: 2, py: 1.25, bgcolor: '#1a1a1a', flexShrink: 0 }}>
        <Stack direction="row" alignItems="center" gap={1}>
          <LightbulbIcon sx={{ color: 'white', fontSize: 16 }} />
          <Typography fontSize={13} fontWeight={600} color="white">AI Findings</Typography>
        </Stack>
        <Button size="small" startIcon={<AddIcon />} onClick={onAddCord}
          sx={{ color: 'white', borderColor: '#555', fontSize: 11, textTransform: 'none', border: '1px solid #555', px: 1 }}>
          Add Cord
        </Button>
      </Stack>

      {/* Cord cards */}
      {polygons.length === 0
        ? <Box sx={{ px: 2, py: 3 }}><Typography fontSize={13} color="text.disabled">No cords detected</Typography></Box>
        : polygons.map((cord, i) => (
          <Box key={i}>
            <CordCard
              index={i}
              cord={cord}
              reported={reportedCounts[i] ?? { arteries: 0, veins: 0 }}
              isHovered={hoveredCordIndex === i}
              onReportedChange={u => onReportedCountsChange(reportedCounts.map((r, j) => j === i ? u : r))}
              onCordChange={u => onPolygonsChange(polygons.map((c, j) => j === i ? u : c))}
              onDelete={() => onDeleteCord(i)}
              onMouseEnter={() => onCordHover(i)}
              onMouseLeave={() => onCordHover(null)}
            />
            {i < polygons.length - 1 && <Divider />}
          </Box>
        ))
      }
    </Card>
  );
}