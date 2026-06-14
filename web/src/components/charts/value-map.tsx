"use client";

import { useMemo } from "react";
import { ParentSize } from "@visx/responsive";
import { scaleLinear, scaleSqrt } from "@visx/scale";
import { Group } from "@visx/group";
import { AxisLeft, AxisBottom } from "@visx/axis";
import { GridRows, GridColumns } from "@visx/grid";
import { Line } from "@visx/shape";
import { useTooltip, TooltipWithBounds } from "@visx/tooltip";
import { localPoint } from "@visx/event";
import type { ProjectItem } from "@/lib/api";
import { fmtCop, fmtPct, TIR_DEGENERADA } from "@/lib/format";

const M = { top: 16, right: 18, bottom: 38, left: 46 };

interface Pt {
  nombre: string;
  tir: number;
  margen: number;
  ventas: number;
  tipo: string;
  und: number;
}

function color(tipo: string): string {
  return /no\s*vis/i.test(tipo) ? "var(--cg-amber)" : "var(--primary)";
}

/** Mapa de valor del portafolio: TIR apal. ref. (X) × margen operativo (Y); tamaño = ventas, color = tipo.
 * Cruz de cuadrantes en los umbrales de industria (TIR 30%, margen 5%). Sin visx-blank: ver DOM. */
export function ValueMap({
  items,
  tirRef = 0.3,
  margenRef = 0.05,
  height = 380,
}: {
  items: ProjectItem[];
  tirRef?: number;
  margenRef?: number;
  height?: number;
}) {
  const pts: Pt[] = useMemo(
    () =>
      items
        .filter((i) => i.tir != null && i.tir > TIR_DEGENERADA && i.margen != null && i.ventas != null)
        .map((i) => ({
          nombre: i.nombre,
          tir: i.tir as number,
          margen: i.margen as number,
          ventas: i.ventas as number,
          tipo: i.tipo || "VIS",
          und: i.und,
        })),
    [items],
  );
  const excluidos = items.length - pts.length;

  return (
    <div>
      <div style={{ width: "100%", height }}>
        <ParentSize>
          {({ width }) => (
            <Inner width={width} height={height} pts={pts} tirRef={tirRef} margenRef={margenRef} />
          )}
        </ParentSize>
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-x-5 gap-y-1 text-xs text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <span className="size-2.5 rounded-full bg-primary" /> VIS
        </span>
        <span className="flex items-center gap-1.5">
          <span className="size-2.5 rounded-full bg-cg-amber" /> No VIS
        </span>
        <span>· tamaño = ventas · cruz en TIR {fmtPct(tirRef, 0)} / margen {fmtPct(margenRef, 0)}</span>
        {excluidos > 0 ? <span>· {excluidos} sin TIR significativa (excluidos)</span> : null}
      </div>
    </div>
  );
}

