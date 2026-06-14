"use client";

import { useMemo, useState, useTransition } from "react";
import { Play, Loader2 } from "lucide-react";
import type { MonteCarloCBResult } from "@/lib/api";
import { runMonteCarloCB } from "@/lib/actions";
import { fmtCop, fmtPct } from "@/lib/format";
import { DistributionHistogram, type HistMarker } from "@/components/charts/distribution-histogram";
import { cn } from "@/lib/utils";

const FORECASTS: { key: string; label: string }[] = [
  { key: "tir_proyecto", label: "TIR proyecto" },
  { key: "tir_equity", label: "TIR socio" },
  { key: "vpn_proyecto", label: "VPN" },
  { key: "margen", label: "Margen" },
  { key: "exposicion_maxima", label: "Exposición máx." },
  { key: "breakeven_mes", label: "Breakeven" },
];
const N_OPTS = [500, 1000, 3000];
const mesFmt = (v: number) => `${v.toFixed(0)} m`;
const FMT: Record<string, (v: number) => string> = {
  tir_proyecto: (v) => fmtPct(v),
  tir_equity: (v) => fmtPct(v),
  margen: (v) => fmtPct(v),
  vpn_proyecto: (v) => fmtCop(v),
  exposicion_maxima: (v) => fmtCop(v),
  breakeven_mes: mesFmt,
};
const VAR_LABEL: Record<string, string> = {
  precio: "Precio de venta",
  costo: "Costo directo",
  ritmo: "Ritmo de ventas",
};

