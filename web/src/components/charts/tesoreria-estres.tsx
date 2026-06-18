"use client";

import { useCallback, useState } from "react";
import type { EChartsOption } from "echarts";
import type { LineSeriesOption } from "echarts/charts";
import { EChart } from "@/components/charts/echart";
import type { ChartTokens } from "@/lib/chart-tokens";
import { mesesHastaHoy } from "@/lib/timeline";
import { timeDataZoom } from "@/lib/echarts-timeline";
import { fmtCop } from "@/lib/format";
import { cn } from "@/lib/utils";
import { MiniStat } from "@/components/mini-stat";
import type { Estres } from "@/lib/api";

function tickY(v: number): string {
  if (v === 0) return "0";
  return `${(v / 1_000_000).toLocaleString("en-US", { maximumFractionDigits: 0 }).replace(/,/g, ".")}`;
}

function pctShock(x: number): string {
  return `${x > 0 ? "+" : ""}${Math.round(x * 100)}%`;
}

type AxisParam = { seriesName?: string; value: number[] };
type MarkLineData = NonNullable<NonNullable<LineSeriesOption["markLine"]>["data"]>;

/**
 * Estrés de la tesorería consolidada: superpone la caja BAJO ESTRÉS (línea roja punteada) sobre la caja
 * BASE (área teal). El toggle elige el escenario; las cifras salen tal cual del motor (recalculado con
 * el shock). La historia: el valle se profundiza y, al borde derecho, bajo estrés la caja SIGUE negativa.
 */
