"use client";

import type { Vehiculos } from "@/lib/api";
import { fmtCop, fmtPct } from "@/lib/format";
import { Banner } from "@/components/banner";

/** M3 — Comparador de vehículos jurídico-financieros. Efecto fiscal + waterfall after-tax por
 *  estructura, en base consistente. La TIR auditada de la fiducia se muestra aparte como oficial. */
export function VehiculosView({ data }: { data: Vehiculos }) {
  const filas = data.vehiculos;
  const of = data.oficial_fiducia;

  return (
    <div className="space-y-7">
      {/* Advertencia: tasas por validar */}
      <Banner tone="warning" label="Por validar">{data.advertencia}</Banner>

      {/* Cifra OFICIAL de la estructura real (fiducia auditada) */}
      <div className="grid grid-cols-2 gap-x-6 gap-y-4 rounded-[var(--radius-data)] border bg-card p-5 sm:grid-cols-3">
        <div>
          <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            TIR proyecto · oficial
          </div>
          <div className="mt-1 num text-3xl font-semibold tracking-tight">
            {fmtPct(of.tir_proyecto_auditada)}
          </div>
          <div className="text-[0.7rem] text-muted-foreground">fiducia · {of.fuente}</div>
        </div>
        <div>
          <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            TIR socio · oficial
          </div>
          <div className="mt-1 num text-3xl font-semibold tracking-tight">
            {fmtPct(of.tir_socio_auditada)}
          </div>
          <div className="text-[0.7rem] text-muted-foreground">estructura real (fiducia)</div>
        </div>
        <div className="text-sm text-muted-foreground">
          Esta es la cifra de decisión de la estructura actual. La tabla de abajo compara estructuras
          alternativas en base <span className="font-medium text-foreground/80">mensual after-tax</span>{" "}
          (consistente entre vehículos, más conservadora que la anual auditada).
        </div>
      </div>

      {/* Tabla A vs B */}
      <section>
        <h3 className="mb-2 text-sm font-semibold">Comparación de estructuras</h3>
        <div className="overflow-x-auto rounded-[var(--radius-data)] border bg-card">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-xs uppercase tracking-wide text-muted-foreground">
                <th className="px-4 py-2.5 text-left font-medium">Vehículo</th>
                <th className="px-4 py-2.5 text-left font-medium">Tratamiento</th>
                <th className="px-4 py-2.5 text-right font-medium">UDI after-tax</th>
                <th className="px-4 py-2.5 text-right font-medium">Carga tributaria</th>
                <th className="px-4 py-2.5 text-right font-medium">Δ vs fiducia</th>
              </tr>
            </thead>
            <tbody>
              {filas.map((f) => (
                <tr
                  key={f.vehiculo}
                  className={
                    "border-b last:border-0 " +
                    (f.es_referencia ? "bg-primary/5" : "")
                  }
                >
                  <td className="px-4 py-2.5">
                    <div className="font-medium">{f.nombre_vehiculo}</div>
                    <div className="text-[0.7rem] text-muted-foreground">
                      {f.transparente ? "transparente" : "opaco (doble imposición)"}
                      {f.es_referencia ? " · referencia" : ""}
                    </div>
                  </td>
                  <td className="px-4 py-2.5 text-muted-foreground">
                    {f.exencion_vis_aplicada ? (
                      <span className="rounded bg-primary/10 px-1.5 py-0.5 text-[0.7rem] font-medium text-primary">
                        VIS exenta
                      </span>
                    ) : (
                      <span className="text-[0.78rem]">{f.etiqueta}</span>
                    )}
                  </td>
                  <td className="num px-4 py-2.5 text-right">{fmtCop(f.udi)}</td>
                  <td className="num px-4 py-2.5 text-right">{fmtCop(f.carga_tributaria)}</td>
                  <td
                    className={
                      "num px-4 py-2.5 text-right " +
                      (f.delta_carga_vs_fiducia > 0 ? "text-[var(--negative,#b4413c)]" : "text-muted-foreground")
                    }
                  >
                    {f.es_referencia ? "—" : `+${fmtCop(f.delta_carga_vs_fiducia)}`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-[0.72rem] leading-relaxed text-muted-foreground">{data.nota}</p>
      </section>
    </div>
  );
}
