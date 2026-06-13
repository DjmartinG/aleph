"use client";

import { ParentSize } from "@visx/responsive";
import { scaleLinear, scaleBand } from "@visx/scale";
import { Group } from "@visx/group";
import { Line } from "@visx/shape";
import { AxisBottom } from "@visx/axis";

interface VarBar {
  name: string;
  low: number;
  high: number;
  span: number;
}

/** Agrupa "{Var} ±N%" por variable → {low (impacto más negativo), high (más positivo)}, orden por span. */
function toBars(t: Record<string, number>): VarBar[] {
  const by: Record<string, { low: number; high: number }> = {};
  for (const [k, v] of Object.entries(t)) {
    const parts = k.split(" ");
    parts.pop();
    const name = parts.join(" ");
    const b = by[name] ?? { low: 0, high: 0 };
    if (v < 0) b.low = Math.min(b.low, v);
    else b.high = Math.max(b.high, v);
    by[name] = b;
  }
  return Object.entries(by)
    .map(([name, b]) => ({ name, low: b.low, high: b.high, span: b.high - b.low }))
    .sort((a, b) => b.span - a.span);
}

const M = { top: 6, right: 18, bottom: 26, left: 124 };

function tickY(v: number): string {
  if (v === 0) return "0";
  return `${(v / 1_000_000).toLocaleString("en-US", { maximumFractionDigits: 0 }).replace(/,/g, ".")}`;
}

export function TornadoChart({ tornado, height }: { tornado: Record<string, number>; height?: number }) {
  const bars = toBars(tornado);
  const h = height ?? bars.length * 48 + M.top + M.bottom;
  return (
    <div style={{ width: "100%", height: h }}>
      <ParentSize>{({ width }) => <Inner width={width} height={h} bars={bars} />}</ParentSize>
    </div>
  );
}

function Inner({ width, height, bars }: { width: number; height: number; bars: VarBar[] }) {
  const iw = Math.max(0, width - M.left - M.right);
  const ih = Math.max(0, height - M.top - M.bottom);
  const maxAbs = Math.max(1, ...bars.flatMap((b) => [Math.abs(b.low), Math.abs(b.high)]));
  const x = scaleLinear({ domain: [-maxAbs, maxAbs], range: [0, iw], nice: true });
  const y = scaleBand({ domain: bars.map((b) => b.name), range: [0, ih], padding: 0.42 });
  if (width < 10) return null;
  const zero = x(0);

  return (
    <svg width={width} height={height}>
      <Group left={M.left} top={M.top}>
        {bars.map((b) => {
          const by = y(b.name) ?? 0;
          const bh = y.bandwidth();
          return (
            <Group key={b.name}>
              <text x={-12} y={by + bh / 2} textAnchor="end" dominantBaseline="middle" fontSize={12} fill="var(--foreground)">
                {b.name}
              </text>
              <rect x={x(b.low)} y={by} width={Math.max(0, zero - x(b.low))} height={bh} rx={2} fill="var(--cg-amber)" opacity={0.85} />
              <rect x={zero} y={by} width={Math.max(0, x(b.high) - zero)} height={bh} rx={2} fill="var(--primary)" opacity={0.9} />
            </Group>
          );
        })}
        <Line from={{ x: zero, y: 0 }} to={{ x: zero, y: ih }} stroke="var(--foreground)" strokeOpacity={0.3} />
        <AxisBottom
          top={ih}
          scale={x}
          numTicks={5}
          tickFormat={(v) => tickY(v as number)}
          stroke="var(--rule)"
          tickStroke="transparent"
          tickLabelProps={() => ({ fill: "var(--muted-foreground)", fontSize: 10, textAnchor: "middle", dy: 2 })}
        />
      </Group>
    </svg>
  );
}
