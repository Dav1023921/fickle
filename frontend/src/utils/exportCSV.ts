import type { CordPolygon, ReportedCounts } from '../CasesContext';
 
type Diagnostic = 'Normal' | 'SUA' | 'Uncertain';
 
function cordDiagnostic(arteries: number, veins: number): Diagnostic {
  if (arteries === 2 && veins === 1) return 'Normal';
  if (arteries === 1 && veins === 1) return 'SUA';
  return 'Uncertain';
}
 
export function exportCSV(
  filename: string,
  overallDiagnostic: Diagnostic,
  polygons: CordPolygon[],
  reportedCounts: ReportedCounts[],
) {
  const rows: string[][] = [];
 
  // Header row
  rows.push(['Case', 'Date', 'Overall Diagnosis', 'Cord', 'Reported Arteries', 'Reported Veins', 'Diameter (px)', 'Cord Diagnosis', 'AI Arteries', 'AI Veins']);
 
  const date = new Date().toLocaleDateString('en-GB');
 
  reportedCounts.forEach((rc, i) => {
    const cord       = polygons[i];
    const aiArteries = cord?.vessels.filter(v => v.type === 'Artery').length ?? '—';
    const aiVeins    = cord?.vessels.filter(v => v.type === 'Vein').length ?? '—';
    const diameter   = cord ? Math.round(cord.diameter) : '—';
    const diag       = cordDiagnostic(rc.arteries, rc.veins);
 
    rows.push([
      filename,
      date,
      overallDiagnostic,
      `Cord ${i + 1}`,
      String(rc.arteries),
      String(rc.veins),
      String(diameter),
      diag,
      String(aiArteries),
      String(aiVeins),
    ]);
  });
 
  const csv     = rows.map(r => r.join(',')).join('\n');
  const blob    = new Blob([csv], { type: 'text/csv' });
  const url     = URL.createObjectURL(blob);
  const a       = document.createElement('a');
  a.href        = url;
  a.download    = `fickle_${filename.replace(/\.[^.]+$/, '')}_${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}