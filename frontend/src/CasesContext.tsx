import { createContext, useContext, useState } from 'react'

// ─── result types ─────────────────────────────────────────────────────────────

export type VesselInfo = {
  polygon: number[];
  type: string;
  confidence?: number;
};

export type CordInfo = {
  polygon: number[];
  vessels: VesselInfo[];
  diameter: number;
  confidence: number;
  start_end_points?: [[number, number], [number, number]];
};

export type PipelineResult = {
  polygons: CordInfo[];
  number_of_cords: number;
  sua: boolean;
  diagnostic: 'Normal' | 'SUA' | 'Uncertain';
  confidence: number;
};

// ─── editable state per case ──────────────────────────────────────────────────
// Stored separately from the raw pipeline result so we never mutate the
// original model output — edits are always an overlay on top of it.

export type ReportedCounts = {
  arteries: number;
  veins: number;
  diagnosticOverride?: 'Normal' | 'SUA' | 'Uncertain' | null;
};

export type CaseEdits = {
  polygons: CordPolygon[];
  reportedCounts: ReportedCounts[];
  diagnosticOverride: 'Normal' | 'SUA' | 'Uncertain' | null;
  reviewedAt: string | null; // ISO timestamp, null = not reviewed
};

// ─── case types ───────────────────────────────────────────────────────────────

export type CaseStatus = 'staged' | 'complete';

export type Case = {
  id: string;
  filename: string;
  imageUrl: string;
  status: CaseStatus;
  file: File;
  result?: PipelineResult;
  edits?: CaseEdits;
};

// ─── context ──────────────────────────────────────────────────────────────────

type CasesContextType = {
  cases: Case[];
  setCases: React.Dispatch<React.SetStateAction<Case[]>>;
  updateCaseEdits: (id: string, edits: Partial<CaseEdits>) => void;
  initCaseEdits: (id: string) => void;
};

const CasesContext = createContext<CasesContextType | null>(null);

export const CasesProvider = ({ children }: { children: React.ReactNode }) => {
  const [cases, setCases] = useState<Case[]>([]);

  // Initialise edits for a case from its pipeline result (called on first visit)
  function initCaseEdits(id: string) {
    setCases(prev => prev.map(c => {
      if (c.id !== id || c.edits || !c.result) return c;
      return {
        ...c,
        edits: {
          polygons: c.result.polygons,
          reportedCounts: c.result.polygons.map(cord => ({
            arteries: cord.vessels.filter(v => v.type === 'Artery').length,
            veins:    cord.vessels.filter(v => v.type === 'Vein').length,
          })),
          diagnosticOverride: null,
          reviewedAt: null,
        },
      };
    }));
  }

  // Merge a partial edit update into the existing edits for a case
  function updateCaseEdits(id: string, edits: Partial<CaseEdits>) {
    setCases(prev => prev.map(c => {
      if (c.id !== id) return c;
      return {
        ...c,
        edits: { ...c.edits!, ...edits },
      };
    }));
  }

  return (
    <CasesContext.Provider value={{ cases, setCases, updateCaseEdits, initCaseEdits }}>
      {children}
    </CasesContext.Provider>
  );
};

export const useCases = () => {
  const ctx = useContext(CasesContext);
  if (!ctx) throw new Error('useCases must be used inside CasesProvider');
  return ctx;
};