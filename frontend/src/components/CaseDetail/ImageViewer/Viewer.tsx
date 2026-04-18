import { useEffect, useRef, useState } from "react";
import useImage from "use-image";
import Konva from "konva";
import { Stage, Layer, Image as KonvaImage, Line, Circle } from "react-konva";
import { Box, Button, Typography, List, ListItem, ListItemText, Divider } from "@mui/material";

// ─── types ────────────────────────────────────────────────────────────────────

type Vessel = {
  polygon: number[];
  area: number;
  type: "Artery" | "Vein";
  heatmap?: string;
};

type Cord = {
  polygon: number[];
  vessels: Vessel[];
  diameter: number;
  confidence: number;
  heatmap?: string;
};

type FlatEntry = {
  id: string;
  cordIndex: number;
  vesselIndex: number | null;
  points: number[];
  stroke: string;
  fill: string;
  label: string;
  detail: string;
};

// ─── helpers ──────────────────────────────────────────────────────────────────

function toXY(pts: number[]): { x: number; y: number }[] {
  const result = [];
  for (let i = 0; i < pts.length; i += 2)
    result.push({ x: pts[i], y: pts[i + 1] });
  return result;
}

function toFlat(pts: { x: number; y: number }[]): number[] {
  return pts.flatMap(p => [p.x, p.y]);
}

function flatten(cords: Cord[]): FlatEntry[] {
  const result: FlatEntry[] = [];
  for (let ci = 0; ci < cords.length; ci++) {
    const cord = cords[ci];
    result.push({
      id: `c${ci}`, cordIndex: ci, vesselIndex: null,
      points: cord.polygon, stroke: "#3b82f6", fill: "rgba(59,130,246,0.08)",
      label: `Cord ${ci + 1}`, detail: `Diameter: ${Math.round(cord.diameter)}px`,
    });
    for (let vi = 0; vi < cord.vessels.length; vi++) {
      const vessel = cord.vessels[vi];
      const isArtery = vessel.type === "Artery";
      result.push({
        id: `c${ci}v${vi}`, cordIndex: ci, vesselIndex: vi,
        points: vessel.polygon,
        stroke: isArtery ? "#ef4444" : "#3b82f6",
        fill: isArtery ? "rgba(239,68,68,0.12)" : "rgba(59,130,246,0.12)",
        label: `Cord ${ci + 1} — ${vessel.type} ${vi + 1}`,
        detail: `Area: ${Math.round(vessel.area)}px²`,
      });
    }
  }
  return result;
}

// ─── editable polygon ─────────────────────────────────────────────────────────

type PolygonProps = {
  entry: FlatEntry; strokeWidth: number; editing: boolean;
  selected: boolean; onChange: (pts: number[]) => void; onSelect: () => void;
};

function EditablePolygon({ entry, strokeWidth, editing, selected, onChange, onSelect }: PolygonProps) {
  const [pts, setPts] = useState(toXY(entry.points));
  useEffect(() => { setPts(toXY(entry.points)); }, [entry.points]);

  function handleDrag(index: number, x: number, y: number) {
    const updated = pts.map((p, i) => (i === index ? { x, y } : p));
    setPts(updated);
    onChange(toFlat(updated));
  }

  return (
    <>
      <Line points={toFlat(pts)} closed
        stroke={selected ? "#facc15" : entry.stroke}
        strokeWidth={selected ? strokeWidth * 2.5 : strokeWidth}
        fill={entry.fill} onClick={onSelect} onTap={onSelect}
      />
      {editing && pts.map((pt, i) => (
        <Circle key={i} x={pt.x} y={pt.y} radius={6 / (strokeWidth * 3)}
          fill={entry.stroke} opacity={0.9} draggable
          onDragMove={(e) => handleDrag(i, e.target.x(), e.target.y())}
        />
      ))}
    </>
  );
}

// ─── heatmap grid ─────────────────────────────────────────────────────────────

