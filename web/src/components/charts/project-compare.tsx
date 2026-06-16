"use client";

import { useCallback, useMemo, useState } from "react";
import type { EChartsOption } from "echarts";
import { EChart } from "@/components/charts/echart";
import { chartTokens, type ChartTokens } from "@/lib/chart-tokens";
import { useIsDark } from "@/lib/use-is-dark";
import type { ProjectItem } from "@/lib/api";
import { fmtCop, fmtPct, tirEsDegenerada } from "@/lib/format";
import { cn } from "@/lib/utils";

/** Eje Y en "mil M" sin sufijo: valores en miles COP → /1e6. */
function tickY(v: number): string {
  if (v === 0) return "0";
  return `${(v / 1_000_000).toLocaleString("en-US", { maximumFractionDigits: 0 }).replace(/,/g, ".")}`;
}

type Axis = "pct" | "cop";
interface Metric {
  id: string;
  label: string;
  axis: Axis;
  zero?: boolean; // dibuja línea de cero (valores que pueden ser negativos)
  tir?: boolean; // aplica regla greenfield (no graficar TIR degenerada)
  get: (i: ProjectItem) => number | null;
}

const METRICS: Metric[] = [
  { id: "tir", label: "TIR apal. ref.", axis: "pct", tir: true, get: (i) => i.tir },
  { id: "margen", label: "Margen", axis: "pct", get: (i) => i.margen },
  { id: "vpn", label: "VPN @TIO", axis: "cop", zero: true, get: (i) => i.vpn },
  { id: "ventas", label: "Ventas", axis: "cop", get: (i) => i.ventas },
  { id: "valor", label: "Valor creado (EVA)", axis: "cop", zero: true, get: (i) => i.valor_creado },
];

const MAX_SEL = 6;

/**
 * Comparador de proyectos (ECharts): elige 2+ proyectos del portafolio y compáralos en una métrica de
 * decisión a la vez (barras con VALORES y EJE reales — TIR/margen en %, VPN/ventas/valor en mil M).
 * Honesto por diseño: respeta `splitTir` (greenfield no se grafica) y la línea de cero para negativos.
 * Cero datos nuevos: todo de los `items` que el dashboard ya trae de /v1/portfolio.
 */
export function ProjectCompare({ items }: { items: ProjectItem[] }) {
  const [sel, setSel] = useState<string[]>(() => items.slice(0, Math.min(3, items.length)).map((i) => i.slug));
  const [metricId, setMetricId] = useState<string>("tir");
  const metric = METRICS.find((m) => m.id === metricId) ?? METRICS[0];
  const isDark = useIsDark();
  const palette = chartTokens(isDark).palette;

  const selItems = useMemo(() => sel.map((s) => items.find((i) => i.slug === s)).filter((x): x is ProjectItem => !!x), [sel, items]);

  const greenfieldOmitidos = metric.tir ? selItems.filter((i) => tirEsDegenerada(i.tir)).length : 0;

  function toggle(slug: string) {
    setSel((prev) => {
      if (prev.includes(slug)) return prev.length > 1 ? prev.filter((s) => s !== slug) : prev; // mínimo 1
      if (prev.length >= MAX_SEL) return prev;
      return [...prev, slug];
    });
  }

  const buildOption = useCallback(
    (t: ChartTokens): EChartsOption => {
      const data = selItems.map((i, idx) => {
        const raw = metric.get(i);
        const v = metric.tir && tirEsDegenerada(raw) ? null : raw;
        return { value: v, itemStyle: { color: t.palette[idx % t.palette.length], borderRadius: 3 } };
      });
      const fmt = (v: number) => (metric.axis === "pct" ? fmtPct(v) : fmtCop(v));

      return {
        backgroundColor: "transparent",
        animationDuration: 480,
        grid: { left: 8, right: 14, top: 28, bottom: 24, containLabel: true },
        tooltip: {
          trigger: "item",
          backgroundColor: t.tooltipBg,
          borderColor: t.tooltipBorder,
          borderWidth: 1,
          textStyle: { color: t.tooltipText, fontSize: 12 },
          padding: [6, 10],
          formatter: (raw) => {
            const p = raw as { dataIndex: number; value: number | null };
            const it = selItems[p.dataIndex];
            const txt = p.value == null ? "— greenfield" : fmt(p.value);
            return `<div style="font-weight:600">${it.nombre}</div><div class="num" style="margin-top:2px">${metric.label}: ${txt}</div>`;
          },
        },
        xAxis: {
          type: "category",
          data: selItems.map((i) => i.nombre),
          axisLabel: { color: t.axisLabel, fontSize: 11, interval: 0, hideOverlap: true },
          axisLine: { lineStyle: { color: t.axisLine } },
          axisTick: { show: false },
        },
        yAxis: {
          type: "value",
          axisLabel: {
            color: t.axisLabel,
            fontSize: 10.5,
            formatter: (v: number) => (metric.axis === "pct" ? fmtPct(v, 0) : tickY(v)),
          },
          axisLine: { show: false },
          axisTick: { show: false },
          splitLine: { lineStyle: { color: t.grid, opacity: 0.7 } },
        },
        series: [
          {
            type: "bar",
            data,
            barWidth: "48%",
            barMaxWidth: 64,
            label: {
              show: true,
              position: "top",
              formatter: (p) => (p.value == null ? "—" : fmt(p.value as number)),
              color: t.tooltipText,
              fontSize: 11,
              fontWeight: "bold",
            },
            markLine: metric.zero
              ? {
                  symbol: "none",
                  silent: true,
                  label: { show: false },
                  lineStyle: { color: t.axisLine, width: 1, opacity: 0.8 },
                  data: [{ yAxis: 0 }],
                }
              : undefined,
          },
        ],
      };
    },
    [selItems, metric],
  );

  return (
    <div>
      {/* Selector de proyectos */}
      <div className="mb-3 flex flex-wrap gap-1.5">
        {items.map((i) => {
          const on = sel.includes(i.slug);
          const pos = sel.indexOf(i.slug);
          return (
            <button
              key={i.slug}
              type="button"
              onClick={() => toggle(i.slug)}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs transition-colors [transition-timing-function:var(--ease-out)]",
                on ? "border-primary/40 bg-primary/10 text-foreground" : "border-border bg-card text-muted-foreground hover:text-foreground",
              )}
            >
              <span
                className="size-2 rounded-full"
                style={{ background: on ? palette[pos % palette.length] : "var(--muted-foreground)", opacity: on ? 1 : 0.4 }}
              />
              {i.nombre}
            </button>
          );
        })}
      </div>

      {/* Selector de métrica */}
      <div className="mb-3 inline-flex flex-wrap rounded-[var(--radius-data)] border bg-card p-0.5 text-sm">
        {METRICS.map((m) => (
          <button
            key={m.id}
            type="button"
            onClick={() => setMetricId(m.id)}
            className={cn(
              "rounded-[3px] px-3 py-1 font-medium transition-colors [transition-timing-function:var(--ease-out)]",
              metricId === m.id ? "bg-accent text-accent-foreground" : "text-muted-foreground hover:text-foreground",
            )}
          >
            {m.label}
          </button>
        ))}
      </div>

      <EChart buildOption={buildOption} height={300} exportName={`aleph-comparador-${metric.id}`} />

      {greenfieldOmitidos > 0 ? (
        <div className="mt-2 text-xs text-muted-foreground">
          {greenfieldOmitidos} proyecto{greenfieldOmitidos > 1 ? "s" : ""} sin TIR significativa (greenfield) — sin barra.
        </div>
      ) : null}
    </div>
  );
}
