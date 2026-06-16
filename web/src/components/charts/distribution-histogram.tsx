"use client";

import { useCallback } from "react";
import type { EChartsOption } from "echarts";
import type { CustomSeriesRenderItemAPI, CustomSeriesRenderItemParams } from "echarts";
import { EChart } from "@/components/charts/echart";
import type { ChartTokens } from "@/lib/chart-tokens";

export interface HistMarker {
  label: string;
  value: number;
  /** Rol del marcador (se resuelve a color del token): muted (P10/P90), strong (P50), danger (meta). */
  tone: "muted" | "strong" | "danger";
  dash?: boolean;
}

/** hex (#RRGGBB) → rgba(...) con alfa. */
function rgba(hex: string, a: number): string {
  const h = hex.replace("#", "");
  return `rgba(${parseInt(h.slice(0, 2), 16)}, ${parseInt(h.slice(2, 4), 16)}, ${parseInt(h.slice(4, 6), 16)}, ${a})`;
}

/**
 * Histograma de la distribución Monte Carlo (ECharts): 28 bins, barras bajo el `hurdle` en rojo (zona
 * de "fracaso"); marcadores verticales P10/P50/P90 + meta. NO aplica greenfield/splitTir: los valores
 * crudos de la distribución son intencionales. El binning y los percentiles vienen del API; este
 * componente solo agrupa para pintar.
 */
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
  const buildOption = useCallback(
    (t: ChartTokens): EChartsOption => {
      if (values.length === 0) return { backgroundColor: "transparent" };

      let lo = Infinity;
      let hi = -Infinity;
      for (const v of values) {
        if (v < lo) lo = v;
        if (v > hi) hi = v;
      }
      const span = hi - lo || 1;
      const bw = span / bins;
      const counts = new Array(bins).fill(0) as number[];
      for (const v of values) {
        let i = Math.floor((v - lo) / bw);
        if (i >= bins) i = bins - 1;
        if (i < 0) i = 0;
        counts[i]++;
      }
      const maxC = Math.max(...counts, 1);
      // [x0, count, x1] por bin → custom renderItem dibuja el rect exacto (como la versión visx).
      const data = counts.map((c, i) => [lo + i * bw, c, lo + (i + 1) * bw]);

      const tone: Record<HistMarker["tone"], string> = {
        muted: t.axisLabel,
        strong: t.tooltipText,
        danger: t.peligro,
      };

      const renderItem = (_p: CustomSeriesRenderItemParams, api: CustomSeriesRenderItemAPI) => {
        const x0 = api.value(0) as number;
        const x1 = api.value(2) as number;
        const below = hurdle != null && (x0 + x1) / 2 < hurdle;
        const p0 = api.coord([x0, 0]);
        const p1 = api.coord([x1, api.value(1) as number]);
        return {
          type: "rect" as const,
          shape: {
            x: p0[0] + 0.5,
            y: p1[1],
            width: Math.max(0, p1[0] - p0[0] - 1),
            height: p0[1] - p1[1],
            r: 1,
          },
          style: { fill: below ? rgba(t.peligro, 0.5) : rgba(t.primary, 0.8) },
        };
      };

      return {
        backgroundColor: "transparent",
        animationDuration: 360,
        grid: { top: 16, right: 14, bottom: 28, left: 10, containLabel: true },
        xAxis: {
          type: "value",
          min: lo,
          max: hi,
          splitNumber: 6,
          axisLabel: { color: t.axisLabel, fontSize: 10, formatter: (v: number) => format(v) },
          axisLine: { lineStyle: { color: t.axisLine } },
          axisTick: { show: false },
          splitLine: { show: false },
        },
        yAxis: { type: "value", min: 0, max: maxC, show: false },
        series: [
          {
            type: "custom",
            renderItem,
            encode: { x: [0, 2], y: 1 },
            data,
            markLine: {
              symbol: "none",
              silent: true,
              data: markers.map((m) => ({
                xAxis: m.value,
                lineStyle: {
                  color: tone[m.tone],
                  type: m.dash ? "dashed" : "solid",
                  width: m.dash ? 1 : 1.5,
                  opacity: 0.9,
                },
                label: {
                  show: true,
                  formatter: m.label,
                  position: "end",
                  color: tone[m.tone],
                  fontSize: 9.5,
                  fontWeight: "bold",
                },
              })),
            },
          },
        ],
      };
    },
    [values, markers, hurdle, format, bins],
  );

  return <EChart buildOption={buildOption} height={height} />;
}
