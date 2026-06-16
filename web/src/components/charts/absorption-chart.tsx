"use client";

import { useCallback } from "react";
import type { EChartsOption } from "echarts";
import { EChart } from "@/components/charts/echart";
import type { ChartTokens } from "@/lib/chart-tokens";
import { timeXAxis, hoyMarkLine, timeDataZoom } from "@/lib/echarts-timeline";
import { fmtInt } from "@/lib/format";
import { monthLabel } from "@/lib/timeline";

/** hex (#RRGGBB) → rgba(...) con alfa. */
function rgba(hex: string, a: number): string {
  const h = hex.replace("#", "");
  return `rgba(${parseInt(h.slice(0, 2), 16)}, ${parseInt(h.slice(2, 4), 16)}, ${parseInt(h.slice(4, 6), 16)}, ${a})`;
}

type AxisParam = { axisValue: number; seriesName?: string; value: [number, number] };

/**
 * Curva de absorción (ECharts): barras de unidades vendidas por mes (teal tenue, eje izq.) + línea de
 * acumulado (eje der., escala distinta hasta el total). Eje temporal por años + "Hoy". Unidades con
 * fmtInt (nunca fmtCop). Las series vienen del API; este componente solo las pinta.
 */
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
  const n = ventas.length;
  const h = height + 28; // +slider de zoom temporal

  const buildOption = useCallback(
    (t: ChartTokens): EChartsOption => {
      const maxVentas = Math.max(1, ...ventas);
      const barData = ventas.map((v, m) => [m, v]);
      const lineData = acum.map((v, m) => [m, v ?? 0]);

      return {
        backgroundColor: "transparent",
        animationDuration: 420,
        grid: { left: 36, right: 40, top: 20, bottom: 50 },
        dataZoom: [timeDataZoom(t)],
        tooltip: {
          trigger: "axis",
          backgroundColor: t.tooltipBg,
          borderColor: t.tooltipBorder,
          borderWidth: 1,
          textStyle: { color: t.tooltipText, fontSize: 12 },
          padding: [6, 10],
          axisPointer: { type: "line", lineStyle: { color: t.axisLabel, opacity: 0.3 } },
          formatter: (raw) => {
            const arr = raw as unknown as AxisParam[];
            const m = arr[0]?.axisValue ?? 0;
            const vt = arr.find((p) => p.seriesName === "Unidades/mes")?.value?.[1];
            const ac = arr.find((p) => p.seriesName === "Acumulado")?.value?.[1];
            return (
              `<div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:.04em;color:${t.axisLabel}">${monthLabel(baseDate, m)}</div>` +
              `<div style="margin-top:2px;font-weight:600" class="num">${fmtInt(vt ?? 0)} und/mes</div>` +
              `<div style="color:${t.axisLabel}" class="num">${fmtInt(ac ?? 0)} acum.</div>`
            );
          },
        },
        xAxis: timeXAxis(baseDate, n, t),
        yAxis: [
          {
            type: "value",
            min: 0,
            max: maxVentas * 1.1,
            splitNumber: 4,
            axisLabel: { color: t.axisLabel, fontSize: 10.5 },
            axisLine: { show: false },
            axisTick: { show: false },
            splitLine: { lineStyle: { color: t.grid, opacity: 0.7 } },
          },
          {
            type: "value",
            min: 0,
            max: Math.max(1, total),
            splitNumber: 4,
            axisLabel: { color: t.axisLabel, fontSize: 10.5 },
            axisLine: { show: false },
            axisTick: { show: false },
            splitLine: { show: false },
          },
        ],
        series: [
          {
            name: "Unidades/mes",
            type: "bar",
            yAxisIndex: 0,
            data: barData,
            barWidth: "62%",
            itemStyle: { color: rgba(t.primary, 0.32), borderRadius: 1.5 },
            z: 1,
          },
          {
            name: "Acumulado",
            type: "line",
            yAxisIndex: 1,
            data: lineData,
            smooth: true,
            showSymbol: false,
            lineStyle: { color: t.primary, width: 2.25 },
            z: 2,
            markLine: hoyMarkLine(baseDate, n, t),
          },
        ],
      };
    },
    [ventas, acum, total, baseDate, n],
  );

  return <EChart buildOption={buildOption} height={h} exportName="aleph-absorcion" />;
}
