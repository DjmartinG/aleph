"use client";

import { useMemo } from "react";
import { ParentSize } from "@visx/responsive";
import { scaleLinear } from "@visx/scale";
import { Group } from "@visx/group";
import { AxisBottom } from "@visx/axis";
import type { ScheduleEtapa } from "@/lib/api";
import { yearTicks } from "@/lib/timeline";

const M = { top: 8, right: 18, bottom: 26, left: 138 };
const ROW = 46;

function truncate(s: string, n: number): string {
  return s.length > n ? `${s.slice(0, n - 1)}…` : s;
}

/** Gantt de etapas: barra de ventas (IV→FV, teal) con marca de equilibrio (PE) y barra de
 * construcción (IC→FC, ámbar). Ambas en pistas separadas para no colisionar cuando se solapan. */
export function GanttChart({
  etapas,
  horizonte,
  baseDate,
}: {
  etapas: ScheduleEtapa[];
  horizonte: number;
  baseDate: string | null;
}) {
  const height = etapas.length * ROW + M.top + M.bottom;
  return (
    <div style={{ width: "100%", height }}>
      <ParentSize>
        {({ width }) => (
          <Inner width={width} height={height} etapas={etapas} horizonte={horizonte} baseDate={baseDate} />
        )}
      </ParentSize>
    </div>
  );
}

function Inner({
  width,
  height,
  etapas,
  horizonte,
  baseDate,
}: {
  width: number;
  height: number;
  etapas: ScheduleEtapa[];
  horizonte: number;
  baseDate: string | null;
}) {
  const iw = Math.max(0, width - M.left - M.right);
  const ih = etapas.length * ROW;
  const xScale = useMemo(
    () => scaleLinear({ domain: [0, Math.max(1, horizonte - 1)], range: [0, iw] }),
    [horizonte, iw],
  );
  const ticks = useMemo(() => yearTicks(baseDate, horizonte), [baseDate, horizonte]);

  if (width < 10) return null;

  return (
    <svg width={width} height={height}>
      {/* Pista temporal */}
      <Group left={M.left} top={M.top}>
        {ticks.map((t) => (
          <line
            key={t.m}
            x1={xScale(t.m)}
            x2={xScale(t.m)}
            y1={0}
            y2={ih}
            stroke="var(--rule)"
            strokeOpacity={0.5}
          />
        ))}

        {etapas.map((e, i) => {
          const y0 = i * ROW;
          const vx = xScale(e.iv_mes);
          const vw = Math.max(2, xScale(e.fv_mes) - xScale(e.iv_mes));
          const cx = xScale(e.ic_mes);
          const cw = Math.max(2, xScale(e.fc_mes) - xScale(e.ic_mes));
          return (
            <Group key={String(e.cod)} top={y0}>
              {i > 0 ? (
                <line x1={0} x2={iw} y1={0} y2={0} stroke="var(--rule)" strokeOpacity={0.45} />
              ) : null}
              {/* Ventas (IV → FV) */}
              <rect x={vx} y={ROW / 2 - 13} width={vw} height={10} rx={3} fill="var(--primary)" fillOpacity={0.85} />
              {/* Punto de equilibrio sobre la barra de ventas */}
              <circle cx={xScale(e.pe_mes)} cy={ROW / 2 - 8} r={3.2} fill="var(--card)" stroke="var(--primary)" strokeWidth={1.6} />
              {/* Construcción (IC → FC) */}
              <rect x={cx} y={ROW / 2 + 3} width={cw} height={10} rx={3} fill="var(--cg-amber)" fillOpacity={0.85} />
            </Group>
          );
        })}

        <AxisBottom
          top={ih}
          scale={xScale}
          tickValues={ticks.map((t) => t.m)}
          tickFormat={(v) => ticks.find((t) => t.m === (v as number))?.label ?? ""}
          stroke="var(--rule)"
          tickStroke="transparent"
          tickLabelProps={() => ({ fill: "var(--muted-foreground)", fontSize: 11, textAnchor: "middle", dy: 2 })}
        />
      </Group>

      {/* Rótulos de etapa (columna izquierda) */}
      <Group top={M.top}>
        {etapas.map((e, i) => (
          <Group key={String(e.cod)} top={i * ROW}>
            <text x={6} y={ROW / 2 - 2} fontSize={12} fontWeight={600} fill="var(--foreground)">
              {truncate(e.nombre, 19)}
            </text>
            <text
              x={6}
              y={ROW / 2 + 13}
              fontSize={10.5}
              fill="var(--muted-foreground)"
              style={{ fontVariantNumeric: "tabular-nums" }}
            >
              {e.unidades} und
            </text>
          </Group>
        ))}
      </Group>
    </svg>
  );
}
