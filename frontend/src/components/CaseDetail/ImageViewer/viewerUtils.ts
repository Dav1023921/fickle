export function toXY(pts: number[]): { x: number; y: number }[] {
  const result = [];
  for (let i = 0; i < pts.length; i += 2)
    result.push({ x: pts[i], y: pts[i + 1] });
  return result;
}

export function toFlat(pts: { x: number; y: number }[]): number[] {
  return pts.flatMap(p => [p.x, p.y]);
}

export function euclidean(p1: { x: number; y: number }, p2: { x: number; y: number }): number {
  return Math.sqrt(Math.pow(p2.x - p1.x, 2) + Math.pow(p2.y - p1.y, 2));
}

export function farthestPair(flat: number[]): [number, number] {
  const pts = toXY(flat);
  let best: [number, number] = [0, 1];
  let bestDist = 0;
  for (let i = 0; i < pts.length; i++) {
    for (let j = i + 1; j < pts.length; j++) {
      const d = euclidean(pts[i], pts[j]);
      if (d > bestDist) { bestDist = d; best = [i, j]; }
    }
  }
  return best;
}