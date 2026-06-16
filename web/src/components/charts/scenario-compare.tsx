"use client";

import { useCallback } from "react";
import type { EChartsOption } from "echarts";
import { EChart } from "@/components/charts/echart";
import type { ChartTokens } from "@/lib/chart-tokens";
import type { EscenarioVals } from "@/lib/api";
import { fmtCop, fmtPct } from "@/lib/format";

const ORDER = ["Optimista", "Base", "Pesimista"];

type Row = { name: string } & EscenarioVals;

/**
 * Comparador de escenarios (ECharts): barras horizontales divergentes de utilidad operativa, una fila
 * por escenario (orden fijo Optimista/Base/Pesimista), con el valor (fmtCop) y el margen (fmtPct) al
 * final de la barra. Color = IDENTIDAD del escenario (verde/teal/rojo, excepción consciente). Las
 * cifras salen del API; este componente solo pinta `util_oper` y `margen`.
 */
export function ScenarioCompare({ escenarios }: { escenarios: Record<string, EscenarioVals> }) {
  const rows: Row[] = ORDER.filter((k) => escenarios[k]).map((k) => ({ name: k, ...escenarios[k] }));
  const h = rows.length * 54 + 12;

  const buildOption = useCallback(
    (t: ChartTokens): EChartsOption => {
      const color: Record<string, string> = {
        Optimista: t.exito,
        Base: t.primary,
        Pesimista: t.peligro,
      };
      const vals = rows.map((r) => r.util_oper);
      const lo = Math.min(0, ...vals);
      const hi = Math.max(0, ...vals);

      return {
        backgroundColor: "transparent",
        animationDuration: 420,
        grid: { left: 88, right: 128, top: 6, bottom: 6 },
        xAxis: { type: "value", min: lo, max: hi, show: false },
        yAxis: {
          type: "category",
          data: rows.map((r) => r.name),
          inverse: true,
          axisLine: { show: false },
          axisTick: { show: false },
          axisLabel: { color: t.tooltipText, fontSize: 13, fontWeight: 500 },
        },
        series: [
          {
            type: "bar",
            barWidth: 22,
            data: rows.map((r) => ({
              value: r.util_oper,
              itemStyle: { color: color[r.name] ?? t.axisLabel, borderRadius: 2 },
            })),
            label: {
              show: true,
              position: "right", // extremo exterior de cada barra (las negativas, junto al cero)
              formatter: (p) => {
                const r = rows[p.dataIndex];
                return `{val|${fmtCop(r.util_oper)}}\n{mg|margen ${fmtPct(r.margen)}}`;
              },
              rich: {
                val: { color: t.tooltipText, fontWeight: 600, fontSize: 12.5, lineHeight: 16 },
                mg: { color: t.axisLabel, fontSize: 11, lineHeight: 14 },
              },
            },
            markLine: {
              symbol: "none",
              silent: true,
              label: { show: false },
              lineStyle: { color: t.axisLine, width: 1, type: "solid", opacity: 1 },
              data: [{ xAxis: 0 }],
            },
          },
        ],
      };
    },
    [rows],
  );

  return <EChart buildOption={buildOption} height={h} />;
}
