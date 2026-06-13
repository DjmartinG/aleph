"use client";

import { ParentSize } from "@visx/responsive";
import { scaleLinear } from "@visx/scale";
import { Group } from "@visx/group";
import { Bar, Line } from "@visx/shape";
import { AxisBottom } from "@visx/axis";

export interface HistMarker {
  label: string;
  value: number;
  color: string;
  dash?: boolean;
}

const M = { top: 16, right: 14, bottom: 28, left: 10 };

export function DistributionHistogram({
  values,
  markers,
  hurdle,
  format,
  height = 260,
  bins = 28,
}: {
  values: number[];
  markers: HistMarker[];
  /** valor a la izquierda del cual las barras se pintan en rojo (zona de "fracaso"). */
  hurdle?: number;
  format: (v: number) => string;
  height?: number;
  bins?: number;
}) {
  return (
    <div style={{ width: "100%", height }}>
      <ParentSize>
        {({ width }) => (
          <Inner width={width} height={height} values={values} markers={markers} hurdle={hurdle} format={format} bins={bins} />
        )}
      </ParentSize>
    </div>
  );
}

function Inner({
  width,
  height,
  values,
  markers,
  hurdle,
  format,
  bins,
}: {
  width: number;
  height: number;
  values: number[];
  markers: HistMarker[];
  hurdle?: number;
  format: (v: number) => string;
  bins: number;
}) {
  const iw = Math.max(0, width - M.left - M.right);
  const ih = Math.max(0, height - M.top - M.bottom);
  if (width < 10 || values.length === 0) return null;

  let lo = Infinity;
  let hi = -Infinity;
  for (const v of values) {
    if (v < lo) lo = v;
    if (v > hi) hi = v;
  }
  const span = hi - lo || 1;
  const bw = span / bins;
  const counts = new Array(bins).fill(0);
  for (const v of values) {
    let i = Math.floor((v - lo) / bw);
    if (i >= bins) i = bins - 1;
    if (i < 0) i = 0;
    counts[i]++;
  }
  const maxC = Math.max(...counts, 1);
  const x = scaleLinear({ domain: [lo, hi], range: [0, iw] });
  const y = scaleLinear({ domain: [0, maxC], range: [ih, 0] });

  return (
    <svg width={width} height={height}>
      <Group left={M.left} top={M.top}>
        {counts.map((c, i) => {
          const x0 = lo + i * bw;
          const x1 = x0 + bw;
          const below = hurdle != null && (x0 + x1) / 2 < hurdle;
          return (
            <Bar
              key={i}
              x={x(x0) + 0.5}
              y={y(c)}
              width={Math.max(0, x(x1) - x(x0) - 1)}
              height={ih - y(c)}
              fill={below ? "var(--danger)" : "var(--primary)"}
              opacity={below ? 0.5 : 0.8}
              rx={1}
            />
          );
        })}
        {markers.map((m) => (
          <Group key={m.label}>
            <Line
              from={{ x: x(m.value), y: 0 }}
              to={{ x: x(m.value), y: ih }}
              stroke={m.color}
              strokeWidth={m.dash ? 1 : 1.5}
              strokeDasharray={m.dash ? "3,3" : undefined}
              strokeOpacity={0.9}
            />
            <text x={x(m.value)} y={-4} textAnchor="middle" fontSize={9.5} fontWeight={600} fill={m.color}>
              {m.label}
            </text>
          </Group>
        ))}
        <AxisBottom
          top={ih}
          scale={x}
          numTicks={6}
          tickFormat={(v) => format(v as number)}
          stroke="var(--rule)"
          tickStroke="transparent"
          tickLabelProps={() => ({ fill: "var(--muted-foreground)", fontSize: 10, textAnchor: "middle", dy: 2 })}
        />
      </Group>
    </svg>
  );
}
