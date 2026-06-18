"use client";

import { useIsDark } from "@/lib/use-is-dark";
import { chartTokens } from "@/lib/chart-tokens";
import { cn } from "@/lib/utils";
import type { Concentracion, ConcentracionDim } from "@/lib/api";

/**
 * Concentración / diversificación del portafolio por dimensión (proyecto, ubicación, tipo, fase). Por
 * dimensión: una barra de proporción (share por categoría) + el número EFECTIVO de categorías (1/HHI).
 * Pocas categorías efectivas o un líder dominante = cartera concentrada (riesgo). Colores de la paleta
 * de charts (theme-aware vía useIsDark); barras en CSS (densas, nítidas).
 */
export function ConcentracionPanel({ data }: { data: Concentracion }) {
  const isDark = useIsDark();
  const colors = chartTokens(isDark).palette;
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {data.dimensiones.map((d) => (
        <DimCard key={d.clave} dim={d} colors={colors} />
      ))}
    </div>
  );
}

function pct(x: number): string {
  return `${(x * 100).toFixed(1)}%`;
}

function DimCard({ dim, colors }: { dim: ConcentracionDim; colors: string[] }) {
  const lider = dim.categorias[0];
  // "Concentrado" si el líder pesa > 50% o si hay ≤ 2 categorías efectivas; un cue ámbar (de marca,
  // dirección/atención — no estado semántico rojo).
  const concentrado = (lider && lider.share > 0.5) || (dim.n_efectivo != null && dim.n_efectivo < 2);
  return (
    <div className="rounded-[var(--radius-data)] border bg-card p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <span className="text-sm font-medium">{dim.nombre}</span>
        <span className="num text-xs tabular-nums text-muted-foreground">
          <span className={cn("font-semibold", concentrado ? "text-[var(--cg-amber)]" : "text-foreground")}>
            {dim.n_efectivo != null ? dim.n_efectivo.toFixed(1) : "—"}
          </span>{" "}
          efectivas de {dim.n_categorias}
        </span>
      </div>

      <div className="flex h-2.5 overflow-hidden rounded-full" role="img" aria-label={`Reparto por ${dim.nombre}`}>
        {dim.categorias.map((cat, i) => (
          <div
            key={cat.categoria}
            style={{ width: pct(cat.share), backgroundColor: colors[i % colors.length] }}
            title={`${cat.categoria} ${pct(cat.share)}`}
          />
        ))}
      </div>

      <ul className="mt-3 space-y-1.5">
        {dim.categorias.map((cat, i) => (
          <li key={cat.categoria} className="flex items-center gap-2 text-xs">
            <span
              className="size-2.5 shrink-0 rounded-[2px]"
              style={{ backgroundColor: colors[i % colors.length] }}
              aria-hidden
            />
            <span className="min-w-0 flex-1 truncate text-muted-foreground">{cat.categoria}</span>
            <span className={cn("num tabular-nums", i === 0 ? "font-semibold" : "")}>{pct(cat.share)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
