"use client";

import { useCallback } from "react";
import type { EChartsOption } from "echarts";
import { EChart } from "@/components/charts/echart";
import type { ChartTokens } from "@/lib/chart-tokens";

/** Variación en pasos (ya ×100): -10 → "−10%", 0 → "0", 10 → "+10%". */
function fmtStep(p: number): string {
  const r = Math.round(p);
  if (r === 0) return "0";
  return `${r > 0 ? "+" : "−"}${Math.abs(r)}%`;
}

/** hex (#RRGGBB) → rgba(...) con alfa. */
function rgba(hex: string, a: number): string {
  const h = hex.replace("#", "");
  return `rgba(${parseInt(h.slice(0, 2), 16)}, ${parseInt(h.slice(2, 4), 16)}, ${parseInt(h.slice(4, 6), 16)}, ${a})`;
}

/**
 * Heatmap 2D de margen operativo (ECharts): columnas = variación de PRECIO, filas = variación de COSTO
 * directo; `matriz[i][j]` = margen % (la celda 0/0 es la base, con anillo). Color por celda resuelto en
 * JS (rgba sobre el chart transparente compone sobre la tarjeta = el `color-mix` del CSS): <0 rojo fijo;
 * ≥0 teal escalado por su posición en el rango. Los valores (margen_pct) ya vienen ×100; solo se pintan.
 */
export function Heatmap2D({
  pasosPrecio,
  pasosCosto,
  matriz,
}: {
  pasosPrecio: number[];
  pasosCosto: number[];
  matriz: number[][];
}) {
  const h = pasosCosto.length * 46 + 56;

  const buildOption = useCallback(
    (t: ChartTokens): EChartsOption => {
      const flat = matriz.flat();
      const min = Math.min(...flat);
      const max = Math.max(...flat);
      const span = max - min || 1;

      const cellColor = (v: number): string => {
        if (v < 0) return rgba(t.peligro, 0.38);
        const tt = Math.max(0, Math.min(1, (v - min) / span));
        return rgba(t.primary, (10 + tt * 60) / 100); // 10%..70% de teal
      };

      const data: { value: [number, number, number]; itemStyle: Record<string, unknown> }[] = [];
      for (let i = 0; i < pasosCosto.length; i++) {
        for (let j = 0; j < pasosPrecio.length; j++) {
          const v = matriz[i][j];
          const base = Math.round(pasosPrecio[j]) === 0 && Math.round(pasosCosto[i]) === 0;
          data.push({
            value: [j, i, v],
            itemStyle: {
              color: cellColor(v),
              borderColor: base ? rgba(t.tooltipText, 0.4) : "transparent",
              borderWidth: base ? 2 : 1.5,
              borderRadius: 2,
            },
          });
        }
      }

      return {
        backgroundColor: "transparent",
        animationDuration: 360,
        grid: { top: 10, right: 18, bottom: 36, left: 22, containLabel: true },
        tooltip: {
          backgroundColor: t.tooltipBg,
          borderColor: t.tooltipBorder,
          borderWidth: 1,
          textStyle: { color: t.tooltipText, fontSize: 12 },
          padding: [6, 10],
          formatter: (raw) => {
            const p = raw as unknown as { value: [number, number, number] };
            const [j, i, v] = p.value;
            return `Precio ${fmtStep(pasosPrecio[j])} · Costo ${fmtStep(pasosCosto[i])}<br/><b>margen ${v.toFixed(1)}%</b>`;
          },
        },
        xAxis: {
          type: "category",
          data: pasosPrecio.map(fmtStep),
          name: "VARIACIÓN DE PRECIO",
          nameLocation: "middle",
          nameGap: 24,
          nameTextStyle: { color: t.axisLabel, fontSize: 10, fontWeight: 500 },
          axisLabel: { color: t.axisLabel, fontSize: 11 },
          axisLine: { show: false },
          axisTick: { show: false },
          splitArea: { show: false },
          splitLine: { show: false },
        },
        yAxis: {
          type: "category",
          data: pasosCosto.map(fmtStep),
          inverse: true,
          name: "VARIACIÓN DE COSTO",
          nameLocation: "middle",
          nameGap: 38,
          nameRotate: 90,
          nameTextStyle: { color: t.axisLabel, fontSize: 10, fontWeight: 500 },
          axisLabel: { color: t.axisLabel, fontSize: 11 },
          axisLine: { show: false },
          axisTick: { show: false },
          splitArea: { show: false },
          splitLine: { show: false },
        },
        series: [
          {
            type: "heatmap",
            data,
            label: {
              show: true,
              formatter: (p) => ((p.value as number[])[2] as number).toFixed(1),
              color: t.tooltipText,
              fontSize: 11,
              fontWeight: 500,
            },
          },
        ],
      };
    },
    [pasosPrecio, pasosCosto, matriz],
  );

  return <EChart buildOption={buildOption} height={h} />;
}
