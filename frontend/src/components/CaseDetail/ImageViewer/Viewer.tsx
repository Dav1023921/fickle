import { useEffect, useRef, useState } from "react";
import useImage from "use-image";
import Konva from "konva";
import { Stage, Layer, Image as KonvaImage, Line, Circle, Text } from "react-konva";
import { Box, Button, Typography } from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import RemoveIcon from "@mui/icons-material/Remove";
import { toXY, toFlat, euclidean, farthestPair } from "./viewerUtils";
import type { CordPolygon as Cord} from "../../../CasesContext";

const COLOUR_BLUE          = "#3b82f6";
const COLOUR_RED           = "#ef4444";
const COLOUR_YELLOW        = "#facc15";
const COLOUR_CYAN          = "#00e5ff";
const COLOUR_WHITE         = "#ffffff";

const FILL_BLUE_FAINT      = "rgba(59,130,246,0.08)";
const FILL_BLUE_VESSEL     = "rgba(59,130,246,0.12)";
const FILL_RED_VESSEL      = "rgba(239,68,68,0.12)";
const FILL_YELLOW_SELECTED = "rgba(250,204,21,0.10)";

const CONF_HIGH   = "#16a34a";
const CONF_MED    = "#d97706";
const CONF_LOW    = "#dc2626";

type FlatEntry = {
  id: string;
  cordIndex: number;
  vesselIndex: number | null;
  points: number[];
  stroke: string;
  fill: string;
  lowConfidence: boolean;
};

function flatten(cords: Cord[]): FlatEntry[] {
  const result: FlatEntry[] = [];
  for (let ci = 0; ci < cords.length; ci++) {
    const cord = cords[ci];
    result.push({
      id: `c${ci}`,
      cordIndex: ci,
      vesselIndex: null,
      points: cord.polygon,
      stroke: COLOUR_BLUE,
      fill: FILL_BLUE_FAINT,
      lowConfidence: false,
    });
    for (let vi = 0; vi < cord.vessels.length; vi++) {
      const vessel = cord.vessels[vi];
      const isArtery = vessel.type === "Artery";
      const lowConf  = vessel.confidence !== undefined && vessel.confidence < 0.8;
      result.push({
        id: `c${ci}v${vi}`,
        cordIndex: ci,
        vesselIndex: vi,
        points: vessel.polygon,
        stroke: isArtery ? COLOUR_RED : COLOUR_BLUE,
        fill:   isArtery ? FILL_RED_VESSEL : FILL_BLUE_VESSEL,
        lowConfidence: lowConf,
      });
    }
  }
  return result;
}

type PolygonProps = {
  entry: FlatEntry;
  strokeWidth: number;
  editingCordIndex: number | null;
  editingVesselKey: string | null;
  selectedKey: string | null;
  highlighted: boolean;
  fitScale: number;
  zoom: number;
  feretPickMode: boolean;
  feretPickedIndices: number[];
  onChange: (pts: number[]) => void;
  onCordClick: (cordIndex: number, screenX: number, screenY: number) => void;
  onVesselClick: (cordIndex: number, vesselIndex: number, screenX: number, screenY: number) => void;
  onFeretPointClick: (pointIndex: number) => void;
};

