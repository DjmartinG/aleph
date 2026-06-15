"use client";

import { useMemo, useCallback } from "react";
import { ParentSize } from "@visx/responsive";
import { scaleLinear } from "@visx/scale";
import { Bar, LinePath, Line } from "@visx/shape";
import { Group } from "@visx/group";
import { AxisLeft, AxisRight, AxisBottom } from "@visx/axis";
import { GridRows } from "@visx/grid";
import { curveMonotoneX } from "@visx/curve";
import { useTooltip, TooltipWithBounds } from "@visx/tooltip";
import { localPoint } from "@visx/event";
import { yearTicks, monthLabel, mesesHastaHoy } from "@/lib/timeline";
import { TodayMarker } from "./today-marker";
import { fmtInt } from "@/lib/format";

const M = { top: 20, right: 40, bottom: 26, left: 34 };

interface Pt {
  m: number;
  ventas: number;
  acum: number;
}

/** Curva de absorción: barras de unidades vendidas por mes (teal) + línea de acumulado (eje derecho). */
export function AbsorptionChart({
  ventas,
  acum,
  baseDate,
  total,
  height = 280,
}: {
  ventas: number[];
  acum: number[];
  baseDate: string | null;
  total: number;
  height?: number;
}) {
  return (
    <div style={{ width: "100%", height }}>
      <ParentSize>
        {({ width }) => (
          <Inner width={width} height={height} ventas={ventas} acum={acum} baseDate={baseDate} total={total} />
        )}
      </ParentSize>
    </div>
  );
}

function Inner({
  width,
  height,
  ventas,
  acum,
  baseDate,
  total,
}: {
  width: number;
  height: number;
  ventas: number[];
  acum: number[];
  baseDate: string | null;
  total: number;
}) {
  const iw = Math.max(0, width - M.left - M.right);
  const ih = Math.max(0, height - M.top - M.bottom);
  const n = ventas.length;

  const data: Pt[] = useMemo(
    () => ventas.map((v, m) => ({ m, ventas: v, acum: acum[m] ?? 0 })),
    [ventas, acum],
  );
  const maxVentas = useMemo(() => Math.max(1, ...ventas), [ventas]);

  const xScale = useMemo(() => scaleLinear({ domain: [0, Math.max(1, n - 1)], range: [0, iw] }), [n, iw]);
  const yBars = useMemo(
    () => scaleLinear({ domain: [0, maxVentas * 1.1], range: [ih, 0], nice: true }),
    [maxVentas, ih],
  );
  const yLine = useMemo(
    () => scaleLinear({ domain: [0, Math.max(1, total)], range: [ih, 0] }),
    [total, ih],
  );
  const ticks = useMemo(() => yearTicks(baseDate, n), [baseDate, n]);
  const hoy = useMemo(() => mesesHastaHoy(baseDate), [baseDate]);
  const bw = Math.max(1, (iw / Math.max(1, n)) * 0.62);

  const { tooltipData, tooltipLeft, tooltipTop, showTooltip, hideTooltip } = useTooltip<Pt>();
  const onMove = useCallback(
    (e: React.MouseEvent<SVGRectElement>) => {
      const p = localPoint(e);
      if (!p) return;
      const mi = Math.round(xScale.invert(p.x - M.left));
      const d = data[Math.max(0, Math.min(n - 1, mi))];
      if (!d) return;
      showTooltip({ tooltipData: d, tooltipLeft: M.left + xScale(d.m), tooltipTop: M.top + yLine(d.acum) });
    },
    [data, n, xScale, yLine, showTooltip],
  );

  if (width < 10) return null;

  return (
    <div className="relative">
      <svg width={width} height={height}>
        <Group left={M.left} top={M.top}>
          <GridRows scale={yBars} width={iw} numTicks={4} stroke="var(--rule)" strokeOpacity={0.55} />

          {data.map((d) =>
            d.ventas > 0 ? (
              <Bar
                key={d.m}
                x={xScale(d.m) - bw / 2}
                y={yBars(d.ventas)}
                width={bw}
                height={Math.max(0, ih - yBars(d.ventas))}
                rx={1.5}
                fill="var(--primary)"
                fillOpacity={0.32}
              />
            ) : null,
          )}

          {/* Acumulado (eje derecho) */}
          <LinePath data={data} x={(d) => xScale(d.m)} y={(d) => yLine(d.acum)} curve={curveMonotoneX} stroke="var(--primary)" strokeWidth={2.25} />

          {hoy != null && hoy >= 0 && hoy <= Math.max(1, n - 1) ? (
            <TodayMarker x={xScale(hoy)} ih={ih} iw={iw} />
          ) : null}

          <AxisLeft
            scale={yBars}
            numTicks={4}
            stroke="transparent"
            tickStroke="transparent"
            tickLabelProps={() => ({ fill: "var(--muted-foreground)", fontSize: 10.5, textAnchor: "end", dx: -3, dy: 3 })}
          />
          <AxisRight
            left={iw}
            scale={yLine}
            numTicks={4}
            stroke="transparent"
            tickStroke="transparent"
            tickLabelProps={() => ({ fill: "var(--muted-foreground)", fontSize: 10.5, textAnchor: "start", dx: 3, dy: 3 })}
          />
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

        {tooltipData ? (
          <Group left={M.left} top={M.top}>
            <Line from={{ x: xScale(tooltipData.m), y: 0 }} to={{ x: xScale(tooltipData.m), y: ih }} stroke="var(--foreground)" strokeOpacity={0.18} />
            <circle cx={xScale(tooltipData.m)} cy={yLine(tooltipData.acum)} r={4} fill="var(--primary)" stroke="var(--card)" strokeWidth={2} />
          </Group>
        ) : null}
        <Bar x={M.left} y={M.top} width={iw} height={ih} fill="transparent" onMouseMove={onMove} onMouseLeave={hideTooltip} />
      </svg>

      {tooltipData ? (
        <TooltipWithBounds
          left={tooltipLeft}
          top={tooltipTop}
          style={{
            position: "absolute",
            background: "var(--popover)",
            color: "var(--popover-foreground)",
            border: "1px solid var(--border)",
            borderRadius: 6,
            padding: "6px 10px",
            boxShadow: "var(--shadow-card)",
            pointerEvents: "none",
          }}
        >
          <div className="text-[0.7rem] font-medium uppercase tracking-wide text-muted-foreground">
            {monthLabel(baseDate, tooltipData.m)}
          </div>
          <div className="num mt-0.5 text-sm font-semibold">{fmtInt(tooltipData.ventas)} und/mes</div>
          <div className="num text-xs text-muted-foreground">{fmtInt(tooltipData.acum)} acum.</div>
        </TooltipWithBounds>
      ) : null}
    </div>
  );
}
