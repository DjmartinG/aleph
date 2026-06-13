"use client";

import { useMemo, useCallback } from "react";
import { ParentSize } from "@visx/responsive";
import { scaleLinear } from "@visx/scale";
import { AreaStack, Bar, Line } from "@visx/shape";
import { Group } from "@visx/group";
import { AxisLeft, AxisBottom } from "@visx/axis";
import { GridRows } from "@visx/grid";
import { curveMonotoneX } from "@visx/curve";
import { useTooltip, TooltipWithBounds } from "@visx/tooltip";
import { localPoint } from "@visx/event";
import { yearTicks, monthLabel } from "@/lib/timeline";
import { fmtCop } from "@/lib/format";

const M = { top: 14, right: 16, bottom: 26, left: 40 };
const KEYS = ["separacion", "cuota_inicial", "subrogacion"] as const;
type Key = (typeof KEYS)[number];

const COLOR: Record<Key, string> = {
  separacion: "var(--cg-amber)",
  cuota_inicial: "var(--chart-3, var(--muted-foreground))",
  subrogacion: "var(--primary)",
};
const OPACITY: Record<Key, number> = { separacion: 0.55, cuota_inicial: 0.4, subrogacion: 0.28 };

interface Row {
  m: number;
  separacion: number;
  cuota_inicial: number;
  subrogacion: number;
  total: number;
}

/** Eje Y en "mil M" sin sufijo (lo dice el título): valores en miles COP → /1e6. */
function tickY(v: number): string {
  if (v === 0) return "0";
  return `${(v / 1_000_000).toLocaleString("en-US", { maximumFractionDigits: 0 }).replace(/,/g, ".")}`;
}

/** Recaudo mensual apilado: separación + cuota inicial + subrogación (crédito hipotecario). */
export function RecaudoChart({
  separacion,
  cuotaInicial,
  subrogacion,
  baseDate,
  height = 280,
}: {
  separacion: number[];
  cuotaInicial: number[];
  subrogacion: number[];
  baseDate: string | null;
  height?: number;
}) {
  return (
    <div style={{ width: "100%", height }}>
      <ParentSize>
        {({ width }) => (
          <Inner
            width={width}
            height={height}
            separacion={separacion}
            cuotaInicial={cuotaInicial}
            subrogacion={subrogacion}
            baseDate={baseDate}
          />
        )}
      </ParentSize>
    </div>
  );
}

function Inner({
  width,
  height,
  separacion,
  cuotaInicial,
  subrogacion,
  baseDate,
}: {
  width: number;
  height: number;
  separacion: number[];
  cuotaInicial: number[];
  subrogacion: number[];
  baseDate: string | null;
}) {
  const iw = Math.max(0, width - M.left - M.right);
  const ih = Math.max(0, height - M.top - M.bottom);
  const n = subrogacion.length;

  const data: Row[] = useMemo(
    () =>
      subrogacion.map((_, m) => {
        const s = separacion[m] ?? 0;
        const c = cuotaInicial[m] ?? 0;
        const sub = subrogacion[m] ?? 0;
        return { m, separacion: s, cuota_inicial: c, subrogacion: sub, total: s + c + sub };
      }),
    [separacion, cuotaInicial, subrogacion],
  );
  const maxTotal = useMemo(() => Math.max(1, ...data.map((d) => d.total)), [data]);

  const xScale = useMemo(() => scaleLinear({ domain: [0, Math.max(1, n - 1)], range: [0, iw] }), [n, iw]);
  const yScale = useMemo(
    () => scaleLinear({ domain: [0, maxTotal * 1.08], range: [ih, 0], nice: true }),
    [maxTotal, ih],
  );
  const ticks = useMemo(() => yearTicks(baseDate, n), [baseDate, n]);

  const { tooltipData, tooltipLeft, tooltipTop, showTooltip, hideTooltip } = useTooltip<Row>();
  const onMove = useCallback(
    (e: React.MouseEvent<SVGRectElement>) => {
      const p = localPoint(e);
      if (!p) return;
      const mi = Math.round(xScale.invert(p.x - M.left));
      const d = data[Math.max(0, Math.min(n - 1, mi))];
      if (!d) return;
      showTooltip({ tooltipData: d, tooltipLeft: M.left + xScale(d.m), tooltipTop: M.top + yScale(d.total) });
    },
    [data, n, xScale, yScale, showTooltip],
  );

  if (width < 10) return null;

  return (
    <div className="relative">
      <svg width={width} height={height}>
        <Group left={M.left} top={M.top}>
          <GridRows scale={yScale} width={iw} numTicks={4} stroke="var(--rule)" strokeOpacity={0.55} />

          <AreaStack<Row>
            data={data}
            keys={KEYS as unknown as Key[]}
            value={(d, k) => d[k as Key]}
            x={(d) => xScale(d.data.m)}
            y0={(d) => yScale(d[0])}
            y1={(d) => yScale(d[1])}
            curve={curveMonotoneX}
          >
            {({ stacks, path }) =>
              stacks.map((stack) => (
                <path
                  key={stack.key}
                  d={path(stack) || ""}
                  fill={COLOR[stack.key as Key]}
                  fillOpacity={OPACITY[stack.key as Key]}
                  stroke={COLOR[stack.key as Key]}
                  strokeOpacity={0.5}
                  strokeWidth={0.75}
                />
              ))
            }
          </AreaStack>

          <AxisLeft
            scale={yScale}
            numTicks={4}
            tickFormat={(v) => tickY(v as number)}
            stroke="transparent"
            tickStroke="transparent"
            tickLabelProps={() => ({ fill: "var(--muted-foreground)", fontSize: 10.5, textAnchor: "end", dx: -3, dy: 3 })}
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
          <div className="num mt-0.5 text-sm font-semibold">{fmtCop(tooltipData.total)}</div>
          <div className="num mt-0.5 space-y-px text-[0.7rem] text-muted-foreground">
            <div>Subrogación {fmtCop(tooltipData.subrogacion)}</div>
            <div>Cuota inicial {fmtCop(tooltipData.cuota_inicial)}</div>
            <div>Separación {fmtCop(tooltipData.separacion)}</div>
          </div>
        </TooltipWithBounds>
      ) : null}
    </div>
  );
}