function EditablePolygon({
  entry, strokeWidth, editingCordIndex, editingVesselKey, selectedKey, highlighted, fitScale, zoom,
  feretPickMode, feretPickedIndices, onChange, onCordClick, onVesselClick, onFeretPointClick,
}: PolygonProps) {
  const [pts, setPts] = useState(toXY(entry.points));
  useEffect(() => { setPts(toXY(entry.points)); }, [entry.points]);

  const isCord     = entry.vesselIndex === null;
  const isEditing  = isCord ? editingCordIndex === entry.cordIndex : editingVesselKey === entry.id;
  const isSelected = selectedKey === entry.id;

  function handleDrag(index: number, x: number, y: number) {
    const updated = pts.map((p, i) => (i === index ? { x, y } : p));
    setPts(updated);
    onChange(toFlat(updated));
  }

  const strokeColor = highlighted || isEditing || isSelected ? COLOUR_YELLOW : entry.stroke;
  const strokeW     = highlighted || isEditing || isSelected ? strokeWidth * 2.5 : strokeWidth;
  const fillColor   = isEditing || isSelected || highlighted ? FILL_YELLOW_SELECTED : entry.fill;

  const scale            = fitScale * zoom;
  const pointRadius      = isCord ? 6 / scale : 4 / scale;
  const pointStrokeWidth = isCord ? 2 / scale : 1.5 / scale;

  function pointFillColor(i: number) {
    if (!isCord) return entry.stroke;
    if (feretPickMode) return feretPickedIndices.includes(i) ? COLOUR_CYAN : COLOUR_WHITE;
    return COLOUR_WHITE;
  }

  function pointStrokeColor(i: number) {
    if (isCord && feretPickMode && feretPickedIndices.includes(i)) return COLOUR_CYAN;
    return entry.stroke;
  }

  const showPoints = (isEditing && !feretPickMode) || (feretPickMode && isCord);

  return (
    <>
      <Line
        points={toFlat(pts)}
        closed
        stroke={strokeColor}
        strokeWidth={strokeW}
        fill={fillColor}
        dash={!isCord && entry.lowConfidence && !isEditing && !isSelected
          ? [strokeW * 6, strokeW * 3]
          : undefined}
        onClick={(e) => {
          e.cancelBubble = true;
          if (isCord) {
            onCordClick(entry.cordIndex, e.evt.clientX, e.evt.clientY);
          } else {
            onVesselClick(entry.cordIndex, entry.vesselIndex!, e.evt.clientX, e.evt.clientY);
          }
        }}
        onTap={(e) => {
          e.cancelBubble = true;
          const touch = (e.evt as TouchEvent).touches[0];
          if (isCord) {
            onCordClick(entry.cordIndex, touch.clientX, touch.clientY);
          } else {
            onVesselClick(entry.cordIndex, entry.vesselIndex!, touch.clientX, touch.clientY);
          }
        }}
        onMouseEnter={(e) => {
          const stage = e.target.getStage();
          if (stage) stage.container().style.cursor = "pointer";
        }}
        onMouseLeave={(e) => {
          const stage = e.target.getStage();
          if (stage) stage.container().style.cursor = "default";
        }}
        perfectDrawEnabled={false}
      />
      {showPoints && pts.map((pt, i) => (
        <Circle
          key={i}
          x={pt.x} y={pt.y}
          radius={pointRadius}
          fill={pointFillColor(i)}
          stroke={pointStrokeColor(i)}
          strokeWidth={pointStrokeWidth}
          opacity={0.95}
          draggable={isEditing && !feretPickMode}
          perfectDrawEnabled={false}
          onDragMove={(e) => handleDrag(i, e.target.x(), e.target.y())}
          onClick={(e) => {
            if (feretPickMode) { e.cancelBubble = true; onFeretPointClick(i); }
          }}
          onTap={(e) => {
            if (feretPickMode) { e.cancelBubble = true; onFeretPointClick(i); }
          }}
          onMouseEnter={feretPickMode ? (e) => {
            const stage = e.target.getStage();
            if (stage) stage.container().style.cursor = "crosshair";
          } : undefined}
          onMouseLeave={feretPickMode ? (e) => {
            const stage = e.target.getStage();
            if (stage) stage.container().style.cursor = "default";
          } : undefined}
        />
      ))}
    </>
  );
}

type FeretLineProps = {
  cordIndex: number;
  p1: { x: number; y: number };
  p2: { x: number; y: number };
  strokeWidth: number;
  highlighted: boolean;
  overriding: boolean;
  onLineClick: (cordIndex: number, screenX: number, screenY: number) => void;
};