export function MonteCarlo({ slug }: { slug: string }) {
  const [fc, setFc] = useState<string>("tir_proyecto");
  const [n, setN] = useState(1000);
  const [res, setRes] = useState<MonteCarloCBResult | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [pending, start] = useTransition();

  function run() {
    setErr(null);
    start(async () => {
      try {
        setRes(await runMonteCarloCB(slug, { n, seed: 42, incluir_valores: true }));
      } catch (e) {
        setErr(e instanceof Error ? e.message : "Error al correr la simulación");
      }
    });
  }

  const view = useMemo(() => {
    if (!res) return null;
    const f = res.forecasts[fc];
    if (!f) return null;
    const fmt = FMT[fc] ?? ((v: number) => String(v));
    return { f, fmt };
  }, [res, fc]);

  const markers: HistMarker[] = view
    ? [
        { label: "P10", value: view.f.stats.p10, color: "var(--muted-foreground)", dash: true },
        { label: "P50", value: view.f.stats.p50, color: "var(--foreground)" },
        { label: "P90", value: view.f.stats.p90, color: "var(--muted-foreground)", dash: true },
        ...(view.f.certeza
          ? [{ label: "meta", value: view.f.certeza.umbral, color: "var(--danger)" }]
          : []),
      ]
    : [];

  const tornado = view
    ? Object.entries(view.f.tornado).sort((a, b) => b[1].contribucion_pct - a[1].contribucion_pct)
    : [];

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="inline-flex flex-wrap rounded-[var(--radius-data)] border bg-card p-0.5 text-sm">
          {FORECASTS.map((m) => (
            <button
              key={m.key}
              type="button"
              onClick={() => setFc(m.key)}
              className={cn(
                "rounded-[3px] px-3 py-1 font-medium transition-colors [transition-timing-function:var(--ease-out)]",
                fc === m.key ? "bg-accent text-accent-foreground" : "text-muted-foreground hover:text-foreground",
              )}
            >
              {m.label}
            </button>
          ))}
        </div>

        <label className="flex items-center gap-2 text-sm text-muted-foreground">
          Corridas
          <select
            value={n}
            onChange={(e) => setN(Number(e.target.value))}
            className="num rounded-[3px] border bg-card px-2 py-1 text-sm text-foreground"
          >
            {N_OPTS.map((o) => (
              <option key={o} value={o}>
                {o.toLocaleString("es-CO")}
              </option>
            ))}
          </select>
        </label>

        <button
          type="button"
          onClick={run}
          disabled={pending}
          className="ml-auto inline-flex items-center gap-1.5 rounded-[var(--radius-data)] bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground transition-[opacity,transform] [transition-timing-function:var(--ease-out)] hover:opacity-90 active:scale-[0.98] disabled:opacity-60"
        >
          {pending ? <Loader2 className="size-4 animate-spin" /> : <Play className="size-4" />}
          {res ? "Re-correr" : "Correr simulación"}
        </button>
      </div>

      {err ? <p className="text-sm text-danger">{err}</p> : null}

      {!res && !pending && !err ? (
        <div className="rounded-[var(--radius-data)] border border-dashed bg-card p-10 text-center text-sm text-muted-foreground">
          Elige el indicador y el número de corridas, y dale <strong>Correr simulación</strong>.
        </div>
      ) : null}

      {view ? (
        <>
          <div className="grid grid-cols-2 gap-x-6 gap-y-3 rounded-[var(--radius-data)] border bg-card p-4 sm:grid-cols-4">
            <Stat label="P10" value={view.fmt(view.f.stats.p10)} note="pesimista" />
            <Stat label="Mediana" value={view.fmt(view.f.stats.p50)} note="P50" strong />
            <Stat label="P90" value={view.fmt(view.f.stats.p90)} note="optimista" />
            {view.f.certeza ? (
              <Stat
                label="Certeza"
                value={fmtPct(view.f.certeza.prob, 0)}
                note={`prob. ${view.f.certeza.signo} ${view.fmt(view.f.certeza.umbral)}`}
                good={view.f.certeza.prob >= 0.5}
              />
            ) : (
              <Stat label="Desv. est." value={view.fmt(view.f.stats.std)} note="dispersión" />
            )}
          </div>

          {view.f.valores && view.f.valores.length > 0 ? (
            <div className="mt-4 rounded-[var(--radius-data)] border bg-card p-4">
              <DistributionHistogram
                values={view.f.valores}
                markers={markers}
                hurdle={view.f.certeza ? view.f.certeza.umbral : undefined}
                format={view.fmt}
              />
            </div>
          ) : (
            <p className="mt-4 text-sm text-muted-foreground">
              Sin distribución para {view.f.nombre} (indicador degenerado en este proyecto).
            </p>
          )}

          {tornado.length > 0 ? (
            <div className="mt-4 rounded-[var(--radius-data)] border bg-card p-4">
              <div className="mb-3 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Tornado · contribución a la varianza
              </div>
              <div className="space-y-2">
                {tornado.map(([k, v]) => (
                  <div key={k} className="flex items-center gap-3 text-sm">
                    <span className="w-32 shrink-0 text-muted-foreground">{VAR_LABEL[k] ?? k}</span>
                    <div className="h-3 flex-1 overflow-hidden rounded bg-muted">
                      <div
                        className="h-3 rounded"
                        style={{
                          width: `${Math.min(100, v.contribucion_pct)}%`,
                          background: v.rho >= 0 ? "var(--primary)" : "var(--cg-amber)",
                        }}
                      />
                    </div>
                    <span className="num w-12 shrink-0 text-right tabular-nums">
                      {v.contribucion_pct.toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
              <p className="mt-2 text-[0.7rem] text-muted-foreground/80">
                Qué variable explica más la incertidumbre del indicador (correlación de rango al
                cuadrado, normalizada). Teal = efecto al alza; ámbar = a la baja.
              </p>
            </div>
          ) : null}

          <p className="mt-3 text-xs text-muted-foreground">
            Monte Carlo Crystal Ball · {res?.n?.toLocaleString("es-CO")} corridas · distribuciones por
            variable (precio triangular, costo PERT, ritmo triangular), deterministas por semilla. La
            TIR usa el modelo (no el override de fiducia), por eso difiere de la cifra del tablero;
            sirve para el análisis de riesgo relativo.
          </p>
        </>
      ) : null}
    </div>
  );
}

function Stat({
  label,
  value,
  note,
  strong,
  good,
}: {
  label: string;
  value: string;
  note?: string;
  strong?: boolean;
  good?: boolean;
}) {
  return (
    <div>
      <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</div>
      <div
        className={cn(
          "num mt-0.5 font-semibold",
          strong ? "text-lg" : "text-base",
          good === true ? "text-success" : good === false ? "text-danger" : "",
        )}
      >
        {value}
      </div>
      {note ? <div className="text-[0.7rem] text-muted-foreground/80">{note}</div> : null}
    </div>
  );
}
