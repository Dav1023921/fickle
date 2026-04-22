import { useState, useEffect } from 'react';
import Card from '@mui/material/Card';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import Divider from '@mui/material/Divider';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import LightbulbIcon from '@mui/icons-material/Lightbulb';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';

type VesselInfo = {
  polygon: number[];
  area: number;
  type: string;
};

type CordPolygon = {
  polygon: number[];
  vessels: VesselInfo[];
  diameter: number;
  confidence: number;  // add this
};

export interface PipelineOutput {
  polygons: CordPolygon[];
  number_of_cords: number;
  sua: boolean;
  diagnostic: 'Normal' | 'SUA' | 'Uncertain';
  confidence: number;  // add this
}

interface PanelProps {
  pipelineOutput?: PipelineOutput;
}

// ─── types ────────────────────────────────────────────────────────────────────

interface CordState {
  arteries: number;
  veins: number;
  diameter: number;
  diagnostic: 'Normal' | 'SUA' | 'Uncertain';
  confidence: number;  
}

// ─── helpers ──────────────────────────────────────────────────────────────────

function cordDiagnostic(arteries: number, veins: number): 'Normal' | 'SUA' | 'Uncertain' {
  if (arteries === 2 && veins === 1) return 'Normal';
  if (arteries === 1 && veins === 1) return 'SUA';
  return 'Uncertain';
}

function buildCordStates(polygons: CordPolygon[]): CordState[] {
  return polygons.map(cord => {
    const arteries = cord.vessels.filter(v => v.type === 'Artery').length;
    const veins    = cord.vessels.filter(v => v.type === 'Vein').length;
    return {
      arteries,
      veins,
      diameter: Math.round(cord.diameter),
      diagnostic: cordDiagnostic(arteries, veins),
      confidence: cord.confidence,  // add this
    };
  });
}

const diagnosticColor = (d?: string) =>
  d === 'Normal' ? 'success.main' : d === 'SUA' ? 'error.main' : 'warning.main';

// ─── editable row ─────────────────────────────────────────────────────────────

const EditableRow = ({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) => (
  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 0.5 }}>
    <Typography variant="body2" color="text.secondary">{label}</Typography>
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
      <Box
        component="input"
        type="number"
        value={value}
        onChange={(e) => onChange(Math.max(0, parseInt(e.target.value) || 0))}
        sx={{
          bgcolor: 'grey.100',
          borderRadius: 1,
          px: 1.5,
          py: 0.25,
          width: 64,
          textAlign: 'center',
          border: 'none',
          outline: 'none',
          fontFamily: 'inherit',
          color: 'text.primary',
          fontSize: '0.875rem',
          fontWeight: 500,
          cursor: 'text',
          '&:focus': { bgcolor: 'grey.200', outline: '2px solid', outlineColor: 'primary.main' },
          '&::-webkit-inner-spin-button': { display: 'none' },
          '&::-webkit-outer-spin-button': { display: 'none' },
        }}
      />
      <Box sx={{ display: 'flex', flexDirection: 'column' }}>
        <IconButton size="small" sx={{ p: 0 }} onClick={() => onChange(value + 1)}>
          <KeyboardArrowUpIcon fontSize="small" />
        </IconButton>
        <IconButton size="small" sx={{ p: 0 }} onClick={() => onChange(Math.max(0, value - 1))}>
          <KeyboardArrowDownIcon fontSize="small" />
        </IconButton>
      </Box>
    </Box>
  </Box>
);

const DiameterRow = ({ value, onChange }: { value: number; onChange: (v: number) => void }) => (
  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 0.5 }}>
    <Typography variant="body2" color="text.secondary">Diameter</Typography>
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', bgcolor: 'grey.100', borderRadius: 1, px: 1.5, py: 0.25 }}>
        <Box
          component="input"
          type="number"
          value={value}
          onChange={(e) => onChange(Math.max(0, parseInt(e.target.value) || 0))}
          sx={{
            bgcolor: 'transparent',
            border: 'none',
            outline: 'none',
            fontFamily: 'inherit',
            fontSize: '0.875rem',
            fontWeight: 500,
            width: 48,
            color: 'text.primary',
            textAlign: 'center',
            '&::-webkit-inner-spin-button': { display: 'none' },
            '&::-webkit-outer-spin-button': { display: 'none' },
          }}
        />
        <Typography variant="body2" fontWeight={500}>px</Typography>
      </Box>
      <Box sx={{ display: 'flex', flexDirection: 'column' }}>
        <IconButton size="small" sx={{ p: 0 }} onClick={() => onChange(value + 1)}>
          <KeyboardArrowUpIcon fontSize="small" />
        </IconButton>
        <IconButton size="small" sx={{ p: 0 }} onClick={() => onChange(Math.max(0, value - 1))}>
          <KeyboardArrowDownIcon fontSize="small" />
        </IconButton>
      </Box>
    </Box>
  </Box>
);