export function TesoreriaEstres({ data }: { data: Estres }) {
  const [sel, setSel] = useState<number | null>(null); // null = solo base; 0..n = escenario
  const esc = sel == null ? null : data.escenarios[sel];
  const n = data.base.caja.length;
  const hoy = mesesHastaHoy(data.base_date);
  const hoyEnRango = hoy != null && hoy >= 0 && hoy <= Math.max(1, n - 1);
  const cajaFin = esc ? esc.caja[esc.caja.length - 1] : 0;

  const buildOption = useCallback(
    (t: ChartTokens): EChartsOption => {
      const cajaBase = data.base.caja.map((v, m) => [m, v]);
      const cajaEstr = esc ? esc.caja.map((v, m) => [m, v]) : null;

      const markLineData: MarkLineData = [
        { yAxis: 0, label: { show: false }, lineStyle: { color: t.axisLabel, type: "dashed", width: 1, opacity: 0.5 } },
      ];
      if (hoyEnRango) {
        markLineData.push({
          xAxis: hoy,
          label: {
            show: true, formatter: "Hoy", position: "end", color: t.tooltipText,
            backgroundColor: t.axisLabel, padding: [2, 5], borderRadius: 3, fontSize: 9.5, fontWeight: 600,
          },
          lineStyle: { color: t.axisLabel, type: "dashed", width: 1.25, opacity: 0.7 },
        });
      }

      const valle = esc ? esc.exposicion_maxima : data.base.exposicion_maxima;
      const valleColor = esc ? t.peligro : t.peligro;

      const series: LineSeriesOption[] = [
        {
          name: "Caja base",
          type: "line",
          smooth: true,
          showSymbol: false,
          data: cajaBase,
          z: 3,
          lineStyle: { color: t.primary, width: esc ? 1.5 : 2.25, opacity: esc ? 0.55 : 1 },
          areaStyle: { color: t.primary, opacity: esc ? t.areaOpacity * 0.4 : t.areaOpacity },
          markLine: { symbol: "none", silent: true, data: markLineData },
          markPoint: esc
            ? undefined
            : {
                symbol: "circle",
                symbolSize: 9,
                data: [
                  {
                    name: "Exposición máxima",
                    coord: [valle.mes, valle.valor],
                    itemStyle: { color: valleColor, borderColor: t.tooltipBg, borderWidth: 2 },
                    label: {
                      show: true, formatter: `Exp. máx ${fmtCop(valle.valor)}`, position: "bottom",
                      color: valleColor, fontSize: 10, fontWeight: 600,
                    },
                  },
                ],
              },
        },
      ];
      if (cajaEstr && esc) {
        series.push({
          name: "Caja bajo estrés",
          type: "line",
          smooth: true,
          showSymbol: false,
          data: cajaEstr,
          z: 4,
          lineStyle: { color: t.peligro, width: 2.25, type: "dashed" },
          markPoint: {
            symbol: "circle",
            symbolSize: 9,
            data: [
              {
                name: "Exposición bajo estrés",
                coord: [esc.exposicion_maxima.mes, esc.exposicion_maxima.valor],
                itemStyle: { color: t.peligro, borderColor: t.tooltipBg, borderWidth: 2 },
                label: {
                  show: true, formatter: `Exp. máx ${fmtCop(esc.exposicion_maxima.valor)}`, position: "bottom",
                  color: t.peligro, fontSize: 10, fontWeight: 600,
                },
              },
            ],
          },
        });
      }

      return {
        backgroundColor: "transparent",
        animationDuration: 420,
        grid: { top: 22, right: 16, bottom: 48, left: 8, containLabel: true },
        dataZoom: [timeDataZoom(t)],
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
            const cb = arr.find((p) => p.seriesName === "Caja base")?.value?.[1];
            const ce = arr.find((p) => p.seriesName === "Caja bajo estrés")?.value?.[1];
            const head = `Año ${Math.floor(m / 12) + 1}, mes ${(m % 12) + 1}`;
            let html = `<div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:.04em;color:${t.axisLabel}">${head}</div>`;
            if (cb != null) html += `<div style="margin-top:2px;font-weight:600">Base ${fmtCop(cb)}</div>`;
            if (ce != null) html += `<div style="color:${t.peligro};font-weight:600">Estrés ${fmtCop(ce)}</div>`;
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
        series,
      };
    },
    [data, esc, n, hoy, hoyEnRango],
  );

  return (
    <div className="rounded-[var(--radius-data)] border bg-card p-4">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <Toggle active={sel == null} tone="base" onClick={() => setSel(null)}>
          Caso base
        </Toggle>
        {data.escenarios.map((e, i) => (
          <Toggle key={e.nombre} active={sel === i} tone="stress" onClick={() => setSel(i)}>
            {e.nombre}
          </Toggle>
        ))}
      </div>

      {esc ? (
        <div className="mb-3 grid grid-cols-2 gap-x-6 gap-y-2 sm:grid-cols-4">
          <MiniStat
            label="Shock aplicado"
            value={pctShock(esc.shock.precio)}
            note={`ventas · costos ${pctShock(esc.shock.costo)} · ritmo ${pctShock(esc.shock.ritmo)}`}
          />
          <MiniStat
            label="Necesidad máx. de caja"
            value={fmtCop(Math.abs(esc.exposicion_maxima.valor))}
            note="bajo estrés"
          />
          <MiniStat
            label="Más profundo que base"
            value={fmtCop(Math.abs(esc.delta_exposicion))}
            note="caja propia extra en el peor mes"
          />
          <MiniStat
            label="Caja al cierre"
            value={fmtCop(cajaFin)}
            note={cajaFin < 0 ? "aún en déficit" : "recuperada"}
          />
        </div>
      ) : null}

      <EChart buildOption={buildOption} height={328} exportName="aleph-estres-tesoreria" />

      <p className="mt-2 text-xs text-muted-foreground">
        Caja consolidada si las ventas caen/se atrasan y suben los costos en toda la cartera (recalculado
        con el shock). Bajo estrés el valle se <strong className="text-foreground">profundiza</strong> y,
        al borde derecho, la caja puede seguir <strong className="text-foreground">en déficit</strong>{" "}
        cuando el caso base ya recuperó.
      </p>
    </div>
  );
}

function Toggle({
  active,
  tone,
  onClick,
  children,
}: {
  active: boolean;
  tone: "base" | "stress";
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-full border px-3 py-1 text-xs font-medium transition-colors [transition-timing-function:var(--ease-out)]",
        active && tone === "base" && "border-primary/30 bg-primary/10 text-primary",
        active && tone === "stress" && "border-danger/30 bg-danger/10 text-danger",
        !active && "border-rule text-muted-foreground hover:bg-accent/40",
      )}
      aria-pressed={active}
    >
      {children}
    </button>
  );
}
