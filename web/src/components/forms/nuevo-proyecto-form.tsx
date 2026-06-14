"use client";

import { useMemo, useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { Plus, Trash2, Loader2, Check, AlertTriangle } from "lucide-react";
import { crearYAprobarProyecto } from "@/lib/actions";
import { fmtCop } from "@/lib/format";
import { cn } from "@/lib/utils";

/**
 * Formulario de ALTA de proyecto (Fase 5). El usuario llena lo ESPECÍFICO del proyecto (datos,
 * etapas, costos, lote); los parámetros macro (WACC build-up, financieros, cronograma) van con el
 * ESTÁNDAR CG pre-cargado (editables en una fase posterior). Al enviar: arma el `par`, lo manda al
 * Server Action que crea + aprueba → el motor recalcula y la ficha queda visible.
 *
 * NO calcula cifras: el `ventas` que muestra por etapa es una ESTIMACIÓN de previsualización
 * (und × precio × área / 1000) solo para orientar; las cifras oficiales las produce el motor.
 */

// --- Estándar CG (de la plantilla Navarra): el usuario no los toca en esta fase. ---
const FINANCIERO_CG = {
  renta: 0.35, split_cg: 0.7, pct_ci: 0.3, sep_und_miles: 5000, diferido_sep: 4,
  tasa_credito_ea: 0.155, cobertura_cc: 0.8, monto_cc_pct: 0.8, tir_apalancada_ref: 0.2,
};
const WACC_CG = {
  beta_us: 1.29, tax_us: 13.3, de_us: 21.56, tax_col: 33.0, de_col: 233.3, rf: 0.12,
  rm: 12.44, rp: 3.14, inf_col: 5.1, inf_us: 2.9, tasa_d: 15.0, spread: 10.43, eq_w: 30.0,
};
const CRONOGRAMA_CG = {
  dur_obra: 40, moda_pert: 24, curva: "Gauss", rel_materiales: 0.8, ea_materiales: 0.06, ea_mano_obra: 0.12,
};
const COSTOS_EXTRA_CG = { recon_codensa: 0.002, hon_construccion: 0.035, hon_gerencia: 0.03, hon_ventas: 0.015 };

const ESTADOS = [
  { v: "prefactibilidad", l: "Pre-factibilidad" },
  { v: "aprobado", l: "Aprobado" },
  { v: "construccion", l: "Construcción" },
  { v: "entregado", l: "Entregado" },
];
const TIPOS = ["VIS", "VIP", "No VIS"];
const METODOS = ["$/m²", "$/und"] as const;

type Etapa = {
  nom: string; und: string; metodo: (typeof METODOS)[number]; precio: string;
  area_und: string; vmes: string; pe_pct: string; fecha_inicio: string;
  dur_obra: string; escrituracion: string;
};

const etapaVacia = (n: number): Etapa => ({
  nom: `Etapa ${n}`, und: "", metodo: "$/m²", precio: "", area_und: "",
  vmes: "", pe_pct: "60", fecha_inicio: "", dur_obra: "26", escrituracion: "30",
});

const num = (s: string): number => {
  const v = parseFloat(String(s).replace(/[^\d.-]/g, ""));
  return Number.isFinite(v) ? v : 0;
};

const ventasEtapaMiles = (e: Etapa): number => {
  const base = num(e.und) * num(e.precio);
  return Math.round((e.metodo === "$/m²" ? base * num(e.area_und) : base) / 1000);
};

const inputCls =
  "num w-full rounded-[var(--radius-data)] border bg-card px-2.5 py-1.5 text-right text-sm text-foreground " +
  "outline-none transition-colors [transition-timing-function:var(--ease-out)] focus:border-primary " +
  "placeholder:text-muted-foreground/40";
const textCls = inputCls.replace("text-right", "text-left").replace("num ", "");
const selectCls =
  "w-full rounded-[var(--radius-data)] border bg-card px-2 py-1.5 text-sm text-foreground outline-none focus:border-primary";

export function NuevoProyectoForm() {
  const router = useRouter();
  const [pending, start] = useTransition();
  const [err, setErr] = useState<string | null>(null);
  const [warn, setWarn] = useState<string | null>(null);

  const [meta, setMeta] = useState({ nombre: "", tipo: "VIS", estado: "prefactibilidad", ubicacion: "", zona: "" });
  const [etapas, setEtapas] = useState<Etapa[]>([etapaVacia(1)]);
  const [costos, setCostos] = useState({ directos: "55", indirectos: "18", honorarios: "8", util_lote: "4.5" });
  const [loteBrutoMiles, setLoteBrutoMiles] = useState("");
  const [areas, setAreas] = useState({ m2_vendibles: "", m2_construidos: "", lote_bruta: "", lote_util: "" });

  const setEtapa = (i: number, patch: Partial<Etapa>) =>
    setEtapas((es) => es.map((e, j) => (j === i ? { ...e, ...patch } : e)));
  const addEtapa = () => setEtapas((es) => [...es, etapaVacia(es.length + 1)]);
  const delEtapa = (i: number) => setEtapas((es) => (es.length > 1 ? es.filter((_, j) => j !== i) : es));

  const ventasTotal = useMemo(() => etapas.reduce((s, e) => s + ventasEtapaMiles(e), 0), [etapas]);
  const undTotal = useMemo(() => etapas.reduce((s, e) => s + num(e.und), 0), [etapas]);
  const costosSuma = num(costos.directos) + num(costos.indirectos) + num(costos.honorarios) + num(costos.util_lote);

  function validate(): string | null {
    if (!meta.nombre.trim()) return "El nombre del proyecto es obligatorio.";
    for (const [i, e] of etapas.entries()) {
      const n = i + 1;
      if (num(e.und) <= 0) return `Etapa ${n}: las unidades deben ser mayores que 0.`;
      if (num(e.precio) <= 0) return `Etapa ${n}: el precio debe ser mayor que 0.`;
      if (e.metodo === "$/m²" && num(e.area_und) <= 0)
        return `Etapa ${n}: con método $/m² el área por unidad (m²) debe ser mayor que 0.`;
      if (num(e.vmes) <= 0) return `Etapa ${n}: las ventas por mes deben ser mayores que 0.`;
      if (!e.fecha_inicio) return `Etapa ${n}: define la fecha de inicio de ventas.`;
      if (num(e.dur_obra) <= 0) return `Etapa ${n}: la duración de obra (meses) debe ser mayor que 0.`;
    }
    if (costosSuma <= 0) return "Define la estructura de costos (% de ventas).";
    if (num(loteBrutoMiles) <= 0) return "El valor del lote (miles COP) debe ser mayor que 0.";
    return null;
  }

  function buildPar(): Record<string, unknown> {
    const etapasPar = etapas.map((e, i) => ({
      cod: i + 1,
      nom: e.nom.trim() || `Etapa ${i + 1}`,
      und: num(e.und),
      metodo: e.metodo,
      precio: num(e.precio),
      area_und: num(e.area_und),
      ventas_miles: ventasEtapaMiles(e),
      vmes: num(e.vmes),
      frec: 1,
      pe_pct: num(e.pe_pct) / 100,
      fecha_inicio: e.fecha_inicio,
      sucesora: i === 0 ? null : i, // encadenamiento: la etapa i sucede a la i-1 (cod = i)
      desfase: 0,
      obra_offset: 1,
      dur_obra: num(e.dur_obra),
      escrituracion: num(e.escrituracion),
      emes: 45,
      efrec: 1,
    }));
    const par: Record<string, unknown> = {
      meta: {
        nombre: meta.nombre.trim(),
        tipo: meta.tipo,
        estado: meta.estado,
        ubicacion: meta.ubicacion.trim() || null,
        zona: meta.zona.trim() || null,
        unidades: undTotal,
        moneda: "miles COP",
      },
      etapas: etapasPar,
      costos_pct: {
        directos: num(costos.directos) / 100,
        indirectos: num(costos.indirectos) / 100,
        honorarios: num(costos.honorarios) / 100,
        util_lote: num(costos.util_lote) / 100,
        ...COSTOS_EXTRA_CG,
      },
      lote_bruto_miles: num(loteBrutoMiles),
      cronograma: CRONOGRAMA_CG,
      financiero: { ...FINANCIERO_CG, wacc: WACC_CG },
      schema_version: 1,
    };
    if (Object.values(areas).some((v) => v.trim() !== "")) {
      par.areas = {
        m2_vendibles: num(areas.m2_vendibles),
        m2_construidos: num(areas.m2_construidos),
        lote_bruta: num(areas.lote_bruta),
        lote_util: num(areas.lote_util),
      };
    }
    return par;
  }

  function submit() {
    const v = validate();
    if (v) {
      setErr(v);
      setWarn(null);
      return;
    }
    setErr(null);
    setWarn(null);
    start(async () => {
      const res = await crearYAprobarProyecto({ par: buildPar(), nombre: meta.nombre.trim() });
      if (res.ok) {
        if (!res.checks_ok) {
          // se creó, pero algún cuadre del motor no cierra: avisa antes de navegar.
          setWarn("Proyecto creado, pero algún cuadre del motor no cierra. Revísalo en la ficha.");
        }
        router.push(`/proyectos/${res.slug}`);
      } else {
        setErr(res.message);
      }
    });
  }

  return (
    <div className="space-y-8">
      {/* 1 · Datos generales */}
      <Section title="Datos generales" hint="Identificación del proyecto.">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Field label="Nombre" required className="sm:col-span-2 lg:col-span-1">
            <input
              className={textCls}
              value={meta.nombre}
              onChange={(e) => setMeta({ ...meta, nombre: e.target.value })}
              placeholder="Ej. Navarra Apartamentos"
              autoFocus
            />
          </Field>
          <Field label="Tipo">
            <select className={selectCls} value={meta.tipo} onChange={(e) => setMeta({ ...meta, tipo: e.target.value })}>
              {TIPOS.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </Field>
          <Field label="Fase">
            <select className={selectCls} value={meta.estado} onChange={(e) => setMeta({ ...meta, estado: e.target.value })}>
              {ESTADOS.map((s) => (
                <option key={s.v} value={s.v}>{s.l}</option>
              ))}
            </select>
          </Field>
          <Field label="Ubicación">
            <input className={textCls} value={meta.ubicacion} onChange={(e) => setMeta({ ...meta, ubicacion: e.target.value })} placeholder="Bogotá" />
          </Field>
          <Field label="Zona / barrio">
            <input className={textCls} value={meta.zona} onChange={(e) => setMeta({ ...meta, zona: e.target.value })} placeholder="Fontibón" />
          </Field>
        </div>
      </Section>

      {/* 2 · Etapas */}
      <Section
        title="Etapas y ventas"
        hint="Cada etapa = un frente de venta. El motor encadena las etapas en serie."
        right={
          <span className="num text-xs text-muted-foreground">
            {ventasTotal > 0 ? `≈ ${fmtCop(ventasTotal)} · ${undTotal} und` : null}
          </span>
        }
      >
        <div className="space-y-3">
          {etapas.map((e, i) => {
            const v = ventasEtapaMiles(e);
            return (
              <div key={i} className="rounded-[var(--radius-data)] border bg-card p-4">
                <div className="mb-3 flex items-center gap-2">
                  <input
                    className="-ml-1 rounded-[3px] border border-transparent bg-transparent px-1 py-0.5 text-sm font-medium hover:border-[var(--rule)] focus:border-primary focus:outline-none"
                    value={e.nom}
                    onChange={(ev) => setEtapa(i, { nom: ev.target.value })}
                    aria-label={`Nombre de la etapa ${i + 1}`}
                  />
                  <span className="num ml-auto text-xs text-muted-foreground">{v > 0 ? `≈ ${fmtCop(v)}` : "—"}</span>
                  {etapas.length > 1 ? (
                    <button
                      type="button"
                      onClick={() => delEtapa(i)}
                      className="rounded-[3px] p-1 text-muted-foreground transition-colors hover:bg-danger/10 hover:text-danger"
                      aria-label={`Eliminar la etapa ${i + 1}`}
                    >
                      <Trash2 className="size-3.5" />
                    </button>
                  ) : null}
                </div>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                  <Field label="Unidades">
                    <input className={inputCls} inputMode="numeric" value={e.und} onChange={(ev) => setEtapa(i, { und: ev.target.value })} placeholder="317" />
                  </Field>
                  <Field label="Método">
                    <select className={selectCls} value={e.metodo} onChange={(ev) => setEtapa(i, { metodo: ev.target.value as Etapa["metodo"] })}>
                      {METODOS.map((m) => (
                        <option key={m} value={m}>{m}</option>
                      ))}
                    </select>
                  </Field>
                  <Field label={e.metodo === "$/m²" ? "Precio ($/m²)" : "Precio ($/und)"}>
                    <input className={inputCls} inputMode="decimal" value={e.precio} onChange={(ev) => setEtapa(i, { precio: ev.target.value })} placeholder={e.metodo === "$/m²" ? "3850000" : "200000000"} />
                  </Field>
                  <Field label="Área / und (m²)" hint={e.metodo === "$/und" ? "Solo para indicadores" : undefined}>
                    <input className={inputCls} inputMode="decimal" value={e.area_und} onChange={(ev) => setEtapa(i, { area_und: ev.target.value })} placeholder="52" />
                  </Field>
                  <Field label="Ventas / mes (und)">
                    <input className={inputCls} inputMode="numeric" value={e.vmes} onChange={(ev) => setEtapa(i, { vmes: ev.target.value })} placeholder="15" />
                  </Field>
                  <Field label="Punto equilibrio (%)">
                    <input className={inputCls} inputMode="decimal" value={e.pe_pct} onChange={(ev) => setEtapa(i, { pe_pct: ev.target.value })} placeholder="60" />
                  </Field>
                  <Field label="Inicio ventas">
                    <input type="date" className={cn(inputCls, "text-left")} value={e.fecha_inicio} onChange={(ev) => setEtapa(i, { fecha_inicio: ev.target.value })} />
                  </Field>
                  <Field label="Dur. obra (meses)">
                    <input className={inputCls} inputMode="numeric" value={e.dur_obra} onChange={(ev) => setEtapa(i, { dur_obra: ev.target.value })} placeholder="26" />
                  </Field>
                  <Field label="Escrituración (mes)" hint="Meses desde inicio de ventas">
                    <input className={inputCls} inputMode="numeric" value={e.escrituracion} onChange={(ev) => setEtapa(i, { escrituracion: ev.target.value })} placeholder="30" />
                  </Field>
                </div>
              </div>
            );
          })}
          <button
            type="button"
            onClick={addEtapa}
            className="inline-flex items-center gap-1.5 rounded-[var(--radius-data)] border border-dashed px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:border-primary hover:text-foreground"
          >
            <Plus className="size-4" /> Agregar etapa
          </button>
        </div>
      </Section>

      {/* 3 · Costos + lote */}
      <Section title="Costos y lote" hint="Costos como % de las ventas. El lote en miles de COP.">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Field label="Costos directos (%)"><input className={inputCls} inputMode="decimal" value={costos.directos} onChange={(e) => setCostos({ ...costos, directos: e.target.value })} /></Field>
          <Field label="Costos indirectos (%)"><input className={inputCls} inputMode="decimal" value={costos.indirectos} onChange={(e) => setCostos({ ...costos, indirectos: e.target.value })} /></Field>
          <Field label="Honorarios (%)"><input className={inputCls} inputMode="decimal" value={costos.honorarios} onChange={(e) => setCostos({ ...costos, honorarios: e.target.value })} /></Field>
          <Field label="Utilidad del lote (%)"><input className={inputCls} inputMode="decimal" value={costos.util_lote} onChange={(e) => setCostos({ ...costos, util_lote: e.target.value })} /></Field>
          <Field label="Valor del lote (miles COP)" required hint="18000000 = 18 mil M">
            <input className={inputCls} inputMode="decimal" value={loteBrutoMiles} onChange={(e) => setLoteBrutoMiles(e.target.value)} placeholder="18000000" />
          </Field>
          <div className="flex items-end pb-1.5 text-xs text-muted-foreground">
            Costos suman <span className="num mx-1 font-medium text-foreground">{costosSuma.toFixed(1)}%</span> de ventas
          </div>
        </div>
      </Section>

      {/* 4 · Áreas (opcional) */}
      <details className="group rounded-[var(--radius-data)] border bg-card">
        <summary className="flex cursor-pointer list-none items-center gap-2 px-4 py-3 text-sm font-medium">
          <span className="h-3.5 w-0.5 rounded-full bg-primary" aria-hidden />
          Áreas <span className="font-normal text-muted-foreground">(opcional, para los indicadores $/m²)</span>
          <span className="ml-auto text-xs text-muted-foreground transition-transform group-open:rotate-90">›</span>
        </summary>
        <div className="grid gap-4 border-t border-[var(--rule)] p-4 sm:grid-cols-2 lg:grid-cols-4">
          <Field label="m² vendibles"><input className={inputCls} inputMode="decimal" value={areas.m2_vendibles} onChange={(e) => setAreas({ ...areas, m2_vendibles: e.target.value })} placeholder="49452" /></Field>
          <Field label="m² construidos"><input className={inputCls} inputMode="decimal" value={areas.m2_construidos} onChange={(e) => setAreas({ ...areas, m2_construidos: e.target.value })} placeholder="68000" /></Field>
          <Field label="Lote bruta (m²)"><input className={inputCls} inputMode="decimal" value={areas.lote_bruta} onChange={(e) => setAreas({ ...areas, lote_bruta: e.target.value })} placeholder="35000" /></Field>
          <Field label="Lote útil (m²)"><input className={inputCls} inputMode="decimal" value={areas.lote_util} onChange={(e) => setAreas({ ...areas, lote_util: e.target.value })} placeholder="28000" /></Field>
        </div>
      </details>

      {/* Nota de defaults CG */}
      <p className="text-xs text-muted-foreground">
        El costo de capital (WACC build-up), los supuestos financieros (crédito, fiducia, separación) y el
        cronograma usan el <strong className="font-medium text-foreground">estándar CG</strong>. Serán
        editables por proyecto en una fase posterior.
      </p>

      {/* Errores / avisos */}
      {err ? (
        <div className="flex items-start gap-2 rounded-[var(--radius-data)] border border-danger/30 bg-danger/5 px-4 py-3 text-sm text-danger">
          <AlertTriangle className="mt-0.5 size-4 shrink-0" />
          <span>{err}</span>
        </div>
      ) : null}
      {warn ? (
        <div className="flex items-start gap-2 rounded-[var(--radius-data)] border border-warning/30 bg-warning/5 px-4 py-3 text-sm text-warning">
          <AlertTriangle className="mt-0.5 size-4 shrink-0" />
          <span>{warn}</span>
        </div>
      ) : null}

      {/* Acción */}
      <div className="flex items-center justify-end gap-3 border-t border-[var(--rule)] pt-5">
        <button
          type="button"
          onClick={() => router.push("/")}
          className="rounded-[var(--radius-data)] px-3 py-2 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          Cancelar
        </button>
        <button
          type="button"
          onClick={submit}
          disabled={pending}
          className="inline-flex items-center gap-1.5 rounded-[var(--radius-data)] bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-[opacity,transform] [transition-timing-function:var(--ease-out)] hover:opacity-90 active:scale-[0.98] disabled:opacity-60"
        >
          {pending ? <Loader2 className="size-4 animate-spin" /> : <Check className="size-4" />}
          {pending ? "Creando…" : "Crear y aprobar proyecto"}
        </button>
      </div>
    </div>
  );
}

function Section({
  title,
  hint,
  right,
  children,
}: {
  title: string;
  hint?: string;
  right?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section>
      <div className="mb-3 flex items-center gap-2">
        <span className="h-3.5 w-0.5 rounded-full bg-primary" aria-hidden />
        <h2 className="text-sm font-medium">{title}</h2>
        {right ? <div className="ml-auto">{right}</div> : null}
      </div>
      {hint ? <p className="mb-3 text-xs text-muted-foreground">{hint}</p> : null}
      {children}
    </section>
  );
}

function Field({
  label,
  required,
  hint,
  className,
  children,
}: {
  label: string;
  required?: boolean;
  hint?: string;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <label className={cn("block", className)}>
      <span className="mb-1 flex items-center gap-1 text-xs font-medium text-muted-foreground">
        {label}
        {required ? <span className="text-primary">*</span> : null}
      </span>
      {children}
      {hint ? <span className="mt-0.5 block text-[0.7rem] text-muted-foreground/70">{hint}</span> : null}
    </label>
  );
}