function Inner({
  width,
  height,
  pts,
  tirRef,
  margenRef,
}: {
  width: number;
  height: number;
  pts: Pt[];
  tirRef: number;
  margenRef: number;
}) {
  const iw = Math.max(0, width - M.left - M.right);
  const ih = Math.max(0, height - M.top - M.bottom);

  const xScale = useMemo(() => {
    const xs = [...pts.map((p) => p.tir), tirRef, 0];
    const lo = Math.min(...xs);
    const hi = Math.max(...xs);
    const pad = (hi - lo) * 0.15 || 0.05;
    return scaleLinear({ domain: [lo - pad, hi + pad], range: [0, iw], nice: true });
  }, [pts, tirRef, iw]);

  const yScale = useMemo(() => {
    const ys = [...pts.map((p) => p.margen), margenRef, 0];
    const lo = Math.min(...ys);
    const hi = Math.max(...ys);
    const pad = (hi - lo) * 0.18 || 0.02;
    return scaleLinear({ domain: [lo - pad, hi + pad], range: [ih, 0], nice: true });
  }, [pts, margenRef, ih]);

  const rScale = useMemo(() => {
    const max = Math.max(1, ...pts.map((p) => p.ventas));
    return scaleSqrt({ domain: [0, max], range: [7, 26] });
  }, [pts]);

  const { tooltipData, tooltipLeft, tooltipTop, showTooltip, hideTooltip } = useTooltip<Pt>();

  if (width < 10) return null;
  const xq = xScale(tirRef);
  const yq = yScale(margenRef);

  return (
    <div className="relative">
      <svg width={width} height={height}>
        <Group left={M.left} top={M.top}>
          <GridRows scale={yScale} width={iw} numTicks={4} stroke="var(--rule)" strokeOpacity={0.5} />
          <GridColumns scale={xScale} height={ih} numTicks={5} stroke="var(--rule)" strokeOpacity={0.5} />

          {/* Cruz de cuadrantes */}
          <Line from={{ x: xq, y: 0 }} to={{ x: xq, y: ih }} stroke="var(--muted-foreground)" strokeOpacity={0.45} strokeDasharray="4,3" />
          <Line from={{ x: 0, y: yq }} to={{ x: iw, y: yq }} stroke="var(--muted-foreground)" strokeOpacity={0.45} strokeDasharray="4,3" />

          {/* Rótulos de cuadrante */}
          <QuadLabel x={iw - 4} y={4} anchor="end" text="Estrella" />
          <QuadLabel x={4} y={4} anchor="start" text="Crecimiento" />
          <QuadLabel x={iw - 4} y={ih - 14} anchor="end" text="Vigilancia" />
          <QuadLabel x={4} y={ih - 14} anchor="start" text="Revisar" />

          {/* Burbujas */}
          {pts.map((p) => (
            <circle
              key={p.nombre}
              cx={xScale(p.tir)}
              cy={yScale(p.margen)}
              r={rScale(p.ventas)}
              fill={color(p.tipo)}
              fillOpacity={0.22}
              stroke={color(p.tipo)}
              strokeOpacity={0.85}
              strokeWidth={1.5}
              onMouseMove={(e) => {
                const pt = localPoint(e);
                if (pt) showTooltip({ tooltipData: p, tooltipLeft: pt.x, tooltipTop: pt.y });
              }}
              onMouseLeave={hideTooltip}
            />
          ))}
          {/* Etiquetas de nombre (cuando hay pocos puntos) */}
          {pts.length <= 8
            ? pts.map((p) => (
                <text
                  key={`l-${p.nombre}`}
                  x={xScale(p.tir)}
                  y={yScale(p.margen) - rScale(p.ventas) - 4}
                  fontSize={10.5}
                  textAnchor="middle"
                  fill="var(--foreground)"
                  className="pointer-events-none"
                >
                  {p.nombre}
                </text>
              ))
            : null}

          <AxisLeft
            scale={yScale}
            numTicks={4}
            tickFormat={(v) => fmtPct(v as number, 0)}
            stroke="transparent"
            tickStroke="transparent"
            tickLabelProps={() => ({ fill: "var(--muted-foreground)", fontSize: 10.5, textAnchor: "end", dx: -4, dy: 3 })}
          />
          <AxisBottom
            top={ih}
            scale={xScale}
            numTicks={5}
            tickFormat={(v) => fmtPct(v as number, 0)}
            stroke="var(--rule)"
            tickStroke="transparent"
            tickLabelProps={() => ({ fill: "var(--muted-foreground)", fontSize: 10.5, textAnchor: "middle", dy: 2 })}
          />
        </Group>
        <text x={M.left + iw / 2} y={height - 4} fontSize={10.5} textAnchor="middle" fill="var(--muted-foreground)">
          TIR apal. ref.
        </text>
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
          <div className="text-sm font-semibold">{tooltipData.nombre}</div>
          <div className="num mt-0.5 text-xs text-muted-foreground">
            TIR {fmtPct(tooltipData.tir)} · margen {fmtPct(tooltipData.margen)}
          </div>
          <div className="num text-xs text-muted-foreground">
            {fmtCop(tooltipData.ventas)} · {tooltipData.tipo}
          </div>
        </TooltipWithBounds>
      ) : null}
    </div>
  );
}

function QuadLabel({ x, y, anchor, text }: { x: number; y: number; anchor: "start" | "end"; text: string }) {
  return (
    <text
      x={x}
      y={y}
      textAnchor={anchor}
      dominantBaseline="hanging"
      fontSize={10}
      fill="var(--muted-foreground)"
      fillOpacity={0.6}
      className="uppercase tracking-wide"
    >
      {text}
    </text>
  );
}
