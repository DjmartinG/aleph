"use client";

import { useEffect, useRef, useState, useTransition } from "react";
import type { Recalc, GoalSeek } from "@/lib/api";
import { recalcular, resolverMeta } from "@/lib/actions";
import { fmtPct, fmtCop } from "@/lib/format";
import { Banner } from "@/components/banner";

/** M4b — Panel de control sobre el P&G: sliders en vivo (forward) + goal-seek ("devolvernos").
 *  Las TIR/VPN son DIRECCIONALES (base mensual); el margen es exacto. La cifra oficial es la de la ficha. */
export function PanelControl({ slug }: { slug: string }) {
  const [precio, setPrecio] = useState(0);
  const [costo, setCosto] = useState(0);
  const [ritmo, setRitmo] = useState(0);
  const [data, setData] = useState<Recalc | null>(null);
  const [pending, start] = useTransition();
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => {
      start(async () => {
        try {
          setData(await recalcular(slug, { precio, costo, ritmo }));
        } catch {
          /* silencioso: el panel queda con el último valor bueno */
        }
      });
    }, 220);
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, [precio, costo, ritmo, slug]);

  const r = data?.resultado;
  const b = data?.base;

  return (
    <div className="space-y-7">
      <Banner tone="warning" label="Simulador">
        Mueve los drivers para ver el impacto. El <span className="font-medium">margen es exacto</span>; la
        TIR y el VPN son <span className="font-medium">simulados</span> (base mensual, sirven para comparar) —
        la cifra oficial está en la pestaña Resumen.
      </Banner>

      <div className="grid gap-6 lg:grid-cols-[1fr_1.2fr]">
        {/* Sliders */}
        <div className="space-y-5 rounded-[var(--radius-data)] border bg-card p-5">
          <h3 className="text-sm font-semibold">Drivers</h3>
          <Slider label="Precio de venta" value={precio} onChange={setPrecio} />
          <Slider label="Costo directo" value={costo} onChange={setCosto} />
          <Slider label="Ritmo de ventas" value={ritmo} onChange={setRitmo} />
          <button
            type="button"
            onClick={() => { setPrecio(0); setCosto(0); setRitmo(0); }}
            className="text-xs text-muted-foreground underline-offset-2 hover:underline"
          >
            Restablecer
          </button>
        </div>

        {/* KPIs en vivo */}
        <div className={"grid grid-cols-2 gap-x-6 gap-y-5 rounded-[var(--radius-data)] border bg-card p-5 transition-opacity " + (pending ? "opacity-60" : "")}>
          <Kpi label="Margen" hero value={fmtPct(r?.margen)} delta={pct(r?.margen, b?.margen)} />
          <Kpi label="TIR proyecto · sim." value={fmtPct(r?.tir_proyecto)} delta={pct(r?.tir_proyecto, b?.tir_proyecto)} />
          <Kpi label="TIR socio · sim." value={fmtPct(r?.tir_equity)} delta={pct(r?.tir_equity, b?.tir_equity)} />
          <Kpi label="VPN proyecto · sim." value={fmtCop(r?.vpn_proyecto)} delta={cop(r?.vpn_proyecto, b?.vpn_proyecto)} />
          <Kpi label="Exposición máx." value={fmtCop(r?.exposicion_maxima)} delta={cop(r?.exposicion_maxima, b?.exposicion_maxima)} />
          <Kpi label="Punto de equilibrio" value={r ? `mes ${r.breakeven_mes}` : "—"} />
        </div>
      </div>

      <GoalSeekPanel slug={slug} />
    </div>
  );
}

function Slider({ label, value, onChange }: { label: string; value: number; onChange: (n: number) => void }) {
  return (
    <div>
      <div className="mb-1 flex items-baseline justify-between">
        <span className="text-sm">{label}</span>
        <span className={"num text-sm font-medium " + (value > 0 ? "text-primary" : value < 0 ? "text-[var(--cg-amber)]" : "text-muted-foreground")}>
          {value > 0 ? "+" : ""}{(value * 100).toFixed(0)}%
        </span>
      </div>
      <input
        type="range" min={-0.3} max={0.3} step={0.01} value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full accent-[var(--primary)]"
      />
    </div>
  );
}

function Kpi({ label, value, delta, hero }: { label: string; value: string; delta?: string; hero?: boolean }) {
  return (
    <div>
      <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className={"num mt-0.5 font-semibold tracking-tight " + (hero ? "text-2xl" : "text-lg")}>{value}</div>
      {delta ? <div className="num text-[0.72rem] text-muted-foreground">{delta}</div> : null}
    </div>
  );
}

