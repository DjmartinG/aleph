"use client";

import { useCallback } from "react";
import type { EChartsOption } from "echarts";
import { EChart } from "@/components/charts/echart";
import type { ChartTokens } from "@/lib/chart-tokens";
import { timeXAxis, hoyMarkLine } from "@/lib/echarts-timeline";
import { fmtCop } from "@/lib/format";
import { monthLabel } from "@/lib/timeline";

/** Eje Y en "mil M" sin sufijo (lo dice el título): valores en miles COP → /1e6. */
function tickY(v: number): string {
  if (v === 0) return "0";
  return `${(v / 1_000_000).toLocaleString("en-US", { maximumFractionDigits: 0 }).replace(/,/g, ".")}`;
}

type AxisParam = { axisValue: number };

/**
 * Recaudo mensual apilado (ECharts): separación + cuota inicial + subrogación (crédito hipotecario).
 * Orden de apilado FIJO (separación abajo) con opacidades distintas por capa; eje temporal por años +
 * "Hoy"; eje Y en mil M. Colores de marca (separación=ámbar, subrogación=teal, cuota inicial=neutro).
 */
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
  const n = subrogacion.length;

  const buildOption = useCallback(
    (t: ChartTokens): EChartsOption => {
      const totales = subrogacion.map((_, m) => (separacion[m] ?? 0) + (cuotaInicial[m] ?? 0) + (subrogacion[m] ?? 0));
      const maxTotal = Math.max(1, ...totales);

      // Orden de apilado: separación (abajo) → cuota inicial → subrogación. Colores y opacidades por capa.
      const capas = [
        { name: "Separación", serie: separacion, color: t.cgAmber, opacity: 0.55 },
        { name: "Cuota inicial", serie: cuotaInicial, color: t.axisLabel, opacity: 0.4 },
        { name: "Subrogación", serie: subrogacion, color: t.primary, opacity: 0.28 },
      ];

      return {
        backgroundColor: "transparent",
        animationDuration: 420,
        grid: { left: 40, right: 16, top: 20, bottom: 28 },
        tooltip: {
          trigger: "axis",
          backgroundColor: t.tooltipBg,
          borderColor: t.tooltipBorder,
          borderWidth: 1,
          textStyle: { color: t.tooltipText, fontSize: 12 },
          padding: [6, 10],
          axisPointer: { type: "line", lineStyle: { color: t.axisLabel, opacity: 0.3 } },
          formatter: (raw) => {
            const m = (raw as unknown as AxisParam[])[0]?.axisValue ?? 0;
            const s = separacion[m] ?? 0;
            const c = cuotaInicial[m] ?? 0;
            const sub = subrogacion[m] ?? 0;
            return (
              `<div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:.04em;color:${t.axisLabel}">${monthLabel(baseDate, m)}</div>` +
              `<div style="margin-top:2px;font-weight:600" class="num">${fmtCop(s + c + sub)}</div>` +
              `<div style="margin-top:2px;color:${t.axisLabel}" class="num">Subrogación ${fmtCop(sub)}</div>` +
              `<div style="color:${t.axisLabel}" class="num">Cuota inicial ${fmtCop(c)}</div>` +
              `<div style="color:${t.axisLabel}" class="num">Separación ${fmtCop(s)}</div>`
            );
          },
        },
        xAxis: timeXAxis(baseDate, n, t),
        yAxis: {
          type: "value",
          min: 0,
          max: maxTotal * 1.08,
          splitNumber: 4,
          axisLabel: { color: t.axisLabel, fontSize: 10.5, formatter: (v: number) => tickY(v) },
          axisLine: { show: false },
          axisTick: { show: false },
          splitLine: { lineStyle: { color: t.grid, opacity: 0.7 } },
        },
        series: capas.map((cap, idx) => ({
          name: cap.name,
          type: "line",
          stack: "recaudo",
          smooth: true,
          showSymbol: false,
          data: cap.serie.map((v, m) => [m, v ?? 0]),
          lineStyle: { color: cap.color, width: 0.75, opacity: 0.5 },
          areaStyle: { color: cap.color, opacity: cap.opacity },
          ...(idx === capas.length - 1 ? { markLine: hoyMarkLine(baseDate, n, t) } : {}),
        })),
      };
    },
    [separacion, cuotaInicial, subrogacion, baseDate, n],
  );

  return <EChart buildOption={buildOption} height={height} />;
}
