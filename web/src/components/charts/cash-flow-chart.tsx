"use client";

import { useCallback } from "react";
import type { EChartsOption } from "echarts";
import type { LineSeriesOption } from "echarts/charts";
import { EChart } from "@/components/charts/echart";
import type { ChartTokens } from "@/lib/chart-tokens";
import { mesesHastaHoy } from "@/lib/timeline";
import { fmtCop } from "@/lib/format";

export interface CashPoint {
  m: number;
  acum: number;
  credito: number;
}

/** Eje Y compacto: magnitud en "mil M" sin el sufijo (lo dice el título de la gráfica). */
function tickY(v: number): string {
  if (v === 0) return "0";
  return `${(v / 1_000_000).toLocaleString("en-US", { maximumFractionDigits: 0 }).replace(/,/g, ".")}`;
}

type AxisParam = { seriesName?: string; value: number[] };
type MarkLineData = NonNullable<NonNullable<LineSeriesOption["markLine"]>["data"]>;

/**
 * Flujo de caja mensual (ECharts): caja acumulada (área + línea, teal) + crédito (línea punteada
 * terracota), con la exposición máxima marcada y la línea "Hoy". Las cifras salen tal cual del motor;
 * el toggle proyecto/inversionista vive en FlujoView (este componente solo pinta los datos que recibe).
 */
export function CashFlowChart({
  data,
  maxExposure,
  baseDate = null,
  height = 320,
}: {
  data: CashPoint[];
  maxExposure: { m: number; value: number } | null;
  baseDate?: string | null;
  height?: number;
}) {
  const n = data.length;
  const hoy = mesesHastaHoy(baseDate);
  const hoyEnRango = hoy != null && hoy >= 0 && hoy <= Math.max(1, n - 1);

  const buildOption = useCallback(
    (t: ChartTokens): EChartsOption => {
      const caja = data.map((d) => [d.m, d.acum]);
      const cred = data.map((d) => [d.m, d.credito]);
      const terracota = t.palette[5];

      const markLineData: MarkLineData = [
        { yAxis: 0, label: { show: false }, lineStyle: { color: t.axisLabel, type: "dashed", width: 1, opacity: 0.5 } },
      ];
      if (maxExposure) {
        markLineData.push({
          xAxis: maxExposure.m,
          label: { show: false },
          lineStyle: { color: t.peligro, type: "dashed", width: 1, opacity: 0.5 },
        });
      }
      if (hoyEnRango) {
        markLineData.push({
          xAxis: hoy,
          label: {
            show: true,
            formatter: "Hoy",
            position: "end",
            color: t.tooltipText,
            backgroundColor: t.axisLabel,
            padding: [2, 5],
            borderRadius: 3,
            fontSize: 9.5,
            fontWeight: 600,
          },
          lineStyle: { color: t.axisLabel, type: "dashed", width: 1.25, opacity: 0.7 },
        });
      }

      return {
        backgroundColor: "transparent",
        animationDuration: 420,
        grid: { top: 22, right: 16, bottom: 26, left: 8, containLabel: true },
        tooltip: {
          trigger: "axis",
          backgroundColor: t.tooltipBg,
          borderColor: t.tooltipBorder,
          borderWidth: 1,
          textStyle: { color: t.tooltipText, fontSize: 12 },
          padding: [6, 10],
          formatter: (params) => {
            const arr = params as unknown as AxisParam[];
            const m = (arr[0]?.value?.[0] ?? 0) as number;
            const cj = arr.find((p) => p.seriesName === "Caja acumulada")?.value?.[1];
            const cr = arr.find((p) => p.seriesName === "Crédito")?.value?.[1];
            const head = `Año ${Math.floor(m / 12) + 1}, mes ${(m % 12) + 1}`;
            let html = `<div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:.04em;color:${t.axisLabel}">${head}</div>`;
            if (cj != null) html += `<div style="margin-top:2px;font-weight:600">Caja ${fmtCop(cj)}</div>`;
            if (cr != null && cr > 0) html += `<div style="color:${t.axisLabel}">Crédito ${fmtCop(cr)}</div>`;
            return html;
          },
        },
        xAxis: {
          type: "value",
          min: 0,
          max: Math.max(1, n - 1),
          axisLabel: { color: t.axisLabel, fontSize: 11, formatter: (v: number) => `${Math.round(v / 12)}a` },
          axisLine: { lineStyle: { color: t.axisLine } },
          axisTick: { show: false },
          splitLine: { show: false },
        },
        yAxis: {
          type: "value",
          axisLabel: { color: t.axisLabel, fontSize: 11, formatter: (v: number) => tickY(v) },
          axisLine: { show: false },
          axisTick: { show: false },
          splitLine: { lineStyle: { color: t.grid } },
        },
        series: [
          {
            name: "Caja acumulada",
            type: "line",
            smooth: true,
            showSymbol: false,
            data: caja,
            z: 3,
            lineStyle: { color: t.primary, width: 2.25 },
            areaStyle: { color: t.primary, opacity: t.areaOpacity },
            markPoint: maxExposure
              ? {
                  symbol: "circle",
                  symbolSize: 9,
                  data: [
                    {
                      name: "Exposición máxima",
                      coord: [maxExposure.m, maxExposure.value],
                      itemStyle: { color: t.peligro, borderColor: t.tooltipBg, borderWidth: 2 },
                      label: {
                        show: true,
                        formatter: `Exp. máx ${fmtCop(maxExposure.value)}`,
                        position: "bottom",
                        color: t.peligro,
                        fontSize: 10,
                        fontWeight: 600,
                      },
                    },
                  ],
                }
              : undefined,
            markLine: { symbol: "none", silent: true, data: markLineData },
          },
          {
            name: "Crédito",
            type: "line",
            smooth: true,
            showSymbol: false,
            data: cred,
            z: 2,
            lineStyle: { color: terracota, width: 1.5, type: "dashed" },
          },
        ],
      };
    },
    [data, maxExposure, hoy, hoyEnRango, n],
  );

  return <EChart buildOption={buildOption} height={height} />;
}
