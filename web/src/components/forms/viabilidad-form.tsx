"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2, AlertTriangle } from "lucide-react";
import type { DueDiligenceItem } from "@/lib/api";
import { editarViabilidadYAprobar, type CrearProyectoResult } from "@/lib/actions";
import { cn } from "@/lib/utils";

/** Estado editable de un ítem de due diligence (la plantilla viene pre-llenada del motor). */
type DDRow = { frente: string; item: string; estado: string; impacto: string; nota: string; mitigacion: string };

const ESTADOS = ["pendiente", "ok", "alerta"];
const IMPACTOS = ["alto", "medio", "bajo"];

// Campos canónicos de POT y de mercado (los que el motor contrasta + el contexto informativo).
const POT_FIELDS: { key: string; label: string; step?: string }[] = [
  { key: "indice_construccion_max", label: "Índice de construcción (máx)", step: "0.01" },
  { key: "densidad_max_und_ha", label: "Densidad máx (und/ha)", step: "1" },
  { key: "aprovechamiento_max", label: "Aprovechamiento máx (0–1)", step: "0.01" },
  { key: "altura_max_pisos", label: "Altura máx (pisos)", step: "1" },
  { key: "cesion_min_pct", label: "Cesión mínima (0–1)", step: "0.01" },
];
const MKT_NUM: { key: string; label: string; step?: string }[] = [
  { key: "precio_m2_mercado", label: "Precio comparable /m² (COP)", step: "1000" },
  { key: "absorcion_mercado_und_mes", label: "Absorción de mercado (und/mes)", step: "0.5" },
];
const MKT_TXT: { key: string; label: string }[] = [
  { key: "oferta_competencia", label: "Oferta de competencia" },
  { key: "fuente", label: "Fuente / corte" },
];

function strOf(v: unknown): string {
  return v == null ? "" : String(v);
}

