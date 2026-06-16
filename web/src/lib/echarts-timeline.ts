/**
 * Helpers ECharts para las gráficas del CRONOGRAMA (eje temporal en meses desde `base_date`):
 * un eje X `value` con marcas y gridlines SOLO en enero de cada año (vía `customValues`, ECharts ≥5.5)
 * y el marcador "Hoy" FRACCIONAL como markLine (idéntico look al de la gráfica de Flujo). El eje debe
 * ser `value` (no `category`) para que el "Hoy" fraccional caiga en su posición exacta.
 */
import type { EChartsOption, LineSeriesOption } from "echarts";
import type { ChartTokens } from "@/lib/chart-tokens";
import { yearTicks, mesesHastaHoy } from "@/lib/timeline";

type XAxisOption = NonNullable<EChartsOption["xAxis"]>;
type MarkLineOption = NonNullable<LineSeriesOption["markLine"]>;

/** Eje X temporal: dominio [0, horizonte-1], etiquetas/gridlines de año en su mes de enero. */
export function timeXAxis(baseDate: string | null, horizonte: number, t: ChartTokens): XAxisOption {
  const ticks = yearTicks(baseDate, horizonte);
  const ms = ticks.map((k) => k.m);
  const labelByM: Record<number, string> = {};
  ticks.forEach((k) => (labelByM[k.m] = k.label));
  return {
    type: "value",
    min: 0,
    max: Math.max(1, horizonte - 1),
    axisLabel: {
      color: t.axisLabel,
      fontSize: 11,
      customValues: ms,
      formatter: (v: number) => labelByM[Math.round(v)] ?? "",
    },
    axisTick: { show: false },
    axisLine: { lineStyle: { color: t.axisLine } },
    splitLine: ms.length
      ? { show: true, customValues: ms, lineStyle: { color: t.grid, opacity: 0.7 } }
      : { show: false },
  } as XAxisOption;
}

/** markLine "Hoy" (línea punteada neutra + pill arriba), o sin `data` si Hoy cae fuera del horizonte. */
export function hoyMarkLine(baseDate: string | null, horizonte: number, t: ChartTokens): MarkLineOption {
  const hoy = mesesHastaHoy(baseDate);
  const dentro = hoy != null && hoy >= 0 && hoy <= Math.max(1, horizonte - 1);
  return {
    symbol: "none",
    silent: true,
    data: dentro
      ? [
          {
            xAxis: hoy as number,
            lineStyle: { color: t.axisLabel, type: "dashed", width: 1.25, opacity: 0.7 },
            label: {
              show: true,
              formatter: "Hoy",
              position: "end",
              color: t.tooltipText,
              backgroundColor: t.axisLabel,
              padding: [2, 5],
              borderRadius: 3,
              fontSize: 9.5,
              fontWeight: "bold",
            },
          },
        ]
      : [],
  };
}
