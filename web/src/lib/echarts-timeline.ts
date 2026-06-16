/**
 * Helpers ECharts para las gráficas del CRONOGRAMA (eje temporal en meses desde `base_date`):
 * un eje X `value` con marcas y gridlines SOLO en enero de cada año (vía `customValues`, ECharts ≥5.5)
 * y el marcador "Hoy" FRACCIONAL como markLine (idéntico look al de la gráfica de Flujo). El eje debe
 * ser `value` (no `category`) para que el "Hoy" fraccional caiga en su posición exacta.
 */
import type { EChartsOption, LineSeriesOption, DataZoomComponentOption } from "echarts";
import type { ChartTokens } from "@/lib/chart-tokens";
import { yearTicks, mesesHastaHoy } from "@/lib/timeline";

type XAxisOption = NonNullable<EChartsOption["xAxis"]>;
type MarkLineOption = NonNullable<LineSeriesOption["markLine"]>;

/** hex (#RRGGBB) → rgba(...) con alfa. */
function rgba(hex: string, a: number): string {
  const h = hex.replace("#", "");
  return `rgba(${parseInt(h.slice(0, 2), 16)}, ${parseInt(h.slice(2, 4), 16)}, ${parseInt(h.slice(4, 6), 16)}, ${a})`;
}

/**
 * Slider de ZOOM TEMPORAL para las series mensuales largas (flujo/absorción/recaudo): arrastra los
 * tiradores para acotar la ventana, o el centro para desplazarla. Estilizado con los tokens del tema.
 * Reserva ~26px abajo (subir `grid.bottom` y la altura de la gráfica en consecuencia).
 */
export function timeDataZoom(t: ChartTokens): DataZoomComponentOption {
  return {
    type: "slider",
    height: 16,
    bottom: 6,
    showDetail: false,
    brushSelect: false,
    borderColor: "transparent",
    backgroundColor: "transparent",
    fillerColor: rgba(t.primary, 0.1),
    dataBackground: { lineStyle: { color: t.axisLine, width: 0.5 }, areaStyle: { color: "transparent" } },
    selectedDataBackground: { lineStyle: { color: t.primary, width: 0.8, opacity: 0.5 }, areaStyle: { color: rgba(t.primary, 0.12) } },
    handleStyle: { color: t.tooltipBg, borderColor: t.primary, borderWidth: 1.2 },
    moveHandleStyle: { color: t.primary, opacity: 0.5 },
    handleSize: "70%",
    textStyle: { color: t.axisLabel },
  };
}

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
