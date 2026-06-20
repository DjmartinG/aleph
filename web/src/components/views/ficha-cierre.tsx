import type { Cierre, CierreLinea } from "@/lib/api";
import { fmtCop } from "@/lib/format";
import { ChecksBadge } from "@/components/checks-badge";
import { cn } from "@/lib/utils";

/** Cierre financiero — Fuentes y Usos (curso Camacol §M6). Solo presenta cifras del motor. */
export function CierreView({ cierre }: { cierre: Cierre }) {
  const fin = cierre.financiacion;
  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3">
        <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Cierre financiero · Fuentes y Usos
        </div>
        <ChecksBadge nombre={cierre.cuadre.ok ? "Cuadra" : "Revisar cuadre"} ok={cierre.cuadre.ok} />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Tabla titulo="Usos (inversión + financiación)" lineas={cierre.usos} total={cierre.usos_total} totalLabel="Total usos" />
        <Tabla titulo="Fuentes (ingresos)" lineas={cierre.fuentes} total={cierre.fuentes_total} totalLabel="Total fuentes" />
      </div>

      <div>
        <div className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Resultado y financiación del desfase
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          <Stat label="Utilidad operativa" value={fmtCop(cierre.utilidad_operativa)} note="ventas − inversión" accent />
          <Stat label="Equity pico" value={fmtMaybe(fin.equity_pico)} note="necesidad máx. de caja propia" />
          <Stat label="Crédito máximo" value={fmtMaybe(fin.credito_max)} note="pico del crédito constructor" />
          <Stat label="Exposición máxima" value={fmtMaybe(fin.exposicion_maxima)} note="valle del acumulado" />
          <Stat label="Intereses" value={fmtCop(fin.intereses)} note="costo de la deuda" />
        </div>
      </div>

      <p className="text-[0.7rem] text-muted-foreground">
        Fuentes y Usos del proyecto (curso Camacol · evaluación financiera). El cierre cuadra cuando los
        ingresos igualan la inversión (usos) más la utilidad operativa. Los <strong>intereses</strong> del
        crédito son el costo de la financiación del desfase temporal: <strong>no</strong> se restan a la
        utilidad operativa (afectan el retorno del inversionista por el momento de los flujos, reflejado en
        la TIR del socio).
      </p>
    </div>
  );
}

function fmtMaybe(v: number | null): string {
  return v == null ? "—" : fmtCop(v);
}

function Tabla({
  titulo,
  lineas,
  total,
  totalLabel,
}: {
  titulo: string;
  lineas: CierreLinea[];
  total: number;
  totalLabel: string;
}) {
  return (
    <div className="rounded-[var(--radius-data)] border bg-card p-4">
      <div className="mb-3 text-sm font-medium text-foreground">{titulo}</div>
      <div className="space-y-1.5">
        {lineas.map((l) => (
          <div key={l.concepto} className="flex items-baseline justify-between gap-3 text-sm">
            <span className="text-muted-foreground">{l.concepto}</span>
            <span className="num tabular-nums">{fmtCop(l.valor)}</span>
          </div>
        ))}
      </div>
      <div className="mt-3 flex items-baseline justify-between gap-3 border-t border-rule pt-2 text-sm font-semibold">
        <span>{totalLabel}</span>
        <span className="num tabular-nums">{fmtCop(total)}</span>
      </div>
    </div>
  );
}

function Stat({
  label,
  value,
  note,
  accent,
}: {
  label: string;
  value: string;
  note?: string;
  accent?: boolean;
}) {
  return (
    <div className={cn("rounded-[var(--radius-data)] border bg-card px-3 py-2.5", accent && "border-l-2 border-l-primary/40")}>
      <div className="text-[0.7rem] font-medium uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="num mt-0.5 text-base font-semibold tabular-nums">{value}</div>
      {note ? <div className="text-[0.7rem] text-muted-foreground">{note}</div> : null}
    </div>
  );
}
