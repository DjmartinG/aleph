"use client";

import { useCallback } from "react";
import type { EChartsOption } from "echarts";
import type { CustomSeriesRenderItemAPI, CustomSeriesRenderItemParams } from "echarts";
import { EChart } from "@/components/charts/echart";
import type { ChartTokens } from "@/lib/chart-tokens";
import type { ScheduleEtapa } from "@/lib/api";
import { timeXAxis, hoyMarkLine } from "@/lib/echarts-timeline";

const ROW = 46;

function truncate(s: string, n: number): string {
  return s.length > n ? `${s.slice(0, n - 1)}…` : s;
}

/** hex (#RRGGBB) → rgba(...) con alfa. */
function rgba(hex: string, a: number): string {
  const h = hex.replace("#", "");
  return `rgba(${parseInt(h.slice(0, 2), 16)}, ${parseInt(h.slice(2, 4), 16)}, ${parseInt(h.slice(4, 6), 16)}, ${a})`;
}

/**
 * Gantt de etapas (ECharts custom series): barra de ventas (IV→FV, teal) con marca de equilibrio (PE,
 * anillo hueco) y barra de construcción (IC→FC, ámbar de marca), en pistas separadas. Eje temporal por
 * años + marcador "Hoy". Los hitos (en meses) vienen del API; este componente solo los posiciona.
 */
export function GanttChart({
  etapas,
  horizonte,
  baseDate,
}: {
  etapas: ScheduleEtapa[];
  horizonte: number;
  baseDate: string | null;
}) {
  const height = etapas.length * ROW + 50;

  const buildOption = useCallback(
    (t: ChartTokens): EChartsOption => {
      const data = etapas.map((e, i) => [i, e.iv_mes, e.fv_mes, e.pe_mes, e.ic_mes, e.fc_mes]);

      const renderItem = (_p: CustomSeriesRenderItemParams, api: CustomSeriesRenderItemAPI) => {
        const ci = api.value(0) as number;
        const px = (m: number) => api.coord([m, ci])[0];
        const yc = api.coord([0, ci])[1];
        const vx = px(api.value(1) as number);
        const vw = Math.max(2, px(api.value(2) as number) - vx);
        const cx = px(api.value(4) as number);
        const cw = Math.max(2, px(api.value(5) as number) - cx);
        return {
          type: "group" as const,
          children: [
            { type: "rect" as const, shape: { x: vx, y: yc - 13, width: vw, height: 10, r: 3 }, style: { fill: rgba(t.primary, 0.85) } },
            {
              type: "circle" as const,
              shape: { cx: px(api.value(3) as number), cy: yc - 8, r: 3.2 },
              style: { fill: t.tooltipBg, stroke: t.primary, lineWidth: 1.6 },
            },
            { type: "rect" as const, shape: { x: cx, y: yc + 3, width: cw, height: 10, r: 3 }, style: { fill: rgba(t.cgAmber, 0.85) } },
          ],
        };
      };

      return {
        backgroundColor: "transparent",
        animationDuration: 420,
        grid: { left: 146, right: 18, top: 22, bottom: 28 },
        xAxis: timeXAxis(baseDate, horizonte, t),
        yAxis: {
          type: "category",
          data: etapas.map((e) => String(e.cod)),
          inverse: true,
          axisLine: { show: false },
          axisTick: { show: false },
          splitLine: { show: true, lineStyle: { color: t.grid, opacity: 0.6 } },
          axisLabel: {
            margin: 12,
            formatter: (_v: string, idx: number) =>
              `{n|${truncate(etapas[idx].nombre, 19)}}\n{u|${etapas[idx].unidades} und}`,
            rich: {
              n: { color: t.tooltipText, fontSize: 12, fontWeight: "bold", align: "left", lineHeight: 16 },
              u: { color: t.axisLabel, fontSize: 10.5, align: "left", lineHeight: 14 },
            },
          },
        },
        series: [
          {
            type: "custom",
            renderItem,
            encode: { x: [1, 2, 3, 4, 5], y: 0 },
            data,
            markLine: hoyMarkLine(baseDate, horizonte, t),
          },
        ],
      };
    },
    [etapas, horizonte, baseDate],
  );

  return <EChart buildOption={buildOption} height={height} />;
}