function pct(a?: number | null, base?: number | null): string | undefined {
  if (a === undefined || a === null || base === undefined || base === null) return undefined;
  const d = (a - base) * 100;
  return `${d >= 0 ? "+" : ""}${d.toFixed(1)} pp vs base`;
}
function cop(a?: number | null, base?: number | null): string | undefined {
  if (a === undefined || a === null || base === undefined || base === null) return undefined;
  const d = a - base;
  return `${d >= 0 ? "+" : ""}${fmtCop(d)} vs base`;
}

// ---------- Goal-seek ("devolvernos") ----------

const OBJETIVOS = [
  { key: "margen", label: "Margen", unidad: "%", factor: 0.01 },
  { key: "tir_proyecto", label: "TIR proyecto", unidad: "%", factor: 0.01 },
  { key: "tir_equity", label: "TIR socio", unidad: "%", factor: 0.01 },
  { key: "vpn_proyecto", label: "VPN proyecto", unidad: "mil M", factor: 1_000_000 },
] as const;

const DRIVER_LABEL: Record<string, string> = {
  precio: "Precio de venta",
  costo: "Costo directo",
  ritmo: "Ritmo de ventas",
};

function GoalSeekPanel({ slug }: { slug: string }) {
  const [objetivo, setObjetivo] = useState<string>("margen");
  const [metaInput, setMetaInput] = useState<string>("8");
  const [res, setRes] = useState<GoalSeek | null>(null);
  const [pending, start] = useTransition();
  const [err, setErr] = useState<string | null>(null);

  const obj = OBJETIVOS.find((o) => o.key === objetivo)!;

  function resolver() {
    setErr(null);
    const meta = parseFloat(metaInput) * obj.factor;
    if (!isFinite(meta)) { setErr("Meta inválida"); return; }
    start(async () => {
      try {
        setRes(await resolverMeta(slug, objetivo, meta));
      } catch {
        setErr("No se pudo resolver. Intenta otra meta.");
      }
    });
  }

  return (
    <section className="rounded-[var(--radius-data)] border bg-card p-5">
      <h3 className="text-sm font-semibold">Devolverme a una meta (goal-seek)</h3>
      <p className="mb-3 mt-0.5 text-sm text-muted-foreground">
        Fija una meta y el motor calcula cuánto habría que mover cada driver para alcanzarla.
      </p>
      <div className="flex flex-wrap items-end gap-3">
        <label className="text-sm">
          <span className="mb-1 block text-xs text-muted-foreground">Objetivo</span>
          <select
            value={objetivo}
            onChange={(e) => setObjetivo(e.target.value)}
            className="rounded-[var(--radius-data)] border bg-background px-2 py-1.5 text-sm"
          >
            {OBJETIVOS.map((o) => <option key={o.key} value={o.key}>{o.label}</option>)}
          </select>
        </label>
        <label className="text-sm">
          <span className="mb-1 block text-xs text-muted-foreground">Meta ({obj.unidad})</span>
          <input
            type="number" value={metaInput} onChange={(e) => setMetaInput(e.target.value)}
            className="num w-28 rounded-[var(--radius-data)] border bg-background px-2 py-1.5 text-sm"
          />
        </label>
        <button
          type="button" onClick={resolver} disabled={pending}
          className="rounded-[var(--radius-data)] bg-primary px-4 py-1.5 text-sm font-medium text-primary-foreground transition-opacity [transition-timing-function:var(--ease-out)] disabled:opacity-50"
        >
          {pending ? "Resolviendo…" : "Resolver"}
        </button>
      </div>

      {err ? <p className="mt-3 text-sm text-[var(--cg-amber)]">{err}</p> : null}

      {res ? (
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          {Object.entries(res).map(([driver, d]) => (
            <div key={driver} className="rounded-[var(--radius-data)] border p-3">
              <div className="text-xs font-medium text-muted-foreground">{DRIVER_LABEL[driver] ?? driver}</div>
              {d.alcanzable && d.delta !== undefined ? (
                <div className="num mt-1 text-lg font-semibold tracking-tight">
                  {d.delta >= 0 ? "+" : ""}{(d.delta * 100).toFixed(1)}%
                </div>
              ) : (
                <div className="mt-1 text-sm text-muted-foreground">no alcanzable en ±50%</div>
              )}
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}