// ─── cord section ─────────────────────────────────────────────────────────────

interface CordSectionProps {
  index: number;
  cord: CordState;
  onChange: (updated: CordState) => void;
}

const CordSection = ({ index, cord, onChange }: CordSectionProps) => {
  const handleArteries = (v: number) => {
    const updated = { ...cord, arteries: v, diagnostic: cordDiagnostic(v, cord.veins) };
    onChange(updated);
  };
  const handleVeins = (v: number) => {
    const updated = { ...cord, veins: v, diagnostic: cordDiagnostic(cord.arteries, v) };
    onChange(updated);
  };
  const handleDiameter = (v: number) => onChange({ ...cord, diameter: v });

  return (
       <Box sx={{ px: 2.5, py: 2 }}>
      {/* cord header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1.5}>
        <Typography variant="caption" fontWeight={600} color="text.secondary"
          sx={{ textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          Cord {index + 1}
        </Typography>
        <Typography variant="body2" fontWeight={600} color={diagnosticColor(cord.diagnostic)}>
          {cord.diagnostic}
        </Typography>
      </Stack>

      <EditableRow label="Arteries" value={cord.arteries} onChange={handleArteries} />
      <EditableRow label="Veins"    value={cord.veins}    onChange={handleVeins} />
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 0.5 }}>
        <Typography variant="body2" color="text.secondary">Total vessels</Typography>
        <Box sx={{ bgcolor: 'grey.100', borderRadius: 1, px: 1.5, py: 0.25, minWidth: 64, textAlign: 'center' }}>
          <Typography variant="body2" fontWeight={500}>{cord.arteries + cord.veins}</Typography>
        </Box>
      </Box>
      <DiameterRow value={cord.diameter} onChange={handleDiameter} />

      {/* cord confidence */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 0.5 }}>
        <Typography variant="body2" color="text.secondary">Confidence</Typography>
        <Box sx={{ bgcolor: 'grey.100', borderRadius: 1, px: 1.5, py: 0.25, minWidth: 64, textAlign: 'center' }}>
          <Typography variant="body2" fontWeight={500}>
            {Math.round(cord.confidence * 100)}%
          </Typography>
        </Box>
      </Box>
    </Box>
  );
};

// ─── panel ────────────────────────────────────────────────────────────────────

const Panel = ({ pipelineOutput }: PanelProps) => {
  const [cords, setCords] = useState<CordState[]>([]);

  useEffect(() => {
    setCords(buildCordStates(pipelineOutput?.polygons ?? []));
  }, [pipelineOutput]);

  const handleCordChange = (i: number, updated: CordState) => {
    setCords(prev => prev.map((c, j) => j === i ? updated : c));
  };

  return (
    <Card variant="outlined" sx={{ width: '100%', minWidth: 320, maxWidth: 460, borderRadius: 2, overflowY: 'auto' }}>

      {/* header */}
      <Box sx={{ bgcolor: '#1a1a1a', px: 2, py: 1.25 }}>
        <Stack direction="row" spacing={1} alignItems="center">
          <LightbulbIcon fontSize="small" sx={{ color: 'white' }} />
          <Typography variant="body2" fontWeight={500} sx={{ color: 'white' }}>
            AI Findings
          </Typography>
        </Stack>
      </Box>

      {/* per cord sections */}
      {cords.length === 0
        ? <Box sx={{ px: 2.5, py: 2 }}>
            <Typography variant="body2" color="text.disabled">No cords detected</Typography>
          </Box>
        : cords.map((cord, i) => (
            <Box key={i}>
              <CordSection index={i} cord={cord} onChange={(u) => handleCordChange(i, u)} />
              {i < cords.length - 1 && <Divider />}
            </Box>
          ))
      }
      <Divider />
  </Card>
  );
};

export default Panel;