"use client";

import { useCallback } from "react";
import type { EChartsOption } from "echarts";
import { EChart } from "@/components/charts/echart";
import type { ChartTokens } from "@/lib/chart-tokens";

interface VarBar {
  name: string;
  low: number;
  high: number;
  span: number;
}

/** Agrupa "{Var} ±N%" por variable → {low (impacto más negativo), high (más positivo)}, orden por span. */
function toBars(t: Record<string, number>): VarBar[] {
  const by: Record<string, { low: number; high: number }> = {};
  for (const [k, v] of Object.entries(t)) {
    const parts = k.split(" ");
    parts.pop();
    const name = parts.join(" ");
    const b = by[name] ?? { low: 0, high: 0 };
    if (v < 0) b.low = Math.min(b.low, v);
    else b.high = Math.max(b.high, v);
    by[name] = b;
  }
  return Object.entries(by)
    .map(([name, b]) => ({ name, low: b.low, high: b.high, span: b.high - b.low }))
    .sort((a, b) => b.span - a.span);
}

/** Eje en mil M: valor/1e6 con separador de miles por punto, 0 decimales, "0" literal para el cero. */
function tickY(v: number): string {
  if (v === 0) return "0";
  return `${(v / 1_000_000).toLocaleString("en-US", { maximumFractionDigits: 0 }).replace(/,/g, ".")}`;
}

/** Redondea hacia arriba a un número "lindo" (1/2/5 ×10^k) para un dominio simétrico = nice:true de visx. */
function niceCeil(v: number): number {
  if (v <= 0) return 1;
  const mag = Math.pow(10, Math.floor(Math.log10(v)));
  const n = v / mag;
  const nice = n <= 1 ? 1 : n <= 2 ? 2 : n <= 5 ? 5 : 10;
  return nice * mag;
}

/**
 * Tornado de sensibilidad (ECharts): impacto en la utilidad operativa de variar cada variable ±10%.
 * Barras horizontales divergentes centradas en cero; ámbar = a la baja, teal = al alza. Las cifras
 * (deltas de util_oper en miles COP) salen del API; este componente solo agrupa y escala.
 */
export function TornadoChart({ tornado, height }: { tornado: Record<string, number>; height?: number }) {
  const bars = toBars(tornado);
  const h = height ?? bars.length * 48 + 32;

  const buildOption = useCallback(
    (t: ChartTokens): EChartsOption => {
      const maxAbs = niceCeil(Math.max(1, ...bars.flatMap((b) => [Math.abs(b.low), Math.abs(b.high)])));
      return {
        backgroundColor: "transparent",
        animationDuration: 420,
        grid: { left: 8, right: 18, top: 6, bottom: 26, containLabel: true },
        xAxis: {
          type: "value",
          min: -maxAbs,
          max: maxAbs,
          axisLabel: { color: t.axisLabel, fontSize: 10, formatter: (v: number) => tickY(v) },
          axisLine: { lineStyle: { color: t.axisLine } },
          axisTick: { show: false },
          splitLine: { show: false },
        },
        yAxis: {
          type: "category",
          data: bars.map((b) => b.name),
          inverse: true,
          axisLine: { show: false },
          axisTick: { show: false },
          axisLabel: { color: t.tooltipText, fontSize: 12 },
        },
        series: [
          {
            name: "A la baja",
            type: "bar",
            barWidth: 18,
            data: bars.map((b) => b.low),
            itemStyle: { color: t.cgAmber, opacity: 0.85, borderRadius: 2 },
            markLine: {
              symbol: "none",
              silent: true,
              label: { show: false },
              lineStyle: { color: t.tooltipText, width: 1, opacity: 0.3 },
              data: [{ xAxis: 0 }],
            },
          },
          {
            name: "Al alza",
            type: "bar",
            barWidth: 18,
            barGap: "-100%",
            data: bars.map((b) => b.high),
            itemStyle: { color: t.primary, opacity: 0.9, borderRadius: 2 },
          },
        ],
      };
    },
    [bars],
  );

  return <EChart buildOption={buildOption} height={h} />;
}
