"use client";

import { useCallback } from "react";
import type { EChartsOption } from "echarts";
import type { CustomSeriesRenderItemAPI, CustomSeriesRenderItemParams } from "echarts";
import { EChart } from "@/components/charts/echart";
import type { ChartTokens } from "@/lib/chart-tokens";
import type { Pyg } from "@/lib/api";
import { fmtCop } from "@/lib/format";

/** Eje Y en "mil M" sin sufijo (lo dice el subtítulo): valores en miles COP → /1e6. */
function tickY(v: number): string {
  if (v === 0) return "0";
  return `${(v / 1_000_000).toLocaleString("en-US", { maximumFractionDigits: 0 }).replace(/,/g, ".")}`;
}

interface Bar {
  name: string;
  top: number;
  base: number;
  amount: number;
  color: string;
  total: boolean;
}

/**
 * Cascada (waterfall) del P&G (ECharts custom series): cómo cada peso de venta se erosiona (lote →
 * obra → indirectos → honorarios → impuestos) hasta la utilidad neta. RECONCILIA por construcción con
 * `util_oper` del motor (mismos términos de la fórmula de modelo.pyg); el impuesto = `renta` (0 en VIS,
 * exento) y util. neta = util_oper − renta. → es exhibición, no recálculo. Todo sale de `Results.pyg`.
 */
export function PygWaterfall({ pyg, height = 300 }: { pyg: Pyg; height?: number }) {
  const buildOption = useCallback(
    (t: ChartTokens): EChartsOption => {
      const ti = pyg.total_ingresos;
      const lote = pyg.costo_lote;
      const dir = pyg.directos;
      const indir = pyg.indirectos_otros + pyg.gastos_fijos; // términos REALES de la fórmula del motor
      const hon = pyg.honorarios;
      const uo = pyg.util_oper;
      const renta = pyg.renta ?? 0; // impuesto de RENTA del P&G — 0 en VIS (exento). NO usar `udi`
      const un = uo - renta;        // utilidad neta = util_oper − renta (después de impuestos)

      // Guard de fidelidad: la cadena de restas DEBE cerrar en util_oper (si no, falta una línea).
      const reUO = ti - lote - dir - indir - hon;
      if (Math.abs(reUO - uo) > 1) {
        console.warn("PygWaterfall: la cascada no reconcilia con util_oper", { reconstruido: reUO, motor: uo });
      }

      const t2 = ti - lote;
      const t3 = t2 - dir;
      const t4 = t3 - indir;
      // t5 = t4 - hon === uo

      const bars: Bar[] = [
        { name: "Ingresos", top: ti, base: 0, amount: ti, color: t.primary, total: true },
        { name: "Lote", top: ti, base: t2, amount: lote, color: t.cgAmber, total: false },
        { name: "C. directo", top: t2, base: t3, amount: dir, color: t.cgAmber, total: false },
        { name: "Indirectos", top: t3, base: t4, amount: indir, color: t.cgAmber, total: false },
        { name: "Honorarios", top: t4, base: uo, amount: hon, color: t.cgAmber, total: false },
        { name: "Util. oper.", top: uo, base: 0, amount: uo, color: t.primary, total: true },
        { name: "Impuestos", top: uo, base: un, amount: renta, color: t.cgAmber, total: false },
        { name: "Util. neta", top: un, base: 0, amount: un, color: un >= 0 ? t.exito : t.peligro, total: true },
      ];

      const renderItem = (params: CustomSeriesRenderItemParams, api: CustomSeriesRenderItemAPI) => {
        const ci = api.value(0) as number;
        const top = api.value(1) as number;
        const base = api.value(2) as number;
        const b = bars[params.dataIndex];
        const pTop = api.coord([ci, top]);
        const pBase = api.coord([ci, base]);
        const bw = (api.size?.([1, 0]) as number[])[0] * 0.55;
        const y = Math.min(pTop[1], pBase[1]);
        const hgt = Math.max(1, Math.abs(pBase[1] - pTop[1]));
        const fw: "bold" | "normal" = b.total ? "bold" : "normal";
        return {
          type: "group" as const,
          children: [
            {
              type: "rect" as const,
              shape: { x: pTop[0] - bw / 2, y, width: bw, height: hgt, r: 2 },
              style: { fill: b.color, opacity: b.total ? 0.92 : 0.82 },
            },
            {
              type: "text" as const,
              style: {
                x: pTop[0],
                y: y - 5,
                text: `${b.total || Math.abs(b.amount) < 1 ? "" : "−"}${fmtCop(b.amount)}`,
                textAlign: "center",
                textVerticalAlign: "bottom",
                fontSize: 10,
                fontWeight: fw,
                fill: b.total ? t.tooltipText : t.axisLabel,
              },
            },
          ],
        };
      };

      return {
        backgroundColor: "transparent",
        animationDuration: 480,
        grid: { left: 8, right: 12, top: 24, bottom: 24, containLabel: true },
        tooltip: {
          trigger: "item",
          backgroundColor: t.tooltipBg,
          borderColor: t.tooltipBorder,
          borderWidth: 1,
          textStyle: { color: t.tooltipText, fontSize: 12 },
          padding: [6, 10],
          formatter: (raw) => {
            const b = bars[(raw as { dataIndex: number }).dataIndex];
            const head = b.total ? b.name : `${b.name} (resta)`;
            const extra = b.name === "Util. oper." && pyg.margen_oper != null ? ` · margen ${(pyg.margen_oper * 100).toFixed(1)}%` : "";
            return `<div style="font-weight:600">${head}</div><div class="num" style="margin-top:2px">${fmtCop(b.amount)}${extra}</div>`;
          },
        },
        xAxis: {
          type: "category",
          data: bars.map((b) => b.name),
          axisLabel: { color: t.axisLabel, fontSize: 10.5, interval: 0 },
          axisLine: { lineStyle: { color: t.axisLine } },
          axisTick: { show: false },
        },
        yAxis: {
          type: "value",
          axisLabel: { color: t.axisLabel, fontSize: 10.5, formatter: (v: number) => tickY(v) },
          axisLine: { show: false },
          axisTick: { show: false },
          splitLine: { lineStyle: { color: t.grid, opacity: 0.7 } },
        },
        series: [
          {
            type: "custom",
            renderItem,
            encode: { x: 0, y: [1, 2] },
            data: bars.map((b, i) => ({ value: [i, b.top, b.base] })),
            markLine: {
              symbol: "none",
              silent: true,
              label: { show: false },
              lineStyle: { color: t.axisLine, width: 1, opacity: 0.8 },
              data: [{ yAxis: 0 }],
            },
          },
        ],
      };
    },
    [pyg],
  );

  return <EChart buildOption={buildOption} height={height} exportName="aleph-pyg-cascada" />;
}
