import { useEffect, useState } from 'react';
import Navbar from '../components/Navbar';
import Panel from '../components/CaseDetail/DiagnosisPanel';
import Viewer from '../components/CaseDetail/ImageViewer';
import { Box } from '@mui/material';
import ToolPanel from '../components/CaseDetail/ToolPanel';
import { useParams, useNavigate } from 'react-router-dom';
import { useCases } from '../CasesContext';
import type { CordInfo, ReportedCounts } from '../CasesContext';

export default function CaseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { cases, updateCaseEdits, initCaseEdits } = useCases();
  const currentCase = cases.find(c => c.id === id);

  const [hoveredCordIndex, setHoveredCordIndex] = useState<number | null>(null);

  useEffect(() => {
    if (id) initCaseEdits(id);
  }, [id]);

  const polygons: CordInfo[] = currentCase?.edits?.polygons
    ?? currentCase?.result?.polygons
    ?? [];

  const reportedCounts: ReportedCounts[] = currentCase?.edits?.reportedCounts
    ?? polygons.map(cord => ({
      arteries: cord.vessels.filter(v => v.type === 'Artery').length,
      veins:    cord.vessels.filter(v => v.type === 'Vein').length,
    }));

  const diagnosticOverride = currentCase?.edits?.diagnosticOverride ?? null;
  const reviewed = !!currentCase?.edits?.reviewedAt;

  function handlePolygonsChange(updated: CordInfo[]) {
    if (id) updateCaseEdits(id, { polygons: updated });
  }

  function handleReportedCountsChange(updated: ReportedCounts[]) {
    if (id) updateCaseEdits(id, { reportedCounts: updated });
  }

  function handleAddCord() {
    const newCord: CordInfo = { polygon: [], vessels: [], diameter: 0, confidence: 0 };
    const newPolygons = [...polygons, newCord];
    const newCounts   = [...reportedCounts, { arteries: 0, veins: 0 }];
    if (id) updateCaseEdits(id, { polygons: newPolygons, reportedCounts: newCounts });
  }

  function handleDeleteCord(index: number) {
    const newPolygons = polygons.filter((_, i) => i !== index);
    const newCounts   = reportedCounts.filter((_, i) => i !== index);
    if (id) updateCaseEdits(id, { polygons: newPolygons, reportedCounts: newCounts });
  }

  function handleDiagnosticOverride(val: 'Normal' | 'SUA' | 'Uncertain' | null) {
    if (id) updateCaseEdits(id, { diagnosticOverride: val });
  }

  function handleMarkReviewed() {
    if (id) updateCaseEdits(id, { reviewedAt: new Date().toISOString() });
  }

  function handleUnmarkReviewed() {
    if (id) updateCaseEdits(id, { reviewedAt: null });
  }

  return (
    <>
      <Navbar label="Home" />
      <Box display="flex" flexDirection="row" gap={2} padding={2}
        sx={{ height: 'calc(100vh - 64px)', overflow: 'hidden' }}>

        <Box sx={{ flex: 1, minWidth: 0, minHeight: 0, display: 'flex' }}>
          <Viewer
          imageUrl={currentCase?.imageUrl}
          polygons={polygons}
          hoveredCordIndex={hoveredCordIndex}
          onPolygonsChange={handlePolygonsChange}
          onFeretChange={() => {}}
          onAddCord={(cord) => {
            const newCounts   = [...reportedCounts, {
              arteries: cord.vessels.filter(v => v.type === 'Artery').length,
              veins:    cord.vessels.filter(v => v.type === 'Vein').length,
            }];
            if (id) updateCaseEdits(id, {reportedCounts: newCounts });
          }}
          />
        </Box>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, flex: 1, minWidth: 0, height: '100%' }}>
          <Box sx={{ flex: 1, minHeight: 0, overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
            <Panel
              polygons={polygons}
              onPolygonsChange={handlePolygonsChange}
              pipelineOutput={currentCase?.result}
              hoveredCordIndex={hoveredCordIndex}
              onCordHover={setHoveredCordIndex}
              reportedCounts={reportedCounts}
              onReportedCountsChange={handleReportedCountsChange}
              onAddCord={handleAddCord}
              onDeleteCord={handleDeleteCord}
            />
          </Box>
          <ToolPanel
            polygons={polygons}
            reportedCounts={reportedCounts}
            diagnosticOverride={diagnosticOverride}
            reviewed={reviewed}
            onDiagnosticOverride={handleDiagnosticOverride}
            onMarkReviewed={handleMarkReviewed}
            onUnmarkReviewed={handleUnmarkReviewed}
            onGoBack={() => navigate('/')}
          />
        </Box>

      </Box>
    </>
  );
}