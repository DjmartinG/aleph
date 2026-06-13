"use client";

import { useMemo, useState, useTransition } from "react";
import { Play, Loader2 } from "lucide-react";
import type { MonteCarloResult } from "@/lib/api";
import { runMonteCarlo } from "@/lib/actions";
import { fmtCop, fmtPct } from "@/lib/format";
import { DistributionHistogram, type HistMarker } from "@/components/charts/distribution-histogram";
import { cn } from "@/lib/utils";

type Metric = "tir" | "tir_socio" | "vpn";
const METRICS: { key: Metric; label: string }[] = [
  { key: "tir", label: "TIR proyecto" },
  { key: "tir_socio", label: "TIR socio" },
  { key: "vpn", label: "VPN" },
];
const N_OPTS = [500, 1000, 3000];

export function MonteCarlo({ slug }: { slug: string }) {
  const [metric, setMetric] = useState<Metric>("tir");
  const [n, setN] = useState(1000);
  const [res, setRes] = useState<MonteCarloResult | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [pending, start] = useTransition();

  function run() {
    setErr(null);
    start(async () => {
      try {
        setRes(await runMonteCarlo(slug, { tipo: "tir", n }));
      } catch (e) {
        setErr(e instanceof Error ? e.message : "Error al correr la simulación");
      }
    });
  }

  const view = useMemo(() => {
    if (!res) return null;
    if (metric === "tir")
      return { values: res.tir_proyecto, stats: res.stats_tir, format: fmtPct, hurdle: res.hurdle, probLabel: "TIR > TIO", prob: res.prob_tir_hurdle };
    if (metric === "tir_socio") {
      const arr = res.tir_equity;
      const prob = arr.length ? arr.filter((v) => v > res.hurdle).length / arr.length : 0;
      return { values: arr, stats: res.stats_equity, format: fmtPct, hurdle: res.hurdle, probLabel: "TIR socio > TIO", prob };
    }
    return { values: res.vpn_proyecto, stats: res.stats_vpn, format: fmtCop, hurdle: 0, probLabel: "VPN > 0", prob: res.prob_vpn_pos };
  }, [res, metric]);

  const markers: HistMarker[] = view
    ? [
        { label: "P10", value: view.stats.p10, color: "var(--muted-foreground)", dash: true },
        { label: "P50", value: view.stats.p50, color: "var(--foreground)" },
        { label: "P90", value: view.stats.p90, color: "var(--muted-foreground)", dash: true },
        { label: metric === "vpn" ? "0" : "TIO", value: view.hurdle, color: "var(--danger)" },
      ]
    : [];

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="inline-flex rounded-[var(--radius-data)] border bg-card p-0.5 text-sm">
          {METRICS.map((m) => (
            <button
              key={m.key}
              type="button"
              onClick={() => setMetric(m.key)}
              className={cn(
                "rounded-[3px] px-3 py-1 font-medium transition-colors [transition-timing-function:var(--ease-out)]",
                metric === m.key ? "bg-accent text-accent-foreground" : "text-muted-foreground hover:text-foreground",
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
            <Stat label="P10" value={view.format(view.stats.p10)} note="pesimista" />
            <Stat label="Mediana" value={view.format(view.stats.p50)} note="P50" strong />
            <Stat label="P90" value={view.format(view.stats.p90)} note="optimista" />
            <Stat
              label={view.probLabel}
              value={fmtPct(view.prob, 0)}
              note="prob. de éxito"
              good={view.prob >= 0.5}
            />
          </div>

          <div className="mt-4 rounded-[var(--radius-data)] border bg-card p-4">
            <DistributionHistogram values={view.values} markers={markers} hurdle={view.hurdle} format={view.format} />
          </div>

          <p className="mt-2 text-xs text-muted-foreground">
            Simulación BASE: 3 variables (precio ±15%, costo ±10%, ritmo de ventas ±30%), distribución
            uniforme e independiente · {res?.n_validas?.toLocaleString("es-CO")} corridas válidas. Barras
            a la izquierda del umbral = zona de no-éxito. <em>Próximo nivel:</em> distribuciones
            calibradas (log-normal/beta) + correlaciones.
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
