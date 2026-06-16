"use client";

import { useCallback, useMemo } from "react";
import type { EChartsOption } from "echarts";
import type { ScatterSeriesOption } from "echarts/charts";
import { EChart } from "@/components/charts/echart";
import type { ChartTokens } from "@/lib/chart-tokens";
import type { ProjectItem } from "@/lib/api";
import { fmtCop, fmtPct, TIR_DEGENERADA } from "@/lib/format";

interface Pt {
  nombre: string;
  tir: number;
  margen: number;
  ventas: number;
  tipo: string;
  und: number;
}

/** ¿"No VIS"? (color ámbar de marca; el resto va teal). Misma regex que la versión visx. */
function esNoVis(tipo: string): boolean {
  return /no\s*vis/i.test(tipo);
}

/** hex (#RRGGBB) → rgba(...) con alfa (para burbuja hueca: relleno 0.22, borde 0.85). */
function rgba(hex: string, a: number): string {
  const h = hex.replace("#", "");
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${a})`;
}

/** Escala de radio por ventas: sqrt, dominio [0, max], rango de RADIO [7,26] (= la visx). */
function radio(v: number, max: number): number {
  return 7 + 19 * Math.sqrt(Math.max(0, v) / (max || 1));
}

/**
 * Mapa de valor del portafolio (ECharts): TIR apal. ref. (X) × margen operativo (Y); tamaño = ventas,
 * color = tipo (VIS teal / No VIS ámbar de marca). Cruz de cuadrantes en los umbrales de industria
 * (TIR 30%, margen 5%). Las cifras salen del API (items ya greenfield-safe); este componente solo pinta.
 */
export function ValueMap({
  items,
  tirRef = 0.3,
  margenRef = 0.05,
  height = 380,
}: {
  items: ProjectItem[];
  tirRef?: number;
  margenRef?: number;
  height?: number;
}) {
  const pts: Pt[] = useMemo(
    () =>
      items
        .filter((i) => i.tir != null && i.tir > TIR_DEGENERADA && i.margen != null && i.ventas != null)
        .map((i) => ({
          nombre: i.nombre,
          tir: i.tir as number,
          margen: i.margen as number,
          ventas: i.ventas as number,
          tipo: i.tipo || "VIS",
          und: i.und,
        })),
    [items],
  );
  const excluidos = items.length - pts.length;

  const buildOption = useCallback(
    (t: ChartTokens): EChartsOption => {
      const maxVentas = Math.max(1, ...pts.map((p) => p.ventas));

      // Dominios: SIEMPRE incluyen 0, tirRef y margenRef, con el mismo padding que la versión visx.
      const xs = [...pts.map((p) => p.tir), tirRef, 0];
      const xLo = Math.min(...xs);
      const xHi = Math.max(...xs);
      const xPad = (xHi - xLo) * 0.15 || 0.05;
      const ys = [...pts.map((p) => p.margen), margenRef, 0];
      const yLo = Math.min(...ys);
      const yHi = Math.max(...ys);
      const yPad = (yHi - yLo) * 0.18 || 0.02;
      const xMin = xLo - xPad;
      const xMax = xHi + xPad;
      const yMin = yLo - yPad;
      const yMax = yHi + yPad;

      const showNames = pts.length <= 8;

      const serie = (noVis: boolean): ScatterSeriesOption => {
        const c = noVis ? t.cgAmber : t.primary;
        return {
          name: noVis ? "No VIS" : "VIS",
          type: "scatter",
          data: pts
            .filter((p) => esNoVis(p.tipo) === noVis)
            .map((p) => ({ value: [p.tir, p.margen, p.ventas], name: p.nombre, tipo: p.tipo })),
          symbolSize: (val: number[]) => 2 * radio(val[2], maxVentas),
          itemStyle: { color: rgba(c, 0.22), borderColor: rgba(c, 0.85), borderWidth: 1.5 },
          label: showNames
            ? {
                show: true,
                position: "top",
                distance: 5,
                formatter: (p) => (p as { name: string }).name,
                color: t.tooltipText,
                fontSize: 10.5,
              }
            : { show: false },
          z: 3,
        };
      };

      // Rótulos de cuadrante en las 4 esquinas del dominio (puntos invisibles con label).
      const quad: ScatterSeriesOption = {
        type: "scatter",
        silent: true,
        symbolSize: 0,
        z: 1,
        data: [
          { value: [xMax, yMax], label: { align: "right", verticalAlign: "top", offset: [-2, 2] }, name: "Estrella" },
          { value: [xMin, yMax], label: { align: "left", verticalAlign: "top", offset: [2, 2] }, name: "Crecimiento" },
          { value: [xMax, yMin], label: { align: "right", verticalAlign: "bottom", offset: [-2, -2] }, name: "Vigilancia" },
          { value: [xMin, yMin], label: { align: "left", verticalAlign: "bottom", offset: [2, -2] }, name: "Revisar" },
        ],
        label: {
          show: true,
          formatter: (p) => (p as { name: string }).name.toUpperCase(),
          color: t.axisLabel,
          opacity: 0.6,
          fontSize: 10,
        },
        // Cruz de cuadrantes (líneas punteadas en tirRef / margenRef).
        markLine: {
          symbol: "none",
          silent: true,
          label: { show: false },
          lineStyle: { color: t.axisLabel, type: "dashed", width: 1, opacity: 0.5 },
          data: [{ xAxis: tirRef }, { yAxis: margenRef }],
        },
      };

      return {
        backgroundColor: "transparent",
        animationDuration: 420,
        grid: { top: 16, right: 18, bottom: 40, left: 8, containLabel: true },
        tooltip: {
          trigger: "item",
          backgroundColor: t.tooltipBg,
          borderColor: t.tooltipBorder,
          borderWidth: 1,
          textStyle: { color: t.tooltipText, fontSize: 12 },
          padding: [6, 10],
          formatter: (raw) => {
            const p = raw as unknown as { value: number[]; name: string; data: { tipo: string } };
            const [tir, margen, ventas] = p.value;
            return (
              `<div style="font-weight:600">${p.name}</div>` +
              `<div style="margin-top:2px;color:${t.axisLabel}" class="num">TIR ${fmtPct(tir)} · margen ${fmtPct(margen)}</div>` +
              `<div style="color:${t.axisLabel}" class="num">${fmtCop(ventas)} · ${p.data.tipo}</div>`
            );
          },
        },
        xAxis: {
          type: "value",
          min: xMin,
          max: xMax,
          name: "TIR apal. ref.",
          nameLocation: "middle",
          nameGap: 26,
          nameTextStyle: { color: t.axisLabel, fontSize: 10.5 },
          axisLabel: { color: t.axisLabel, fontSize: 10.5, showMinLabel: false, showMaxLabel: false, formatter: (v: number) => fmtPct(v, 0) },
          axisLine: { lineStyle: { color: t.axisLine } },
          axisTick: { show: false },
          splitLine: { lineStyle: { color: t.grid, opacity: 0.7 } },
        },
        yAxis: {
          type: "value",
          min: yMin,
          max: yMax,
          axisLabel: { color: t.axisLabel, fontSize: 10.5, showMinLabel: false, showMaxLabel: false, formatter: (v: number) => fmtPct(v, 0) },
          axisLine: { show: false },
          axisTick: { show: false },
          splitLine: { lineStyle: { color: t.grid, opacity: 0.7 } },
        },
        series: [serie(false), serie(true), quad],
      };
    },
    [pts, tirRef, margenRef],
  );

  return (
    <div>
      <EChart buildOption={buildOption} height={height} />
      <div className="mt-2 flex flex-wrap items-center gap-x-5 gap-y-1 text-xs text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <span className="size-2.5 rounded-full bg-primary" /> VIS
        </span>
        <span className="flex items-center gap-1.5">
          <span className="size-2.5 rounded-full bg-cg-amber" /> No VIS
        </span>
        <span>· tamaño = ventas · cruz en TIR {fmtPct(tirRef, 0)} / margen {fmtPct(margenRef, 0)}</span>
        {excluidos > 0 ? <span>· {excluidos} sin TIR significativa (excluidos)</span> : null}
      </div>
    </div>
  );
}
