"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2, AlertTriangle } from "lucide-react";
import type { Tipologia } from "@/lib/api";
import { editarTipologiasYAprobar, type CrearProyectoResult } from "@/lib/actions";
import { fmtCop } from "@/lib/format";
import { cn } from "@/lib/utils";

const CLASES = ["apartamento", "comercio", "parqueadero", "deposito"];
const METODOS = ["$/und", "$/m²"];
const HOUSING = new Set(["apartamento", "comercio"]);

type Row = { etapa: number; nombre: string; clase: string; metodo: string; und: string; precio: string; area_und: string };

function toRow(t: Tipologia): Row {
  return {
    etapa: Number(t.etapa),
    nombre: t.nombre ?? "",
    clase: t.clase ?? "apartamento",
    metodo: t.metodo ?? "$/und",
    und: String(t.und ?? ""),
    precio: String(t.precio ?? ""),
    area_und: t.area_und != null ? String(t.area_und) : "",
  };
}

/** Ventas (miles COP) de una fila — ESPEJO de `_ventas_tipologia` del motor (solo orientativo; la
 *  cifra oficial la calcula el motor). En VIS, parqueadero/depósito = 0 (comunales). */
function previewVentas(r: Row, esVis: boolean): number | null {
  const und = Number(r.und);
  const precio = Number(r.precio);
  if (!und || !precio) return null;
  if (esVis && !HOUSING.has(r.clase)) return 0;
  if (r.metodo === "$/m²") {
    const area = Number(r.area_und);
    if (!area) return null;
    return (und * precio * area) / 1000;
  }
  return (und * precio) / 1000;
}

export function TipologiasForm({
  slug,
  cods,
  esVis,
  tipologias,
}: {
  slug: string;
  cods: number[];
  esVis: boolean;
  tipologias: Tipologia[];
}) {
  const router = useRouter();
  const [pending, start] = useTransition();
  const [result, setResult] = useState<CrearProyectoResult | null>(null);
  const [rows, setRows] = useState<Row[]>(() => tipologias.map(toRow));

  function setRow(i: number, patch: Partial<Row>) {
    setRows((prev) => prev.map((r, j) => (j === i ? { ...r, ...patch } : r)));
  }

  function submit() {
    setResult(null);
    const out: Record<string, unknown>[] = rows.map((r) => ({
      etapa: Number(r.etapa),
      nombre: r.nombre.trim() || undefined,
      clase: r.clase,
      metodo: r.metodo,
      und: Math.round(Number(r.und) || 0),
      precio: Number(r.precio) || 0,
      ...(r.metodo === "$/m²" ? { area_und: Number(r.area_und) || 0 } : {}),
    }));
    start(async () => {
      const res = await editarTipologiasYAprobar({ slug, tipologias: out });
      setResult(res);
      if (res.ok) router.push(`/proyectos/${slug}`);
    });
  }

  return (
    <div className="space-y-5">
      <div className="overflow-x-auto rounded-[var(--radius-data)] border bg-card">
        <table className="w-full min-w-[760px] text-sm">
          <thead>
            <tr className="border-b border-rule text-left text-[0.7rem] uppercase tracking-wide text-muted-foreground">
              <th className="px-3 py-2 font-medium">Etapa</th>
              <th className="px-3 py-2 font-medium">Nombre</th>
              <th className="px-3 py-2 font-medium">Clase</th>
              <th className="px-3 py-2 font-medium">Método</th>
              <th className="px-3 py-2 text-right font-medium">Unidades</th>
              <th className="px-3 py-2 text-right font-medium">Precio (COP)</th>
              <th className="px-3 py-2 text-right font-medium">Área/und</th>
              <th className="px-3 py-2 text-right font-medium">Ventas (prev.)</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => {
              const prev = previewVentas(r, esVis);
              const comunal = esVis && !HOUSING.has(r.clase);
              return (
                <tr key={i} className="border-b border-rule last:border-0">
                  <td className="px-3 py-2">
                    <select value={r.etapa} onChange={(e) => setRow(i, { etapa: Number(e.target.value) })}
                      className="rounded-[var(--radius-data)] border bg-background px-2 py-1">
                      {cods.map((c) => <option key={c} value={c}>{c}</option>)}
                    </select>
                  </td>
                  <td className="px-3 py-2">
                    <input type="text" value={r.nombre} onChange={(e) => setRow(i, { nombre: e.target.value })}
                      className="w-32 rounded-[var(--radius-data)] border bg-background px-2 py-1" />
                  </td>
                  <td className="px-3 py-2">
                    <select value={r.clase} onChange={(e) => setRow(i, { clase: e.target.value })}
                      className="rounded-[var(--radius-data)] border bg-background px-2 py-1 capitalize">
                      {CLASES.map((c) => <option key={c} value={c}>{c}</option>)}
                    </select>
                  </td>
                  <td className="px-3 py-2">
                    <select value={r.metodo} onChange={(e) => setRow(i, { metodo: e.target.value })}
                      className="rounded-[var(--radius-data)] border bg-background px-2 py-1">
                      {METODOS.map((m) => <option key={m} value={m}>{m}</option>)}
                    </select>
                  </td>
                  <td className="px-3 py-2 text-right">
                    <input type="number" value={r.und} onChange={(e) => setRow(i, { und: e.target.value })}
                      className="num w-20 rounded-[var(--radius-data)] border bg-background px-2 py-1 text-right tabular-nums" />
                  </td>
                  <td className="px-3 py-2 text-right">
                    <input type="number" step="1000000" value={r.precio} onChange={(e) => setRow(i, { precio: e.target.value })}
                      className="num w-32 rounded-[var(--radius-data)] border bg-background px-2 py-1 text-right tabular-nums" />
                  </td>
                  <td className="px-3 py-2 text-right">
                    <input type="number" value={r.area_und} disabled={r.metodo !== "$/m²"}
                      onChange={(e) => setRow(i, { area_und: e.target.value })}
                      className="num w-20 rounded-[var(--radius-data)] border bg-background px-2 py-1 text-right tabular-nums disabled:opacity-40" />
                  </td>
                  <td className="num px-3 py-2 text-right tabular-nums text-muted-foreground">
                    {prev == null ? "—" : fmtCop(prev)}
                    {comunal ? <span className="ml-1 text-[0.65rem] text-amber-700 dark:text-amber-300">comunal</span> : null}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <p className="text-[0.7rem] text-muted-foreground">
        El <strong>precio va en PESOS COP</strong> (p. ej. 250.000.000), no en miles. La columna “Ventas
        (prev.)” es orientativa: <strong>la cifra oficial la calcula el motor</strong> al guardar.
        {esVis ? " En VIS/VIP los parqueaderos y depósitos son comunales (no generan ingreso)." : ""}
      </p>

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
        <button type="button" onClick={submit} disabled={pending}
          className={cn(
            "inline-flex items-center gap-1.5 rounded-[var(--radius-data)] bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-[transform,opacity] [transition-timing-function:var(--ease-out)] active:scale-[0.98]",
            pending && "opacity-60",
          )}>
          {pending ? "Guardando…" : "Guardar tipologías y re-aprobar"}
        </button>
        <span className="text-[0.7rem] text-muted-foreground">
          Crea una versión nueva; el motor re-deriva unidades y ventas de la tabla.
        </span>
      </div>
    </div>
  );
}
