"use client";

import { ParentSize } from "@visx/responsive";
import { scaleLinear, scaleBand } from "@visx/scale";
import { Group } from "@visx/group";
import { Line } from "@visx/shape";
import type { EscenarioVals } from "@/lib/api";
import { fmtCop, fmtPct } from "@/lib/format";

const ORDER = ["Optimista", "Base", "Pesimista"];
const COLOR: Record<string, string> = {
  Optimista: "var(--success)",
  Base: "var(--primary)",
  Pesimista: "var(--danger)",
};

const M = { top: 6, right: 138, bottom: 6, left: 92 };

type Row = { name: string } & EscenarioVals;

export function ScenarioCompare({ escenarios }: { escenarios: Record<string, EscenarioVals> }) {
  const rows: Row[] = ORDER.filter((k) => escenarios[k]).map((k) => ({ name: k, ...escenarios[k] }));
  const h = rows.length * 54 + M.top + M.bottom;
  return (
    <div style={{ width: "100%", height: h }}>
      <ParentSize>{({ width }) => <Inner width={width} height={h} rows={rows} />}</ParentSize>
    </div>
  );
}

function Inner({ width, height, rows }: { width: number; height: number; rows: Row[] }) {
  const iw = Math.max(0, width - M.left - M.right);
  const ih = Math.max(0, height - M.top - M.bottom);
  const vals = rows.map((r) => r.util_oper);
  const lo = Math.min(0, ...vals);
  const hi = Math.max(0, ...vals);
  const x = scaleLinear({ domain: [lo, hi], range: [0, iw], nice: true });
  const y = scaleBand({ domain: rows.map((r) => r.name), range: [0, ih], padding: 0.32 });
  if (width < 10) return null;
  const zero = x(0);

  return (
    <svg width={width} height={height}>
      <Group left={M.left} top={M.top}>
        <Line from={{ x: zero, y: 0 }} to={{ x: zero, y: ih }} stroke="var(--rule)" />
        {rows.map((r) => {
          const by = y(r.name) ?? 0;
          const bh = y.bandwidth();
          const xv = x(r.util_oper);
          const x0 = Math.min(zero, xv);
          const w = Math.max(2, Math.abs(xv - zero));
          const labelX = Math.max(xv, zero) + 8;
          return (
            <Group key={r.name}>
              <text x={-12} y={by + bh / 2} textAnchor="end" dominantBaseline="middle" fontSize={13} fontWeight={500} fill="var(--foreground)">
                {r.name}
              </text>
              <rect x={x0} y={by} width={w} height={bh} rx={2} fill={COLOR[r.name] ?? "var(--muted-foreground)"} opacity={0.9} />
              <text x={labelX} y={by + bh / 2 - 6} textAnchor="start" dominantBaseline="middle" fontSize={12.5} fontWeight={600} fill="var(--foreground)" style={{ fontVariantNumeric: "tabular-nums" }}>
                {fmtCop(r.util_oper)}
              </text>
              <text x={labelX} y={by + bh / 2 + 9} textAnchor="start" dominantBaseline="middle" fontSize={11} fill="var(--muted-foreground)" style={{ fontVariantNumeric: "tabular-nums" }}>
                margen {fmtPct(r.margen)}
              </text>
            </Group>
          );
        })}
      </Group>
    </svg>
  );
}
