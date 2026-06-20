"use client";

import { useCallback } from "react";
import type { EChartsOption } from "echarts";
import type { CustomSeriesRenderItemAPI, CustomSeriesRenderItemParams } from "echarts";
import type { MarkAreaComponentOption } from "echarts/components";
import { EChart } from "@/components/charts/echart";
import type { ChartTokens } from "@/lib/chart-tokens";
import { fmtInt, fmtPct } from "@/lib/format";

export interface HistMarker {
  label: string;
  value: number;
  /** Rol del marcador → color del token: muted (P10/P90), strong (P50), mean (media), danger (meta). */
  tone: "muted" | "strong" | "mean" | "danger";
  dash?: boolean;
}

/** hex (#RRGGBB) → rgba(...) con alfa. */
function rgba(hex: string, a: number): string {
  const h = hex.replace("#", "");
  return `rgba(${parseInt(h.slice(0, 2), 16)}, ${parseInt(h.slice(2, 4), 16)}, ${parseInt(h.slice(4, 6), 16)}, ${a})`;
}

/**
 * Histograma de la distribución Monte Carlo (estilo Oracle Crystal Ball). El binning se hace aquí a
 * partir del array crudo de corridas que entrega el motor (M5) — es agrupación de PRESENTACIÓN, no
 * recálculo financiero. Features Crystal Ball:
 *  - tooltip por barra (rango del eje X = rentabilidad/indicador, frecuencia y % acumulado);
 *  - banda de CERTEZA sombreada (región que cumple la meta) con barras dentro en teal vivo y fuera en gris;
 *  - eje de frecuencia (izq) + curva acumulada (S) opcional en eje % (der);
 *  - marcadores P10/P50/P90/media + la meta (umbral) que se mueve en vivo.
 */
export function DistributionHistogram({
  values,
  markers,
  umbral,
  signoMayor = true,
  showCumulative = false,
  format,
  height = 300,
  bins = 30,
}: {
  values: number[];
  markers: HistMarker[];
  /** Umbral activo (meta, puede ser interactivo): dibuja la línea "meta" + la banda de certeza. */
  umbral?: number;
  /** Dirección de la meta: true = "≥" (banda a la derecha), false = "≤" (banda a la izquierda). */
  signoMayor?: boolean;
  /** Muestra la curva de frecuencia acumulada (S) + el eje % derecho. */
  showCumulative?: boolean;
  format: (v: number) => string;
  height?: number;
  bins?: number;
}) {
  const buildOption = useCallback(
    (t: ChartTokens): EChartsOption => {
      if (values.length === 0) return { backgroundColor: "transparent" };

      // --- binning (presentación) ---
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
      const total = values.length;
      const maxC = Math.max(...counts, 1);

      // meta por bin: todo lo que el tooltip necesita (sin recalcular en el formatter).
      let acc = 0;
      const meta = counts.map((c, i) => {
        acc += c;
        return { x0: lo + i * bw, x1: lo + (i + 1) * bw, count: c, pct: c / total, cumPct: acc / total };
      });
      const barData = meta.map((m) => [m.x0, m.count, m.x1]); // encode x:[0,2], y:1
      const cdfData = meta.map((m) => [(m.x0 + m.x1) / 2, m.cumPct * 100]);

      const dentroBanda = (mid: number) =>
        umbral == null ? true : signoMayor ? mid >= umbral : mid <= umbral;
      const gris = rgba(t.axisLabel, 0.3);

      const renderItem = (_p: CustomSeriesRenderItemParams, api: CustomSeriesRenderItemAPI) => {
        const x0 = api.value(0) as number;
        const x1 = api.value(2) as number;
        const dentro = dentroBanda((x0 + x1) / 2);
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
          style: { fill: dentro ? rgba(t.accent, 0.85) : gris },
        };
      };

      const tone: Record<HistMarker["tone"], string> = {
        muted: t.axisLabel,
        strong: t.tooltipText,
        mean: t.primary,
        danger: t.peligro,
      };
      const markLineData = [
        ...markers.map((m) => ({
          xAxis: m.value,
          lineStyle: { color: tone[m.tone], type: m.dash ? ("dashed" as const) : ("solid" as const), width: m.dash ? 1 : 1.5, opacity: 0.9 },
          // la media va abajo para no chocar con P50 (suelen estar muy cerca); el resto arriba.
          label: { show: true, formatter: m.label, position: m.tone === "mean" ? ("start" as const) : ("end" as const), color: tone[m.tone], fontSize: 9.5, fontWeight: "bold" as const },
        })),
        ...(umbral != null
          ? [{
              xAxis: umbral,
              lineStyle: { color: t.tooltipText, type: "dashed" as const, width: 1.5, opacity: 0.95 },
              label: { show: true, formatter: "meta", position: "end" as const, color: t.tooltipText, fontSize: 9.5, fontWeight: "bold" as const },
            }]
          : []),
      ];

      const markArea: MarkAreaComponentOption | undefined =
        umbral == null
          ? undefined
          : {
              silent: true,
              itemStyle: { color: rgba(t.accent, 0.07) },
              data: [[{ xAxis: signoMayor ? umbral : lo }, { xAxis: signoMayor ? hi : umbral }]],
            };

      return {
        backgroundColor: "transparent",
        animationDuration: 360,
        grid: { top: 18, right: showCumulative ? 40 : 14, bottom: 28, left: 8, containLabel: true },
        tooltip: {
          trigger: "item",
          backgroundColor: t.tooltipBg,
          borderColor: t.tooltipBorder,
          borderWidth: 1,
          textStyle: { color: t.tooltipText, fontSize: 12 },
          padding: [6, 10],
          formatter: (raw) => {
            const di = (raw as { dataIndex: number }).dataIndex;
            const m = meta[di];
            if (!m) return "";
            return (
              `<div style="font-weight:600">${format(m.x0)} – ${format(m.x1)}</div>` +
              `<div class="num" style="margin-top:2px">Frecuencia: ${fmtInt(m.count)} (${fmtPct(m.pct, 1)})</div>` +
              `<div class="num" style="color:${t.axisLabel}">Acumulado: ${fmtPct(m.cumPct, 1)}</div>`
            );
          },
        },
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
        yAxis: [
          {
            type: "value",
            min: 0,
            max: maxC,
            show: true,
            axisLabel: { color: t.axisLabel, fontSize: 10, formatter: (v: number) => fmtInt(v) },
            axisLine: { show: false },
            axisTick: { show: false },
            splitLine: { lineStyle: { color: t.grid } },
          },
          {
            type: "value",
            min: 0,
            max: 100,
            show: showCumulative,
            position: "right",
            axisLabel: { color: t.axisLabel, fontSize: 10, formatter: (v: number) => `${v}%` },
            axisLine: { show: false },
            axisTick: { show: false },
            splitLine: { show: false },
          },
        ],
        series: [
          {
            type: "custom" as const,
            renderItem,
            encode: { x: [0, 2], y: 1 },
            data: barData,
            yAxisIndex: 0,
            markArea,
            markLine: { symbol: "none", silent: true, data: markLineData },
          },
          ...(showCumulative
            ? [
                {
                  type: "line" as const,
                  name: "Acumulado",
                  data: cdfData,
                  yAxisIndex: 1,
                  smooth: true,
                  showSymbol: false,
                  lineStyle: { color: t.primary, width: 2 },
                  areaStyle: { color: rgba(t.primary, t.areaOpacity) },
                  z: 5,
                },
              ]
            : []),
        ],
      };
    },
    [values, markers, umbral, signoMayor, showCumulative, format, bins],
  );

  return <EChart buildOption={buildOption} height={height} />;
}
