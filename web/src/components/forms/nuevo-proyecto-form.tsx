"use client";

import { useMemo, useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { Plus, Trash2, Loader2, Check, AlertTriangle } from "lucide-react";
import { crearYAprobarProyecto, editarYAprobarProyecto } from "@/lib/actions";
import { fmtCop } from "@/lib/format";
import { cn } from "@/lib/utils";

/**
 * Formulario de proyecto (Fase 5 + admin Inc.2), reutilizado para CREAR y EDITAR. El usuario llena lo
 * ESPECÍFICO del proyecto (datos, etapas, costos, lote); en CREAR, los parámetros macro (WACC build-up,
 * financieros, cronograma) van con el ESTÁNDAR CG pre-cargado; en EDITAR, se PRESERVAN los del proyecto
 * (buildPar hace overlay sobre el `par` original). Al enviar: arma el `par` y lo manda al Server Action
 * (crear+aprobar, o nueva-versión+aprobar) → el motor recalcula y la ficha queda actualizada.
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
  /** Etapa original (solo EDITAR): identidad estable para que buildPar haga overlay por IDENTIDAD,
   *  no por posición (preserva los campos extra de ESTA etapa aunque se borren/agreguen otras). */
  _orig?: Record<string, unknown>;
};

const etapaVacia = (n: number): Etapa => ({
  nom: `Etapa ${n}`, und: "", metodo: "$/m²", precio: "", area_und: "",
  vmes: "", pe_pct: "60", fecha_inicio: "", dur_obra: "26", escrituracion: "30",
});

/** Estado del formulario (campos como strings). Lo produce parseParToForm para pre-llenar al EDITAR. */
export interface FormValues {
  meta: { nombre: string; tipo: string; estado: string; ubicacion: string; zona: string };
  etapas: Etapa[];
  costos: { directos: string; indirectos: string; honorarios: string; util_lote: string };
  loteBrutoMiles: string;
  areas: { m2_vendibles: string; m2_construidos: string; lote_bruta: string; lote_util: string };
}

const s = (v: unknown): string => (v === null || v === undefined ? "" : String(v));
/** fracción → string de porcentaje, sin ruido de coma flotante (0.045 → "4.5", 0.6 → "60").
 *  toFixed(10) deja la pérdida del ida-y-vuelta por debajo de 1e-12 (muy por debajo del umbral). */
const pctStr = (v: unknown): string =>
  v === null || v === undefined || v === "" ? "" : String(+(Number(v) * 100).toFixed(10));

/** Inverso de buildPar: convierte el `par` crudo del motor al estado del formulario (para EDITAR). */
export function parseParToForm(par: Record<string, unknown>): FormValues {
  const meta = (par.meta ?? {}) as Record<string, unknown>;
  const etapas = (par.etapas ?? []) as Record<string, unknown>[];
  const c = (par.costos_pct ?? {}) as Record<string, unknown>;
  const a = (par.areas ?? {}) as Record<string, unknown>;
  return {
    meta: {
      nombre: s(meta.nombre),
      tipo: s(meta.tipo) || "VIS",
      estado: s(meta.estado) || "prefactibilidad",
      ubicacion: s(meta.ubicacion),
      zona: s(meta.zona),
    },
    etapas: etapas.length
      ? etapas.map((e) => ({
          nom: s(e.nom),
          und: s(e.und),
          metodo: e.metodo === "$/und" ? "$/und" : "$/m²",
          precio: s(e.precio),
          area_und: s(e.area_und),
          vmes: s(e.vmes),
          pe_pct: pctStr(e.pe_pct),
          fecha_inicio: s(e.fecha_inicio),
          dur_obra: s(e.dur_obra),
          escrituracion: s(e.escrituracion),
          _orig: e, // identidad estable para el overlay por identidad en buildPar
        }))
      : [etapaVacia(1)],
    costos: {
      directos: pctStr(c.directos),
      indirectos: pctStr(c.indirectos),
      honorarios: pctStr(c.honorarios),
      util_lote: pctStr(c.util_lote),
    },
    loteBrutoMiles: s(par.lote_bruto_miles),
    areas: {
      m2_vendibles: s(a.m2_vendibles),
      m2_construidos: s(a.m2_construidos),
      lote_bruta: s(a.lote_bruta),
      lote_util: s(a.lote_util),
    },
  };
}