function FeretLine({ cordIndex, p1, p2, strokeWidth, highlighted, overriding, onLineClick }: FeretLineProps) {
  const [hovered, setHovered] = useState(false);
  const color     = overriding || highlighted || hovered ? COLOUR_YELLOW : COLOUR_CYAN;
  const lineWidth = strokeWidth * (hovered || overriding ? 2.5 : 1.5);
  const diameter  = Math.round(euclidean(p1, p2));
  const midX      = (p1.x + p2.x) / 2;
  const midY      = (p1.y + p2.y) / 2;

  return (
    <>
      <Line
        points={[p1.x, p1.y, p2.x, p2.y]}
        stroke="rgba(0,0,0,0.01)"
        strokeWidth={strokeWidth * 15}
        onClick={(e) => {
          e.cancelBubble = true;
          onLineClick(cordIndex, e.evt.clientX, e.evt.clientY);
        }}
        onTap={(e) => {
          e.cancelBubble = true;
          const touch = (e.evt as TouchEvent).touches[0];
          onLineClick(cordIndex, touch.clientX, touch.clientY);
        }}
        onMouseEnter={(e) => {
          setHovered(true);
          const stage = e.target.getStage();
          if (stage) stage.container().style.cursor = "pointer";
        }}
        onMouseLeave={(e) => {
          setHovered(false);
          const stage = e.target.getStage();
          if (stage) stage.container().style.cursor = "default";
        }}
      />
      <Line
        points={[p1.x, p1.y, p2.x, p2.y]}
        stroke={color}
        strokeWidth={lineWidth}
        dash={overriding ? [] : [6 / lineWidth, 3 / lineWidth]}
        opacity={0.9}
        perfectDrawEnabled={false}
        listening={false}
      />
      <Text
        x={midX + 4 / lineWidth}
        y={midY - 12 / lineWidth}
        text={`${diameter}px`}
        fontSize={11 / lineWidth}
        fill={color}
        opacity={0.9}
        listening={false}
      />
    </>
  );
}

type PopupProps = {
  x: number;
  y: number;
  title: string;
  children: React.ReactNode;
  onClose: () => void;
};

function Popup({ x, y, title, children, onClose }: PopupProps) {
  return (
    <Box
      onClick={e => e.stopPropagation()}
      sx={{
        position: "absolute",
        left: x + 8,
        top: y - 8,
        zIndex: 200,
        bgcolor: "white",
        border: "1px solid #999",
        borderRadius: 1,
        boxShadow: "2px 2px 6px rgba(0,0,0,0.25)",
        minWidth: 160,
        overflow: "hidden",
      }}
    >
      <Box sx={{ bgcolor: "#e8e8e8", borderBottom: "1px solid #ccc", px: 1, py: 0.5 }}>
        <Typography sx={{ fontSize: 11, fontWeight: 600, color: "#333", fontFamily: "monospace" }}>
          {title}
        </Typography>
      </Box>
      <Box sx={{ px: 1, py: 0.75, display: "flex", flexDirection: "column", gap: 0.5 }}>
        {children}
        <Button size="small"
          sx={{ color: "#888", fontSize: 10, p: 0, minWidth: 0, justifyContent: "flex-start", textTransform: "none" }}
          onClick={onClose}>
          Dismiss
        </Button>
      </Box>
    </Box>
  );
}

const ZOOM_BY  = 1.15;
const ZOOM_MIN = 0.5;
const ZOOM_MAX = 8;

type Props = {
  imageUrl?: string;
  polygons?: Cord[];
  hoveredCordIndex: number | null;
  onFeretChange: (cordIndex: number, newDiameter: number) => void;
  onPolygonsChange?: (polygons: Cord[]) => void;
  onAddCord?: (cord: Cord) => void;
};

