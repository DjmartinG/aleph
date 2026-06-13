"use client";

import { useMemo, useCallback } from "react";
import { ParentSize } from "@visx/responsive";
import { scaleLinear } from "@visx/scale";
import { AreaClosed, LinePath, Line, Bar } from "@visx/shape";
import { LinearGradient } from "@visx/gradient";
import { AxisLeft, AxisBottom } from "@visx/axis";
import { GridRows } from "@visx/grid";
import { Group } from "@visx/group";
import { curveMonotoneX } from "@visx/curve";
import { useTooltip, TooltipWithBounds } from "@visx/tooltip";
import { localPoint } from "@visx/event";
import { fmtCop } from "@/lib/format";

export interface CashPoint {
  m: number;
  acum: number;
  credito: number;
}

const M = { top: 18, right: 18, bottom: 28, left: 70 };

/** Eje Y compacto: magnitud en "mil M" sin el sufijo (lo dice el título de la gráfica). */
function tickY(v: number): string {
  if (v === 0) return "0";
  return `${(v / 1_000_000).toLocaleString("en-US", { maximumFractionDigits: 0 }).replace(/,/g, ".")}`;
}

export function CashFlowChart({
  data,
  maxExposure,
  height = 320,
}: {
  data: CashPoint[];
  maxExposure: { m: number; value: number } | null;
  height?: number;
}) {
  return (
    <div style={{ width: "100%", height }}>
      <ParentSize>{({ width }) => <Inner width={width} height={height} data={data} maxExposure={maxExposure} />}</ParentSize>
    </div>
  );
}

function Inner({
  width,
  height,
  data,
  maxExposure,
}: {
  width: number;
  height: number;
  data: CashPoint[];
  maxExposure: { m: number; value: number } | null;
}) {
  const iw = Math.max(0, width - M.left - M.right);
  const ih = Math.max(0, height - M.top - M.bottom);
  const n = data.length;

  const xScale = useMemo(
    () => scaleLinear({ domain: [0, Math.max(1, n - 1)], range: [0, iw] }),
    [n, iw],
  );
  const yScale = useMemo(() => {
    let lo = 0;
    let hi = 0;
    for (const d of data) {
      lo = Math.min(lo, d.acum);
      hi = Math.max(hi, d.acum, d.credito);
    }
    const pad = (hi - lo) * 0.08 || 1;
    return scaleLinear({ domain: [lo - pad, hi + pad], range: [ih, 0], nice: true });
  }, [data, ih]);

  const { tooltipData, tooltipLeft, tooltipTop, showTooltip, hideTooltip } = useTooltip<CashPoint>();

  const onMove = useCallback(
    (e: React.MouseEvent<SVGRectElement>) => {
      const p = localPoint(e);
      if (!p) return;
      const mi = Math.round(xScale.invert(p.x - M.left));
      const d = data[Math.max(0, Math.min(n - 1, mi))];
      if (!d) return;
      showTooltip({
        tooltipData: d,
        tooltipLeft: M.left + xScale(d.m),
        tooltipTop: M.top + yScale(d.acum),
      });
    },
    [data, n, xScale, yScale, showTooltip],
  );

  if (width < 10) return null;
  const zeroY = yScale(0);

  return (
    <div className="relative">
      <svg width={width} height={height}>
        <LinearGradient id="cashGrad" from="var(--primary)" to="var(--primary)" fromOpacity={0.28} toOpacity={0.02} />
        <Group left={M.left} top={M.top}>
          <GridRows scale={yScale} width={iw} numTicks={4} stroke="var(--rule)" strokeOpacity={0.6} />

          <AreaClosed
            data={data}
            x={(d) => xScale(d.m)}
            y={(d) => yScale(d.acum)}
            yScale={yScale}
            curve={curveMonotoneX}
            fill="url(#cashGrad)"
          />
          {/* Línea cero (umbral de exposición). */}
          <Line from={{ x: 0, y: zeroY }} to={{ x: iw, y: zeroY }} stroke="var(--muted-foreground)" strokeOpacity={0.5} strokeDasharray="3,3" />

          {/* Crédito (ámbar). */}
          <LinePath data={data} x={(d) => xScale(d.m)} y={(d) => yScale(d.credito)} curve={curveMonotoneX} stroke="var(--cg-amber)" strokeWidth={1.5} strokeOpacity={0.85} />
          {/* Caja acumulada (teal). */}
          <LinePath data={data} x={(d) => xScale(d.m)} y={(d) => yScale(d.acum)} curve={curveMonotoneX} stroke="var(--primary)" strokeWidth={2.25} />

          {/* Exposición máxima (punto + etiqueta). */}
          {maxExposure ? (
            <Group>
              <Line from={{ x: xScale(maxExposure.m), y: 0 }} to={{ x: xScale(maxExposure.m), y: ih }} stroke="var(--danger)" strokeOpacity={0.35} strokeDasharray="2,3" />
              <circle cx={xScale(maxExposure.m)} cy={yScale(maxExposure.value)} r={4.5} fill="var(--danger)" stroke="var(--card)" strokeWidth={2} />
            </Group>
          ) : null}

          <AxisLeft
            scale={yScale}
            numTicks={4}
            tickFormat={(v) => tickY(v as number)}
            stroke="transparent"
            tickStroke="transparent"
            tickLabelProps={() => ({ fill: "var(--muted-foreground)", fontSize: 11, textAnchor: "end", dx: -4, dy: 3 })}
          />
          <AxisBottom
            top={ih}
            scale={xScale}
            numTicks={Math.min(8, Math.ceil(n / 12))}
            tickFormat={(v) => `${Math.round((v as number) / 12)}a`}
            stroke="var(--rule)"
            tickStroke="transparent"
            tickLabelProps={() => ({ fill: "var(--muted-foreground)", fontSize: 11, textAnchor: "middle", dy: 2 })}
          />
        </Group>

        {/* Crosshair + overlay para tooltip. */}
        {tooltipData ? (
          <Group left={M.left} top={M.top}>
            <Line from={{ x: xScale(tooltipData.m), y: 0 }} to={{ x: xScale(tooltipData.m), y: ih }} stroke="var(--foreground)" strokeOpacity={0.18} />
            <circle cx={xScale(tooltipData.m)} cy={yScale(tooltipData.acum)} r={4} fill="var(--primary)" stroke="var(--card)" strokeWidth={2} />
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
            Año {Math.floor(tooltipData.m / 12) + 1}, mes {(tooltipData.m % 12) + 1}
          </div>
          <div className="num mt-0.5 text-sm font-semibold">
            Caja {fmtCop(tooltipData.acum)}
          </div>
          {tooltipData.credito > 0 ? (
            <div className="num text-xs text-muted-foreground">Crédito {fmtCop(tooltipData.credito)}</div>
          ) : null}
        </TooltipWithBounds>
      ) : null}
    </div>
  );
}
