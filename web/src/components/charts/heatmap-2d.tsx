"use client";

import { Fragment } from "react";

/** Variación en pasos (ya ×100): -10 → "−10%", 0 → "0", 10 → "+10%". */
function fmtStep(p: number): string {
  const r = Math.round(p);
  if (r === 0) return "0";
  return `${r > 0 ? "+" : "−"}${Math.abs(r)}%`;
}

/** Color de la celda por margen: <0 ámbar/rojo; ≥0 teal escalado por su posición en el rango. */
function cellBg(v: number, min: number, max: number): string {
  if (v < 0) return "color-mix(in oklab, var(--danger) 38%, var(--card))";
  const span = max - min || 1;
  const t = Math.max(0, Math.min(1, (v - min) / span));
  const pct = Math.round(10 + t * 60); // 10%..70% de teal sobre la tarjeta
  return `color-mix(in oklab, var(--primary) ${pct}%, var(--card))`;
}

/**
 * Heatmap 2D de margen operativo: filas = variación de COSTO directo, columnas = variación de PRECIO.
 * `matriz[i][j]` = margen % (la celda central, pasos 0/0, es la base). Sin visx (grid CSS).
 */
export function Heatmap2D({
  pasosPrecio,
  pasosCosto,
  matriz,
}: {
  pasosPrecio: number[];
  pasosCosto: number[];
  matriz: number[][];
}) {
  const flat = matriz.flat();
  const min = Math.min(...flat);
  const max = Math.max(...flat);

  return (
    <div className="overflow-x-auto">
      <div className="flex items-stretch gap-2">
        {/* Eje Y (costo) */}
        <div className="flex items-center">
          <span className="whitespace-nowrap text-[0.7rem] uppercase tracking-wide text-muted-foreground [writing-mode:vertical-rl] [transform:rotate(180deg)]">
            Variación de costo
          </span>
        </div>

        <div className="min-w-0">
          <div
            className="grid gap-0.5"
            style={{ gridTemplateColumns: `auto repeat(${pasosPrecio.length}, minmax(3rem, 1fr))` }}
          >
            {/* Encabezado de columnas (precio) */}
            <div className="flex items-end justify-end pr-2 pb-1 text-[0.65rem] text-muted-foreground">
              costo&nbsp;\&nbsp;precio
            </div>
            {pasosPrecio.map((p, j) => (
              <div key={j} className="num pb-1 text-center text-xs font-medium tabular-nums text-muted-foreground">
                {fmtStep(p)}
              </div>
            ))}

            {/* Filas (costo) */}
            {pasosCosto.map((c, i) => (
              <Fragment key={i}>
                <div className="num flex items-center justify-end pr-2 text-xs font-medium tabular-nums text-muted-foreground">
                  {fmtStep(c)}
                </div>
                {matriz[i].map((v, j) => {
                  const base = Math.round(pasosPrecio[j]) === 0 && Math.round(c) === 0;
                  return (
                    <div
                      key={j}
                      className={`num flex h-10 items-center justify-center rounded-[2px] text-xs font-medium tabular-nums text-foreground ${
                        base ? "ring-2 ring-foreground/40" : ""
                      }`}
                      style={{ background: cellBg(v, min, max) }}
                      title={`Precio ${fmtStep(pasosPrecio[j])} · Costo ${fmtStep(c)} → margen ${v.toFixed(1)}%`}
                    >
                      {v.toFixed(1)}
                    </div>
                  );
                })}
              </Fragment>
            ))}
          </div>
          <div className="mt-1.5 text-center text-[0.7rem] uppercase tracking-wide text-muted-foreground">
            Variación de precio
          </div>
        </div>
      </div>
    </div>
  );
}
