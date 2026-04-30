import { useState } from 'react';
import { Box, Typography, Button, Table, TableHead, TableBody, TableRow, TableCell, Chip } from '@mui/material';
import UploadBar from './UploadBar';
import { theme } from '../../theme';
import { useCases, type Case, type CaseStatus } from '../../CasesContext';
import { useNavigate } from 'react-router-dom';

// Derive the overall diagnosis from edits if available, otherwise fall back to pipeline result
function getDisplayDiagnostic(c: Case): string {
  if (!c.result) return '—';
  // If pathologist has overridden the diagnosis, use that
  if (c.edits?.diagnosticOverride) return c.edits.diagnosticOverride;
  // If reported counts exist, derive from them
  if (c.edits?.reportedCounts?.length) {
    const counts = c.edits.reportedCounts;
    const hasSUA     = counts.some(r => r.arteries === 1 && r.veins === 1);
    const allNormal  = counts.every(r => r.arteries === 2 && r.veins === 1);
    if (hasSUA)    return 'SUA';
    if (allNormal) return 'Normal';
    return 'Uncertain';
  }
  return c.result.diagnostic ?? '—';
}

const diagnosticColor = (d: string) =>
  d === 'Normal' ? 'success' : d === 'SUA' ? 'error' : 'warning';

const MainPanel = () => {
  const { cases, setCases } = useCases();
  const navigate = useNavigate();
  const [analysing, setAnalysing] = useState(false);

  const staged   = cases.filter(c => c.status === 'staged');
  const toReview = cases.filter(c => c.status === 'complete');

  const handleFilesAdded = (files: FileList) => {
    const existingFilenames = cases.map(c => c.filename);
    const newCases: Case[] = Array.from(files)
      .filter(file => !existingFilenames.includes(file.name))
      .map(file => ({
        id: crypto.randomUUID(),
        filename: file.name,
        imageUrl: URL.createObjectURL(file),
        status: 'staged' as const,
        file,
      }));
    setCases(prev => [...prev, ...newCases]);
  };

  const handleRunAll = async () => {
    setAnalysing(true);
    for (const c of staged) {
      const formData = new FormData();
      formData.append('file', c.file);
      try {
        const res    = await fetch('http://localhost:8003/analyse', { method: 'POST', body: formData });
        const result = await res.json();
        setCases(prev => prev.map(x => x.id === c.id ? { ...x, status: 'complete' as CaseStatus, result } : x));
      } catch (err) {
        console.error('Failed to analyse', c.filename, err);
      }
    }
    setAnalysing(false);
  };

  return (
    <Box sx={{ width: '90%', bgcolor: theme.palette.background.default, display: 'flex', flexDirection: 'column' }}>

      <UploadBar onFilesAdded={handleFilesAdded} />

      {/* staged files */}
      <Box sx={{ backgroundColor: '#e0e0e0', borderRadius: 1, padding: 2, minHeight: 180, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
        <Typography>Selected Files</Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
          {staged.map(c => (
            <Box key={c.id} sx={{ display: 'flex', alignItems: 'center', bgcolor: 'white', borderRadius: 1, padding: '4px 8px' }}>
              <Typography variant="caption">{c.filename}</Typography>
            </Box>
          ))}
        </Box>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
          <Button variant="contained" color="primary" disabled={staged.length === 0 || analysing} onClick={handleRunAll}>
            {analysing ? 'Analysing...' : 'Analyse All'}
          </Button>
        </Box>
      </Box>

      {/* cases table */}
      <Box sx={{ mt: 3 }}>
        <Table>
          <TableHead sx={{ backgroundColor: '#f5f5f5' }}>
            <TableRow>
              <TableCell>Case Number</TableCell>
              <TableCell>Diagnosis</TableCell>
              <TableCell>Reviewed</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {toReview.map((c, i) => {
              const diagnosis = getDisplayDiagnostic(c);
              const reviewed  = !!c.edits?.reviewedAt;
              return (
                <TableRow key={c.id} hover sx={{ cursor: 'pointer' }} onClick={() => navigate(`/cases/${c.id}`)}>
                  <TableCell>#{i + 1} {c.filename}</TableCell>
                  <TableCell>
                    {diagnosis === '—'
                      ? '—'
                      : <Chip
                          label={diagnosis}
                          size="small"
                          color={diagnosticColor(diagnosis) as any}
                          variant="outlined"
                        />
                    }
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={reviewed ? 'YES' : 'NO'}
                      size="small"
                      color={reviewed ? 'success' : 'default'}
                      variant={reviewed ? 'filled' : 'outlined'}
                    />
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </Box>
    </Box>
  );
};

export default MainPanel;