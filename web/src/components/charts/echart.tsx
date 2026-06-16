"use client";

import { useEffect, useRef } from "react";
import type { EChartsType } from "echarts/core";
import type { EChartsOption } from "echarts";
import { echarts } from "@/lib/echarts";
import { useIsDark } from "@/lib/use-is-dark";
import { chartTokens, type ChartTokens } from "@/lib/chart-tokens";

/**
 * Wrapper client de ECharts. Recibe `buildOption(tokens)` y se encarga del ciclo de vida: init en
 * `useEffect`, `setOption` con los tokens del modo activo, RE-PINTA al togglear el tema (vía
 * `useIsDark`), `ResizeObserver` → `resize()`, y `dispose()` al desmontar. `buildOption` debe ser
 * estable (memoizado con `useCallback`) para no re-renderizar en cada render del padre.
 */
export function EChart({
  buildOption,
  height = 320,
  className,
}: {
  buildOption: (t: ChartTokens) => EChartsOption;
  height?: number;
  className?: string;
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
    chartRef.current?.setOption(buildOption(chartTokens(isDark)), true);
  }, [isDark, buildOption]);

  return <div ref={elRef} style={{ width: "100%", height }} className={className} />;
}
