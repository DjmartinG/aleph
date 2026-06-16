"use client";

import { useCallback, useEffect, useRef } from "react";
import type { EChartsType } from "echarts/core";
import type { EChartsOption } from "echarts";
import { ImageDown } from "lucide-react";
import { echarts } from "@/lib/echarts";
import { useIsDark } from "@/lib/use-is-dark";
import { chartTokens, type ChartTokens } from "@/lib/chart-tokens";

/**
 * Wrapper client de ECharts. Recibe `buildOption(tokens)` y se encarga del ciclo de vida: init en
 * `useEffect`, `setOption` con los tokens del modo activo, RE-PINTA al togglear el tema (vía
 * `useIsDark`), `ResizeObserver` → `resize()`, y `dispose()` al desmontar. `buildOption` debe ser
 * estable (memoizado con `useCallback`) para no re-renderizar en cada render del padre.
 *
 * Pulido común a TODAS las gráficas (Fase 2A): animación de entrada suave (cubicOut) y un botón
 * discreto para DESCARGAR la gráfica como PNG (2×, fondo sólido del tema) — aparece al pasar el mouse.
 */
export function EChart({
  buildOption,
  height = 320,
  className,
  exportName = "aleph-grafica",
}: {
  buildOption: (t: ChartTokens) => EChartsOption;
  height?: number;
  className?: string;
  /** Nombre del archivo al descargar PNG (sin extensión). */
  exportName?: string;
}) {
  const elRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<EChartsType | null>(null);
  const isDark = useIsDark();

  useEffect(() => {
    const el = elRef.current;
    if (!el) return;
    const chart = echarts.init(el, undefined, { renderer: "canvas" });
    chartRef.current = chart;
    const ro = new ResizeObserver(() => chart.resize());
    ro.observe(el);
    return () => {
      ro.disconnect();
      chart.dispose();
      chartRef.current = null;
    };
  }, []);

  useEffect(() => {
    // Defaults de animación (la gráfica puede sobreescribir animationDuration en su buildOption).
    chartRef.current?.setOption(
      { animationEasing: "cubicOut", animationDuration: 480, ...buildOption(chartTokens(isDark)) },
      true,
    );
  }, [isDark, buildOption]);

  const descargarPng = useCallback(() => {
    const chart = chartRef.current;
    if (!chart) return;
    const url = chart.getDataURL({ type: "png", pixelRatio: 2, backgroundColor: chartTokens(isDark).tooltipBg });
    const a = document.createElement("a");
    a.href = url;
    a.download = `${exportName}.png`;
    document.body.appendChild(a);
    a.click();
    a.remove();
  }, [isDark, exportName]);

  return (
    <div className="group relative">
      <button
        type="button"
        onClick={descargarPng}
        aria-label="Descargar PNG"
        title="Descargar PNG"
        className="absolute right-1 top-1 z-10 grid size-7 place-items-center rounded-[var(--radius-data)] border border-transparent text-muted-foreground opacity-0 transition-[opacity,background-color,color,border-color] [transition-timing-function:var(--ease-out)] hover:border-border hover:bg-card hover:text-foreground focus-visible:opacity-100 group-hover:opacity-100"
      >
        <ImageDown className="size-3.5" />
      </button>
      <div ref={elRef} style={{ width: "100%", height }} className={className} />
    </div>
  );
}
