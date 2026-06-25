"use client";

import { useMemo, useState, useTransition } from "react";
import { Play, Loader2, RotateCcw } from "lucide-react";
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
// Tope 500: el MC re-corre el motor por cada corrida y el API vive en un App Service B1 (1 core, CPU
// muy limitada → ~8-10x más lento que una máquina normal). Medido en prod: incluso 1.000 corridas
// pasan de 60s (timeout serverless de Vercel → 504). 500 entran (~20-30s) y ya dan percentiles
// suficientes para una sensibilidad. Para 2.000+ corridas hace falta un tier de App Service más rápido
// (P0v3/P1v2, CPU dedicada) o un MC asíncrono. (El motor ya corre en modo `lite`, ~1.35x.)
const N_OPTS = [200, 300, 500];
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
type Modo = "frecuencia" | "acumulada";

export function MonteCarlo({ slug }: { slug: string }) {
  const [fc, setFc] = useState<string>("tir_proyecto");
  const [n, setN] = useState(300);
  const [res, setRes] = useState<MonteCarloCBResult | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [pending, start] = useTransition();
  const [modo, setModo] = useState<Modo>("frecuencia");
  const [umbral, setUmbral] = useState<number | null>(null); // umbral de certeza interactivo

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

  // Meta del motor + dirección; reinicia el umbral interactivo al cambiar de indicador (patrón oficial
  // de "ajustar estado en render", no en un efecto: evita el render en cascada).
  const baseUmbral = view?.f.certeza?.umbral ?? null;
  const signoMayor = view?.f.certeza ? view.f.certeza.signo.includes(">") : true;
  const resetKey = `${fc}:${baseUmbral}`;
  const [prevKey, setPrevKey] = useState(resetKey);
  if (prevKey !== resetKey) {
    setPrevKey(resetKey);
    setUmbral(baseUmbral);
  }

  // Certeza EN VIVO: cuenta corridas que cumplen el umbral interactivo (descriptivo, no recálculo).
  const certezaLive = useMemo(() => {
    const vals = view?.f.valores;
    if (umbral == null || !vals || vals.length === 0) return null;
    const k = vals.filter((v) => (signoMayor ? v >= umbral : v <= umbral)).length;
    return k / vals.length;
  }, [umbral, signoMayor, view]);

  const markers: HistMarker[] = view
    ? [
        { label: "P10", value: view.f.stats.p10, tone: "muted", dash: true },
        { label: "P50", value: view.f.stats.p50, tone: "strong" },
        { label: "media", value: view.f.stats.media, tone: "mean", dash: true },
        { label: "P90", value: view.f.stats.p90, tone: "muted", dash: true },
      ]
    : [];

  const tornado = view
    ? Object.entries(view.f.tornado).sort((a, b) => b[1].contribucion_pct - a[1].contribucion_pct)
    : [];

  const desviado = umbral != null && baseUmbral != null && umbral !== baseUmbral;

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
          {/* KPIs en cards — media y desviación siempre visibles */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            <Stat label="P10" value={view.fmt(view.f.stats.p10)} note="pesimista" />
            <Stat label="Mediana" value={view.fmt(view.f.stats.p50)} note="P50" strong accent />
            <Stat label="P90" value={view.fmt(view.f.stats.p90)} note="optimista" />
            <Stat label="Media" value={view.fmt(view.f.stats.media)} note="promedio" />
            <Stat label="Desv. est." value={view.fmt(view.f.stats.std)} note="dispersión" />
            {view.f.certeza ? (
              <Stat
                label="Certeza"
                value={fmtPct(certezaLive ?? view.f.certeza.prob, 0)}
                note={`prob. ${view.f.certeza.signo} ${view.fmt(umbral ?? view.f.certeza.umbral)}`}
                good={(certezaLive ?? view.f.certeza.prob) >= 0.5}
                accent
              />
            ) : (
              <Stat label="Rango" value={`${view.fmt(view.f.stats.min)} – ${view.fmt(view.f.stats.max)}`} note="mín – máx" />
            )}
          </div>

          {view.f.valores && view.f.valores.length > 0 ? (
            <div className="mt-4 rounded-[var(--radius-data)] border bg-card p-4">
              <div className="mb-2 flex items-center justify-between">
                <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Distribución de {view.f.nombre}
                </div>
                <div className="inline-flex rounded-[var(--radius-data)] border bg-card p-0.5 text-xs">
                  {(["frecuencia", "acumulada"] as const).map((mo) => (
                    <button
                      key={mo}
                      type="button"
                      onClick={() => setModo(mo)}
                      className={cn(
                        "rounded-[3px] px-2.5 py-1 font-medium capitalize transition-colors [transition-timing-function:var(--ease-out)]",
                        modo === mo ? "bg-accent text-accent-foreground" : "text-muted-foreground hover:text-foreground",
                      )}
                    >
                      {mo}
                    </button>
                  ))}
                </div>
              </div>

              <DistributionHistogram
                values={view.f.valores}
                markers={markers}
                umbral={umbral ?? undefined}
                signoMayor={signoMayor}
                showCumulative={modo === "acumulada"}
                format={view.fmt}
              />

              {/* Certeza interactiva: mover el umbral y ver el % en vivo (descriptivo, no recálculo) */}
              {view.f.certeza && umbral != null ? (
                <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-rule pt-3 text-sm">
                  <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Certeza
                  </span>
                  <input
                    type="range"
                    min={view.f.stats.min}
                    max={view.f.stats.max}
                    step={Math.max((view.f.stats.max - view.f.stats.min) / 200, 1e-9)}
                    value={umbral}
                    onChange={(e) => setUmbral(Number(e.target.value))}
                    className="h-1 min-w-[140px] flex-1 cursor-pointer accent-[var(--primary)]"
                    aria-label="Umbral de certeza"
                  />
                  <span className="num tabular-nums">
                    <span className="text-base font-semibold">{fmtPct(certezaLive ?? 0, 0)}</span>
                    <span className="text-muted-foreground">
                      {" "}
                      prob. {view.f.certeza.signo} {view.fmt(umbral)}
                    </span>
                  </span>
                  {desviado ? (
                    <button
                      type="button"
                      onClick={() => setUmbral(baseUmbral)}
                      className="inline-flex items-center gap-1 rounded-[3px] border px-2 py-0.5 text-xs text-muted-foreground transition-colors hover:text-foreground"
                    >
                      <RotateCcw className="size-3" aria-hidden /> base {fmtPct(view.f.certeza.prob, 0)}
                    </button>
                  ) : null}
                </div>
              ) : null}
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
              <p className="mt-2 text-[0.7rem] text-muted-foreground">
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
  accent,
}: {
  label: string;
  value: string;
  note?: string;
  strong?: boolean;
  good?: boolean;
  accent?: boolean;
}) {
  return (
    <div
      className={cn(
        "rounded-[var(--radius-data)] border bg-card px-3 py-2.5",
        accent && "border-l-2 border-l-primary/40",
      )}
    >
      <div className="text-[0.7rem] font-medium uppercase tracking-wide text-muted-foreground">{label}</div>
      <div
        className={cn(
          "num mt-0.5 font-semibold tabular-nums",
          strong ? "text-lg" : "text-base",
          good === true ? "text-success" : good === false ? "text-danger" : "",
        )}
      >
        {value}
      </div>
      {note ? <div className="text-[0.7rem] text-muted-foreground">{note}</div> : null}
    </div>
  );
}