const num = (s: string): number => {
  const v = parseFloat(String(s).replace(/[^\d.-]/g, ""));
  return Number.isFinite(v) ? v : 0;
};

/** Para campos que el motor exige ENTEROS (unidades, ventas/mes, meses): el contrato (schema.py)
 *  los tipa como int y Pydantic rechaza un float fraccionario con un 422 técnico → redondeamos. */
const numInt = (s: string): number => Math.round(num(s));

const ventasEtapaMiles = (e: Etapa): number => {
  const base = numInt(e.und) * num(e.precio);
  return Math.round((e.metodo === "$/m²" ? base * num(e.area_und) : base) / 1000);
};

const inputCls =
  "num w-full rounded-[var(--radius-data)] border bg-card px-2.5 py-1.5 text-right text-sm text-foreground " +
  "outline-none transition-colors [transition-timing-function:var(--ease-out)] focus:border-primary " +
  "placeholder:text-muted-foreground/40";
const textCls = inputCls.replace("text-right", "text-left").replace("num ", "");
const selectCls =
  "w-full rounded-[var(--radius-data)] border bg-card px-2 py-1.5 text-sm text-foreground outline-none focus:border-primary";

export function ProyectoForm({
  mode = "create",
  initial,
  originalPar,
  slug,
  projectId,
}: {
  mode?: "create" | "edit";
  initial?: FormValues;
  /** `par` original (solo EDITAR): buildPar hace overlay sobre él para preservar WACC/financiero/extras. */
  originalPar?: Record<string, unknown>;
  slug?: string;
  projectId?: string;
} = {}) {
  const router = useRouter();
  const isEdit = mode === "edit";
  const [pending, start] = useTransition();
  const [err, setErr] = useState<string | null>(null);
  const [warn, setWarn] = useState<string | null>(null);

  const [meta, setMeta] = useState(
    initial?.meta ?? { nombre: "", tipo: "VIS", estado: "prefactibilidad", ubicacion: "", zona: "" },
  );
  const [etapas, setEtapas] = useState<Etapa[]>(initial?.etapas ?? [etapaVacia(1)]);
  const [costos, setCostos] = useState(
    initial?.costos ?? { directos: "55", indirectos: "18", honorarios: "8", util_lote: "4.5" },
  );
  const [loteBrutoMiles, setLoteBrutoMiles] = useState(initial?.loteBrutoMiles ?? "");
  const [areas, setAreas] = useState(
    initial?.areas ?? { m2_vendibles: "", m2_construidos: "", lote_bruta: "", lote_util: "" },
  );

  const setEtapa = (i: number, patch: Partial<Etapa>) =>
    setEtapas((es) => es.map((e, j) => (j === i ? { ...e, ...patch } : e)));
  const addEtapa = () => setEtapas((es) => [...es, etapaVacia(es.length + 1)]);
  const delEtapa = (i: number) => setEtapas((es) => (es.length > 1 ? es.filter((_, j) => j !== i) : es));

  const ventasTotal = useMemo(() => etapas.reduce((s, e) => s + ventasEtapaMiles(e), 0), [etapas]);
  const undTotal = useMemo(() => etapas.reduce((s, e) => s + numInt(e.und), 0), [etapas]);
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
    // EDITAR: overlay sobre el par original (preserva financiero/WACC/cronograma). En las etapas,
    // overlay por IDENTIDAD (e._orig), no por posición → al borrar/agregar etapas cada una conserva
    // SUS campos extra (no se barajan). CREAR: defaults CG.
    const etapaBaseCrear = { frec: 1, desfase: 0, obra_offset: 1, emes: 45, efrec: 1 };
    const etapasPar = etapas.map((e, i) => {
      const merged: Record<string, unknown> = {
        ...(e._orig ?? etapaBaseCrear),
        cod: i + 1,
        nom: e.nom.trim() || `Etapa ${i + 1}`,
        und: numInt(e.und),
        metodo: e.metodo,
        precio: num(e.precio),
        area_und: num(e.area_und),
        ventas_miles: ventasEtapaMiles(e),
        vmes: numInt(e.vmes),
        pe_pct: num(e.pe_pct) / 100,
        fecha_inicio: e.fecha_inicio,
        // Modelo DATADO: cada etapa arranca en SU fecha_inicio (sucesora=null). Forzar una cadena
        // serial re-anclaba las etapas 2..N a la PE de la anterior e IGNORABA su fecha → cronograma
        // corrompido (VPN podía cambiar de signo en un "editar sin cambios"). El formulario pide
        // fecha por etapa, así que el modelo correcto es datado.
        sucesora: null,
        dur_obra: numInt(e.dur_obra),
        escrituracion: numInt(e.escrituracion),
      };
      // El precio/ventas los recalcula el formulario → un ventas por vivienda/adicional VIEJO (de un
      // proyecto con tipologías o No-VIS) quedaría obsoleto y corrompería el recaudo. Se eliminan: el
      // motor cae a `ventas_miles`, o los re-deriva de `tipologias` si el proyecto las trae.
      delete merged.ventas_vivienda_miles;
      delete merged.ventas_adicional_miles;
      return merged;
    });
    const baseCostos = (originalPar?.costos_pct as Record<string, unknown> | undefined) ?? COSTOS_EXTRA_CG;
    const baseMeta = (originalPar?.meta as Record<string, unknown> | undefined) ?? {};
    const par: Record<string, unknown> = {
      ...(originalPar ?? { cronograma: CRONOGRAMA_CG, financiero: { ...FINANCIERO_CG, wacc: WACC_CG } }),
      meta: {
        ...baseMeta,
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
        ...baseCostos,
        directos: num(costos.directos) / 100,
        indirectos: num(costos.indirectos) / 100,
        honorarios: num(costos.honorarios) / 100,
        util_lote: num(costos.util_lote) / 100,
      },
      lote_bruto_miles: num(loteBrutoMiles),
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
      const par = buildPar();
      const res =
        isEdit && projectId && slug
          ? await editarYAprobarProyecto({ projectId, slug, par })
          : await crearYAprobarProyecto({ par, nombre: meta.nombre.trim() });
      if (res.ok) {
        if (!res.checks_ok) {
          // se guardó, pero algún cuadre del motor no cierra: avisa antes de navegar.
          setWarn(
            isEdit
              ? "Cambios guardados, pero algún cuadre del motor no cierra. Revísalo en la ficha."
              : "Proyecto creado, pero algún cuadre del motor no cierra. Revísalo en la ficha.",
          );
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

      {/* Nota de defaults / preservación */}
      <p className="text-xs text-muted-foreground">
        {isEdit ? (
          <>
            El costo de capital (WACC build-up), los supuestos financieros y el cronograma del proyecto se{" "}
            <strong className="font-medium text-foreground">conservan</strong> al guardar (no se editan aquí).
            Guardar crea una <strong className="font-medium text-foreground">versión nueva</strong> y la
            aprueba; la anterior queda en el historial.
          </>
        ) : (
          <>
            El costo de capital (WACC build-up), los supuestos financieros (crédito, fiducia, separación) y el
            cronograma usan el <strong className="font-medium text-foreground">estándar CG</strong>. Serán
            editables por proyecto en una fase posterior.
          </>
        )}
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
          onClick={() => router.push(isEdit && slug ? `/proyectos/${slug}` : "/")}
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
          {pending
            ? isEdit
              ? "Guardando…"
              : "Creando…"
            : isEdit
              ? "Guardar cambios y re-aprobar"
              : "Crear y aprobar proyecto"}
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
      {hint ? <span className="mt-0.5 block text-[0.7rem] text-muted-foreground">{hint}</span> : null}
    </label>
  );
}