export function ViabilidadForm({
  slug,
  frentes,
  ddItems,
  pot,
  mercado,
}: {
  slug: string;
  frentes: { clave: string; nombre: string }[];
  ddItems: DueDiligenceItem[];
  pot: Record<string, unknown>;
  mercado: Record<string, unknown>;
}) {
  const router = useRouter();
  const [pending, start] = useTransition();
  const [result, setResult] = useState<CrearProyectoResult | null>(null);

  const [dd, setDd] = useState<DDRow[]>(() =>
    ddItems.map((it) => ({
      frente: it.frente,
      item: it.item,
      estado: it.estado || "pendiente",
      impacto: it.impacto || "medio",
      nota: strOf(it.nota),
      mitigacion: strOf(it.mitigacion),
    })),
  );
  const [potF, setPotF] = useState<Record<string, string>>(() =>
    Object.fromEntries(POT_FIELDS.map((f) => [f.key, strOf(pot[f.key])])),
  );
  const [mktF, setMktF] = useState<Record<string, string>>(() =>
    Object.fromEntries([...MKT_NUM, ...MKT_TXT].map((f) => [f.key, strOf(mercado[f.key])])),
  );

  function setRow(i: number, patch: Partial<DDRow>) {
    setDd((prev) => prev.map((r, j) => (j === i ? { ...r, ...patch } : r)));
  }

  function submit() {
    setResult(null);
    // Due diligence: el registro completo (estado/impacto + nota/mitigación si las hay).
    const dueDiligence = dd.map((r) => ({
      frente: r.frente,
      item: r.item,
      estado: r.estado,
      impacto: r.impacto,
      ...(r.nota.trim() ? { nota: r.nota.trim() } : {}),
      ...(r.mitigacion.trim() ? { mitigacion: r.mitigacion.trim() } : {}),
    }));
    // POT / mercado: solo los campos con valor (numéricos parseados; texto tal cual).
    const potOut: Record<string, unknown> = {};
    for (const f of POT_FIELDS) {
      const v = potF[f.key]?.trim();
      if (v) potOut[f.key] = Number(v);
    }
    const mktOut: Record<string, unknown> = {};
    for (const f of MKT_NUM) {
      const v = mktF[f.key]?.trim();
      if (v) mktOut[f.key] = Number(v);
    }
    for (const f of MKT_TXT) {
      const v = mktF[f.key]?.trim();
      if (v) mktOut[f.key] = v;
    }

    start(async () => {
      const res = await editarViabilidadYAprobar({ slug, dueDiligence, pot: potOut, mercado: mktOut });
      setResult(res);
      if (res.ok) router.push(`/proyectos/${slug}`);
    });
  }

  return (
    <div className="space-y-8">
      {/* Due diligence por frente */}
      <section className="space-y-4">
        <h2 className="text-sm font-semibold text-foreground">Due diligence</h2>
        {frentes.map((f) => {
          const rows = dd.map((r, i) => ({ r, i })).filter(({ r }) => r.frente === f.clave);
          if (rows.length === 0) return null;
          return (
            <div key={f.clave} className="rounded-[var(--radius-data)] border bg-card p-4">
              <div className="mb-3 text-sm font-medium text-foreground">{f.nombre}</div>
              <div className="space-y-3">
                {rows.map(({ r, i }) => (
                  <div key={`${r.frente}-${r.item}`} className="grid gap-2 border-b border-rule pb-3 last:border-0 last:pb-0 sm:grid-cols-[1fr_auto_auto]">
                    <div className="self-center text-sm">{r.item}</div>
                    <Select label="Estado" value={r.estado} options={ESTADOS} onChange={(v) => setRow(i, { estado: v })} />
                    <Select label="Impacto" value={r.impacto} options={IMPACTOS} onChange={(v) => setRow(i, { impacto: v })} />
                    <input
                      type="text"
                      placeholder="Nota / mitigación (opcional)"
                      value={r.mitigacion || r.nota}
                      onChange={(e) => setRow(i, r.estado === "alerta" ? { mitigacion: e.target.value } : { nota: e.target.value })}
                      className="rounded-[var(--radius-data)] border bg-background px-2 py-1 text-sm sm:col-span-3"
                    />
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </section>

      {/* Límites POT */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-foreground">Límites POT de la zona</h2>
        <div className="grid gap-3 rounded-[var(--radius-data)] border bg-card p-4 sm:grid-cols-2 lg:grid-cols-3">
          {POT_FIELDS.map((f) => (
            <Field key={f.key} label={f.label}>
              <input
                type="number"
                step={f.step}
                value={potF[f.key]}
                onChange={(e) => setPotF((p) => ({ ...p, [f.key]: e.target.value }))}
                className="num w-full rounded-[var(--radius-data)] border bg-background px-2 py-1 text-sm tabular-nums"
              />
            </Field>
          ))}
        </div>
      </section>

      {/* Comparables de mercado */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-foreground">Comparables de mercado</h2>
        <div className="grid gap-3 rounded-[var(--radius-data)] border bg-card p-4 sm:grid-cols-2">
          {MKT_NUM.map((f) => (
            <Field key={f.key} label={f.label}>
              <input
                type="number"
                step={f.step}
                value={mktF[f.key]}
                onChange={(e) => setMktF((p) => ({ ...p, [f.key]: e.target.value }))}
                className="num w-full rounded-[var(--radius-data)] border bg-background px-2 py-1 text-sm tabular-nums"
              />
            </Field>
          ))}
          {MKT_TXT.map((f) => (
            <Field key={f.key} label={f.label}>
              <input
                type="text"
                value={mktF[f.key]}
                onChange={(e) => setMktF((p) => ({ ...p, [f.key]: e.target.value }))}
                className="w-full rounded-[var(--radius-data)] border bg-background px-2 py-1 text-sm"
              />
            </Field>
          ))}
        </div>
      </section>

      {result && !result.ok ? (
        <div className="flex items-start gap-2 rounded-[var(--radius-data)] border border-danger/30 bg-danger/5 p-3 text-sm text-danger">
          <AlertTriangle className="mt-0.5 size-4 shrink-0" aria-hidden /> {result.message}
        </div>
      ) : null}
      {result?.ok ? (
        <div className="flex items-center gap-2 rounded-[var(--radius-data)] border border-success/30 bg-success/5 p-3 text-sm text-success">
          <CheckCircle2 className="size-4 shrink-0" aria-hidden /> Guardado. Volviendo a la ficha…
        </div>
      ) : null}

      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={submit}
          disabled={pending}
          className={cn(
            "inline-flex items-center gap-1.5 rounded-[var(--radius-data)] bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-[transform,opacity] [transition-timing-function:var(--ease-out)] active:scale-[0.98]",
            pending && "opacity-60",
          )}
        >
          {pending ? "Guardando…" : "Guardar viabilidad y re-aprobar"}
        </button>
        <span className="text-[0.7rem] text-muted-foreground">
          Crea una versión nueva del escenario. No cambia las cifras financieras (el motor ignora estos
          registros).
        </span>
      </div>
    </div>
  );
}

function Select({ label, value, options, onChange }: { label: string; value: string; options: string[]; onChange: (v: string) => void }) {
  return (
    <label className="flex items-center gap-1.5 text-[0.7rem] text-muted-foreground">
      <span className="sr-only sm:not-sr-only">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-[var(--radius-data)] border bg-background px-2 py-1 text-sm capitalize text-foreground"
      >
        {options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </label>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1 text-[0.7rem] text-muted-foreground">
      <span>{label}</span>
      {children}
    </label>
  );
}