function Viewer({ imageUrl, polygons = [], hoveredCordIndex, onFeretChange, onPolygonsChange}: Props) {
  const stageRef             = useRef<Konva.Stage | null>(null);
  const containerRef         = useRef<HTMLDivElement>(null);
  const blockNextCanvasClick = useRef(false);

  const [image] = useImage(imageUrl ?? "", "anonymous");
  const [fitScale, setFitScale]         = useState(1);
  const [zoom, setZoom]                 = useState(1);
  const [dims, setDims]                 = useState({ width: 800, height: 600 });
  const [showPolygons, setShowPolygons] = useState(true);
  const [cords, setCords]               = useState<Cord[]>(polygons);

  const [editingCordIndex, setEditingCordIndex] = useState<number | null>(null);
  const [editingVesselKey, setEditingVesselKey] = useState<string | null>(null);
  const [selectedKey, setSelectedKey]           = useState<string | null>(null);

  const [cordPopup,   setCordPopup]   = useState<{ x: number; y: number; cordIndex: number } | null>(null);
  const [vesselPopup, setVesselPopup] = useState<{ x: number; y: number; cordIndex: number; vesselIndex: number } | null>(null);
  const [feretPopup,  setFeretPopup]  = useState<{ x: number; y: number; cordIndex: number } | null>(null);

  const [feretOverrideCord,  setFeretOverrideCord]  = useState<number | null>(null);
  const [feretPickedIndices, setFeretPickedIndices] = useState<number[]>([]);

  const isPanning = useRef(false);
  const lastPos   = useRef({ x: 0, y: 0 });

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
      x: (dims.width  - img.width  * scale) / 2,
      y: (dims.height - img.height * scale) / 2,
    });
    stage.batchDraw();
  }

  useEffect(() => {
    if (!image) return;
    const fit = Math.min(dims.width / image.width, dims.height / image.height) * 0.98;
    setFitScale(fit);
    setZoom(1);
    centerImage(image, fit, 1);
  }, [image, dims]);

  function applyZoom(newZoom: number, cx?: number, cy?: number) {
    const stage = stageRef.current;
    if (!stage || !image) return;
    newZoom = Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, newZoom));
    const oldScale = fitScale * zoom;
    const newScale = fitScale * newZoom;
    const pivotX = cx ?? dims.width  / 2;
    const pivotY = cy ?? dims.height / 2;
    const pos = stage.position();
    const pointTo = { x: (pivotX - pos.x) / oldScale, y: (pivotY - pos.y) / oldScale };
    setZoom(newZoom);
    stage.scale({ x: newScale, y: newScale });
    stage.position({ x: pivotX - pointTo.x * newScale, y: pivotY - pointTo.y * newScale });
    stage.batchDraw();
  }

  function handleWheel(e: Konva.KonvaEventObject<WheelEvent>) {
    e.evt.preventDefault();
    applyZoom(e.evt.deltaY > 0 ? zoom / 1.05 : zoom * 1.05, e.evt.offsetX, e.evt.offsetY);
  }

  function handleMouseDown(e: Konva.KonvaEventObject<MouseEvent>) {
    if (e.evt.altKey) {
      isPanning.current = true;
      lastPos.current   = { x: e.evt.clientX, y: e.evt.clientY };
      stageRef.current!.container().style.cursor = "grab";
    }
  }

  function handleMouseMove(e: Konva.KonvaEventObject<MouseEvent>) {
    if (!isPanning.current) return;
    const stage = stageRef.current!;
    const pos   = stage.position();
    stage.position({
      x: pos.x + e.evt.clientX - lastPos.current.x,
      y: pos.y + e.evt.clientY - lastPos.current.y,
    });
    lastPos.current = { x: e.evt.clientX, y: e.evt.clientY };
    stage.batchDraw();
  }

  function handleMouseUp() {
    isPanning.current = false;
    if (stageRef.current) stageRef.current.container().style.cursor = "default";
  }

  function updateCords(updater: (prev: Cord[]) => Cord[]) {
    setCords(prev => {
      const next = updater(prev);
      onPolygonsChange?.(next);
      return next;
    });
  }

  function updatePolygon(entry: FlatEntry, pts: number[]) {
    updateCords((prev) =>
      prev.map((cord, ci) => {
        if (ci !== entry.cordIndex) return cord;
        if (entry.vesselIndex === null) {
          const [i1, i2] = farthestPair(pts);
          const p = toXY(pts);
          return {
            ...cord,
            polygon: pts,
            start_end_points: [[p[i1].x, p[i1].y], [p[i2].x, p[i2].y]] as [[number, number], [number, number]],
            diameter: euclidean(p[i1], p[i2]),
          };
        }
        return {
          ...cord,
          vessels: cord.vessels.map((v, vi) => vi === entry.vesselIndex ? { ...v, polygon: pts } : v),
        };
      })
    );
  }

  function handleCordClick(cordIndex: number, screenX: number, screenY: number) {
    if (feretOverrideCord !== null) return;
    const rect = containerRef.current!.getBoundingClientRect();
    blockNextCanvasClick.current = true;
    setSelectedKey(`c${cordIndex}`);
    setCordPopup({ x: screenX - rect.left, y: screenY - rect.top, cordIndex });
    setVesselPopup(null);
    setFeretPopup(null);
  }

  function handleVesselClick(cordIndex: number, vesselIndex: number, screenX: number, screenY: number) {
    if (feretOverrideCord !== null) return;
    const rect = containerRef.current!.getBoundingClientRect();
    blockNextCanvasClick.current = true;
    setSelectedKey(`c${cordIndex}v${vesselIndex}`);
    setVesselPopup({ x: screenX - rect.left, y: screenY - rect.top, cordIndex, vesselIndex });
    setCordPopup(null);
    setFeretPopup(null);
  }

  function reclassifyVessel(cordIndex: number, vesselIndex: number, type: "Artery" | "Vein") {
    updateCords(prev => prev.map((c, ci) => {
      if (ci !== cordIndex) return c;
      return { ...c, vessels: c.vessels.map((v, vi) => vi === vesselIndex ? { ...v, type } : v) };
    }));
  }

  function handleFeretLineClick(cordIndex: number, screenX: number, screenY: number) {
    const rect = containerRef.current!.getBoundingClientRect();
    blockNextCanvasClick.current = true;
    setFeretPopup({ x: screenX - rect.left, y: screenY - rect.top, cordIndex });
    setCordPopup(null);
    setFeretOverrideCord(null);
    setFeretPickedIndices([]);
  }

  function startFeretEdit() {
    if (!feretPopup) return;
    setFeretOverrideCord(feretPopup.cordIndex);
    setFeretPickedIndices([]);
  }

  function cancelFeretEdit() {
    setFeretOverrideCord(null);
    setFeretPickedIndices([]);
    setFeretPopup(null);
  }

  function handleFeretPointClick(cordIndex: number, pointIndex: number) {
    if (feretOverrideCord !== cordIndex) return;
    setFeretPickedIndices(prev => {
      const next = [...prev, pointIndex];
      if (next.length === 2) {
        const pts = toXY(cords[cordIndex].polygon);
        const p1  = pts[next[0]];
        const p2  = pts[next[1]];
        const d   = euclidean(p1, p2);
        updateCords(c => c.map((cord, i) => i === cordIndex ? {
          ...cord,
          start_end_points: [[p1.x, p1.y], [p2.x, p2.y]] as [[number, number], [number, number]],
          diameter: d,
        } : cord));
        onFeretChange(cordIndex, d);
        setFeretOverrideCord(null);
        setFeretPopup(null);
        return [];
      }
      return next;
    });
  }

  function dragBounds(pos: { x: number; y: number }) {
    const scale   = fitScale * zoom;
    const imgW    = image!.width  * scale;
    const imgH    = image!.height * scale;
    const padding = 100;
    return {
      x: Math.min(padding, Math.max(dims.width  - imgW - padding, pos.x)),
      y: Math.min(padding, Math.max(dims.height - imgH - padding, pos.y)),
    };
  }

  function getFeretPoints(cord: Cord) {
    if (cord.start_end_points) {
      return {
        p1: { x: cord.start_end_points[0][0], y: cord.start_end_points[0][1] },
        p2: { x: cord.start_end_points[1][0], y: cord.start_end_points[1][1] },
      };
    }
    if (cord.polygon.length < 4) return null;
    const [i1, i2] = farthestPair(cord.polygon);
    const pts = toXY(cord.polygon);
    return { p1: pts[i1], p2: pts[i2] };
  }

  const flat        = flatten(cords);
  const strokeWidth = 2 / (fitScale * zoom);
  const btn = { color: "white", borderColor: "#444", minWidth: 0 };
  const feretPickStep = feretOverrideCord !== null
    ? (feretPickedIndices.length === 0 ? 1 : 2)
    : 0;

  if (!image) return null;

  return (
    <Box sx={{ display: "flex", flexDirection: "column", width: "100%", height: "100%", border: "1px solid", borderColor: "divider", borderRadius: 2, overflow: "hidden" }}>

      {/* Toolbar */}
      <Box sx={{ display: "flex", gap: 1, px: 2, height: 56, alignItems: "center", bgcolor: "#1a1a1a", flexShrink: 0, borderBottom: "1px solid #333" }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
          <Button size="small" variant="contained" sx={btn}
            onClick={() => { setZoom(1); centerImage(image, fitScale, 1); }}>
            Reset View
          </Button>
          <Button size="small" variant="contained" sx={{ ...btn, px: 1 }} title="Zoom in"
            onClick={() => applyZoom(zoom * ZOOM_BY)}>
            <AddIcon fontSize="small" />
          </Button>
          <Button size="small" variant="contained" sx={{ ...btn, px: 1 }} title="Zoom out"
            onClick={() => applyZoom(zoom / ZOOM_BY)}>
            <RemoveIcon fontSize="small" />
          </Button>
        </Box>

        <Box sx={{ width: "1px", height: 28, bgcolor: "#444", mx: 0.5 }} />

        <Button size="small" variant="contained" sx={btn}
          onClick={() => setShowPolygons(p => !p)}>
          {showPolygons ? "Hide Outlines" : "Show Outlines"}
        </Button>


        <Box sx={{ flex: 1 }} />
        <Typography variant="caption" sx={{ color: "#EEE", fontSize: 14, mr: 1 }}>
          {editingCordIndex !== null || editingVesselKey !== null
            ? "Drag points to reshape · Press Done when finished"
            : "Click an outline to edit · Click the diameter line to adjust it"}
        </Typography>

        {(editingCordIndex !== null || editingVesselKey !== null) && (
          <Button size="small" variant="outlined"
            sx={{ borderColor: COLOUR_YELLOW, color: COLOUR_YELLOW, fontWeight: 600 }}
            onClick={() => { setEditingCordIndex(null); setEditingVesselKey(null); setSelectedKey(null); }}>
            ✓ Done
          </Button>
        )}
      </Box>

      {/* Canvas */}
      <Box
        ref={containerRef}
        sx={{ flex: 1, overflow: "hidden", minHeight: 0, position: "relative" }}
        onClick={(e) => {
          if (blockNextCanvasClick.current) {
            blockNextCanvasClick.current = false;
            return;
          }
          if ((e.target as HTMLElement).tagName === "CANVAS") {
            setCordPopup(null);
            setVesselPopup(null);
            setFeretPopup(null);
            setSelectedKey(null);
          }
        }}
      >
        <Stage
          ref={stageRef}
          width={dims.width}
          height={dims.height}
          draggable={editingCordIndex === null && editingVesselKey === null}
          onWheel={handleWheel}
          dragBoundFunc={dragBounds}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
        >
          <Layer listening={false}>
            <KonvaImage image={image} x={0} y={0} width={image.width} height={image.height} perfectDrawEnabled={false} />
          </Layer>

          {showPolygons && (
            <Layer>
              {flat.map((e) => (
                <EditablePolygon
                  key={e.id}
                  entry={e}
                  strokeWidth={strokeWidth}
                  editingCordIndex={editingCordIndex}
                  editingVesselKey={editingVesselKey}
                  selectedKey={selectedKey}
                  highlighted={hoveredCordIndex === e.cordIndex && e.vesselIndex === null}
                  fitScale={fitScale}
                  zoom={zoom}
                  feretPickMode={feretOverrideCord === e.cordIndex && e.vesselIndex === null}
                  feretPickedIndices={feretOverrideCord === e.cordIndex ? feretPickedIndices : []}
                  onChange={(pts) => updatePolygon(e, pts)}
                  onCordClick={handleCordClick}
                  onVesselClick={handleVesselClick}
                  onFeretPointClick={(pi) => handleFeretPointClick(e.cordIndex, pi)}
                />
              ))}
            </Layer>
          )}

          {showPolygons && (
            <Layer>
              {cords.map((cord, ci) => {
                const feretPts = getFeretPoints(cord);
                if (!feretPts) return null;
                return (
                  <FeretLine
                    key={`feret-${ci}`}
                    cordIndex={ci}
                    p1={feretPts.p1}
                    p2={feretPts.p2}
                    strokeWidth={strokeWidth}
                    highlighted={hoveredCordIndex === ci}
                    overriding={feretOverrideCord === ci}
                    onLineClick={handleFeretLineClick}
                  />
                );
              })}
            </Layer>
          )}

        </Stage>

        {/* Vessel popup */}
        {vesselPopup && (() => {
          const vessel = cords[vesselPopup.cordIndex]?.vessels[vesselPopup.vesselIndex];
          if (!vessel) return null;
          const conf = vessel.confidence !== undefined ? Math.round(vessel.confidence * 100) : null;
          const confColor = conf === null ? "#999" : conf >= 80 ? CONF_HIGH : conf >= 50 ? CONF_MED : CONF_LOW;
          return (
            <Popup
              x={vesselPopup.x}
              y={vesselPopup.y}
              title={`Cord ${vesselPopup.cordIndex + 1} · Vessel ${vesselPopup.vesselIndex + 1}`}
              onClose={() => { setVesselPopup(null); setSelectedKey(null); }}
            >
              {conf !== null && (
                <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 0.75, pb: 0.75, borderBottom: "1px solid #eee" }}>
                  <Typography sx={{ fontSize: 11, color: "#555" }}>Model certainty</Typography>
                  <Typography sx={{ fontSize: 12, fontWeight: 700, color: confColor, fontFamily: "monospace" }}>
                    {conf}%
                  </Typography>
                </Box>
              )}
              <Button size="small" variant="outlined"
                sx={{ borderColor: "#bbb", color: "#222", fontSize: 11, textTransform: "none", width: "100%", justifyContent: "flex-start" }}
                onClick={() => {
                  setEditingVesselKey(`c${vesselPopup.cordIndex}v${vesselPopup.vesselIndex}`);
                  setVesselPopup(null);
                }}>
                Edit Polygon
              </Button>
              <Box sx={{ display: "flex", gap: 0.5, mt: 0.25 }}>
                {(["Artery", "Vein"] as const).map(t => (
                  <Button key={t} size="small"
                    variant={vessel.type === t ? "contained" : "outlined"}
                    sx={{
                      fontSize: 10,
                      textTransform: "none",
                      flex: 1,
                      bgcolor: vessel.type === t ? (t === "Artery" ? COLOUR_RED : COLOUR_BLUE) : "transparent",
                      borderColor: t === "Artery" ? COLOUR_RED : COLOUR_BLUE,
                      color: vessel.type === t ? "white" : (t === "Artery" ? COLOUR_RED : COLOUR_BLUE),
                      "&:hover": { opacity: 0.8 },
                    }}
                    onClick={() => reclassifyVessel(vesselPopup.cordIndex, vesselPopup.vesselIndex, t)}>
                    {t}
                  </Button>
                ))}
              </Box>
            </Popup>
          );
        })()}

        {/* Cord popup */}
        {cordPopup && (
          <Popup
            x={cordPopup.x}
            y={cordPopup.y}
            title={`Cord ${cordPopup.cordIndex + 1}`}
            onClose={() => { setCordPopup(null); setSelectedKey(null); }}
          >
            <Button size="small" variant="outlined"
              sx={{ borderColor: "#bbb", color: "#222", fontSize: 11, textTransform: "none", width: "100%", justifyContent: "flex-start" }}
              onClick={() => {
                setEditingCordIndex(cordPopup.cordIndex);
                setCordPopup(null);
              }}>
              Edit Polygon
            </Button>
          </Popup>
        )}

        {/* Feret popup */}
        {feretPopup && (
          <Popup
            x={feretPopup.x}
            y={feretPopup.y}
            title={`Cord ${feretPopup.cordIndex + 1} · Diameter`}
            onClose={() => setFeretPopup(null)}
          >
            {feretPickStep === 0 ? (
              <Button size="small" variant="outlined"
                sx={{ borderColor: "#bbb", color: "#222", fontSize: 11, textTransform: "none", width: "100%", justifyContent: "flex-start" }}
                onClick={startFeretEdit}>
                Edit Diameter
              </Button>
            ) : (
              <Typography variant="caption" sx={{ color: COLOUR_YELLOW, display: "block", mb: 0.5 }}>
                {feretPickStep === 1 ? "Click the first endpoint on the cord outline" : "Click the second endpoint"}
              </Typography>
            )}
            {feretPickStep > 0 && (
              <Button size="small" sx={{ color: "#666", fontSize: 11, p: 0 }} onClick={cancelFeretEdit}>
                Cancel
              </Button>
            )}
          </Popup>
        )}
      </Box>
    </Box>
  );
}

export default Viewer;