function HeatmapGrid({ cords }: { cords: Cord[] }) {
  const items: { label: string; src?: string }[] = [];

  cords.forEach((cord, ci) => {
    cord.vessels.forEach((vessel, vi) => {
      items.push({ label: `Cord ${ci + 1} — ${vessel.type} ${vi + 1}`, src: vessel.heatmap });
    });
  });

  return (
    <Box sx={{ p: 2, overflowY: 'auto', height: '100%', display: 'flex', flexWrap: 'wrap', gap: 2, alignContent: 'flex-start' }}>
      {items.map((item, i) => (
        <Box key={i} sx={{ width: 140, textAlign: 'center' }}>
          {item.src
            ? <img src={item.src} alt={item.label} style={{ width: '100%', display: 'block' }} />
            : <Box sx={{ height: 120, bgcolor: 'grey.100', borderRadius: 2, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Typography variant="caption" color="text.disabled">No heatmap</Typography>
              </Box>
          }
          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
            {item.label}
          </Typography>
        </Box>
      ))}
    </Box>
  );
}

// ─── main viewer ──────────────────────────────────────────────────────────────

const ZOOM_BY = 1.05;

type Props = {
  imageUrl?: string;
  polygons?: Cord[];
};

function Viewer({ imageUrl, polygons = [] }: Props) {
  const stageRef     = useRef<Konva.Stage | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const [image] = useImage(imageUrl ?? "", "anonymous");

  const [fitScale, setFitScale]         = useState(1);
  const [zoom, setZoom]                 = useState(1);
  const [dims, setDims]                 = useState({ width: 800, height: 600 });
  const [showPolygons, setShowPolygons] = useState(true);
  const [showHeatmaps, setShowHeatmaps] = useState(false);
  const [editing, setEditing]           = useState(false);
  const [cords, setCords]               = useState<Cord[]>(polygons);
  const [selectedId, setSelectedId]     = useState<string | null>(null);

  useEffect(() => { setCords(polygons); }, [polygons]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new ResizeObserver((entries) => {
      const rect = entries[0].contentRect;
      setDims({ width: rect.width, height: rect.height });
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  function centerImage(img: HTMLImageElement, fit: number, z: number = 1) {
    const stage = stageRef.current;
    if (!stage) return;
    const scale = fit * z;
    stage.scale({ x: scale, y: scale });
    stage.position({
      x: (dims.width - img.width * scale) / 2,
      y: (dims.height - img.height * scale) / 2,
    });
    stage.batchDraw();
  }

  useEffect(() => {
    if (!image) return;
    const fit = Math.min(dims.width / image.width, dims.height / image.height);
    setFitScale(fit);
    setZoom(1);
    centerImage(image, fit, 1);
  }, [image, dims]);

  function handleWheel(e: Konva.KonvaEventObject<WheelEvent>) {
    e.evt.preventDefault();
    if (!image) return;
    const newZoom = Math.max(1, Math.min(2, e.evt.deltaY > 0 ? zoom / ZOOM_BY : zoom * ZOOM_BY));
    const oldScale = fitScale * zoom;
    const newScale = fitScale * newZoom;
    const cx = dims.width / 2;
    const cy = dims.height / 2;
    const pos = stageRef.current!.position();
    const pointTo = { x: (cx - pos.x) / oldScale, y: (cy - pos.y) / oldScale };
    setZoom(newZoom);
    stageRef.current!.scale({ x: newScale, y: newScale });
    stageRef.current!.position({ x: cx - pointTo.x * newScale, y: cy - pointTo.y * newScale });
    stageRef.current!.batchDraw();
  }

  function updatePolygon(entry: FlatEntry, pts: number[]) {
    setCords((prev) =>
      prev.map((cord, ci) => {
        if (ci !== entry.cordIndex) return cord;
        if (entry.vesselIndex === null) return { ...cord, polygon: pts };
        return { ...cord, vessels: cord.vessels.map((v, vi) => vi === entry.vesselIndex ? { ...v, polygon: pts } : v) };
      })
    );
  }

  function toggleSelect(id: string) {
    setSelectedId(id === selectedId ? null : id);
  }

  const flat = flatten(cords);
  const strokeWidth = 2 / (fitScale * zoom);
  const btn = { color: "white", borderColor: "#444" };

  if (!image) return null;

  return (
    <Box sx={{ display: "flex", flexDirection: "column", width: "100%", height: "100%", border: "1px solid", borderColor: "divider", borderRadius: 2, overflow: "hidden" }}>

      {/* toolbar */}
      <Box sx={{ display: "flex", gap: 1, px: 1.5, height: 48, alignItems: "center", bgcolor: "#1a1a1a", flexShrink: 0 }}>
        <Button size="small" variant="outlined" sx={btn} onClick={() => { setZoom(1); centerImage(image, fitScale, 1); }}>
          Reset View
        </Button>
        <Button size="small" variant="outlined" sx={btn} onClick={() => setShowPolygons(p => !p)}>
          {showPolygons ? "Hide Polygons" : "Show Polygons"}
        </Button>
        <Button size="small" variant="outlined" sx={btn} onClick={() => setShowHeatmaps(p => !p)}>
          {showHeatmaps ? "Hide Heatmaps" : "Heatmaps"}
        </Button>
        <Box sx={{ flex: 1 }} />
        {editing
          ? <Button size="small" variant="outlined" sx={btn} onClick={() => { setEditing(false); setCords(polygons); }}>Cancel</Button>
          : <Button size="small" variant="outlined" sx={btn} onClick={() => setEditing(true)}>Edit Polygons</Button>
        }
      </Box>

      {/* canvas or heatmap grid */}
      <Box ref={containerRef} sx={{ flex: 1, overflow: "hidden", minHeight: 0 }}>
        {showHeatmaps
          ? <HeatmapGrid cords={cords} />
          : (
            <Stage ref={stageRef} width={dims.width} height={dims.height} draggable={!editing} onWheel={handleWheel}>
              <Layer>
                <KonvaImage image={image} x={0} y={0} width={image.width} height={image.height} />
              </Layer>
              {showPolygons && (
                <Layer>
                  {flat.map((e) => (
                    <EditablePolygon key={e.id} entry={e} strokeWidth={strokeWidth}
                      editing={editing} selected={selectedId === e.id}
                      onChange={(pts) => updatePolygon(e, pts)}
                      onSelect={() => toggleSelect(e.id)}
                    />
                  ))}
                </Layer>
              )}
            </Stage>
          )
        }
      </Box>

      {/* polygon list */}
      {!showHeatmaps && (
        <Box sx={{ height: 220, borderTop: "1px solid", borderColor: "divider", overflowY: "auto", flexShrink: 0 }}>
          <List dense disablePadding>
            {flat.map((e) => (
              <>
                <ListItem key={e.id} onClick={() => toggleSelect(e.id)}
                  sx={{ cursor: "pointer", bgcolor: selectedId === e.id ? "primary.50" : "white" }}>
                  <Box sx={{ width: 9, height: 9, borderRadius: "50%", bgcolor: e.stroke, mr: 1.5, flexShrink: 0 }} />
                  <ListItemText primary={e.label} secondary={e.detail}
                    slotProps={{ primary: { style: { fontSize: 13 } }, secondary: { style: { fontSize: 11 } } }}
                  />
                </ListItem>
                <Divider />
              </>
            ))}
          </List>
        </Box>
      )}

    </Box>
  );
}

export default Viewer;