import { Check, AlertTriangle, Circle, ShieldCheck, ShieldAlert, ShieldX } from "lucide-react";
import type { DueDiligence, DueDiligenceItem } from "@/lib/api";
import { cn } from "@/lib/utils";

/** Viabilidad cualitativa — due diligence + registro de riesgos (curso Camacol M4/M5 · B1).
 *  Solo presenta lo que el motor agrega; la captura de estados se hace en el Ingreso de datos. */
export function ViabilidadView({ dd }: { dd: DueDiligence }) {
  const v = dd.veredicto;
  return (
    <div className="space-y-5">
      <VeredictoBanner nivel={v.nivel} n_items={v.n_items} n_ok={v.n_ok} n_alertas={v.n_alertas} n_pendientes={v.n_pendientes} />

      <div className="grid gap-4 md:grid-cols-2">
        {dd.frentes.map((f) => {
          const items = dd.items.filter((i) => i.frente === f.clave);
          if (items.length === 0) return null;
          return (
            <div key={f.clave} className="rounded-[var(--radius-data)] border bg-card p-4">
              <div className="mb-3 text-sm font-medium text-foreground">{f.nombre}</div>
              <div className="space-y-2.5">
                {items.map((it) => (
                  <ItemRow key={`${it.frente}-${it.item}`} it={it} />
                ))}
              </div>
            </div>
          );
        })}
      </div>

      <p className="text-[0.7rem] text-muted-foreground">
        Due diligence del prefacto (curso Camacol · legal, ambiental/ESG, urbanístico, técnico y bancario).
        El veredicto cualitativo <strong>acompaña</strong> al financiero: rojo = riesgo de impacto alto sin
        mitigar; ámbar = due diligence en proceso; verde = sin riesgos abiertos. La captura de estados se
        hace en el Ingreso de datos; los ítems sin diligenciar aparecen como <em>pendiente</em>.
      </p>
    </div>
  );
}

function VeredictoBanner({
  nivel,
  n_items,
  n_ok,
  n_alertas,
  n_pendientes,
}: {
  nivel: string;
  n_items: number;
  n_ok: number;
  n_alertas: number;
  n_pendientes: number;
}) {
  const map: Record<string, { txt: string; cls: string; Icon: typeof ShieldCheck }> = {
    verde: { txt: "Viabilidad cualitativa: sin riesgos abiertos", cls: "bg-success/10 text-success", Icon: ShieldCheck },
    ambar: {
      txt: "Viabilidad cualitativa: due diligence en proceso",
      cls: "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300",
      Icon: ShieldAlert,
    },
    rojo: { txt: "Viabilidad cualitativa: riesgo alto sin mitigar", cls: "bg-danger/10 text-danger", Icon: ShieldX },
  };
  const f = map[nivel] ?? map.ambar;
  const Icon = f.Icon;
  return (
    <div className={cn("flex flex-wrap items-center gap-x-4 gap-y-1 rounded-[var(--radius-data)] px-4 py-3", f.cls)}>
      <span className="inline-flex items-center gap-2 text-sm font-semibold">
        <Icon className="size-4" aria-hidden /> {f.txt}
      </span>
      <span className="num text-xs opacity-80">
        {n_items} ítems · {n_ok} ok · {n_alertas} alertas · {n_pendientes} pendientes
      </span>
    </div>
  );
}

function ItemRow({ it }: { it: DueDiligenceItem }) {
  return (
    <div className="flex items-start justify-between gap-3 text-sm">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <EstadoBadge estado={it.estado} />
          <span className="truncate">{it.item}</span>
        </div>
        {it.mitigacion || it.nota ? (
          <div className="mt-0.5 text-[0.7rem] text-muted-foreground">{it.mitigacion || it.nota}</div>
        ) : null}
      </div>
      <ImpactoChip impacto={it.impacto} />
    </div>
  );
}

function EstadoBadge({ estado }: { estado: string }) {
  const map: Record<string, { cls: string; Icon: typeof Check; label: string }> = {
    ok: { cls: "bg-success/10 text-success", Icon: Check, label: "OK" },
    alerta: { cls: "bg-danger/10 text-danger", Icon: AlertTriangle, label: "Alerta" },
    pendiente: { cls: "bg-muted text-muted-foreground", Icon: Circle, label: "Pendiente" },
  };
  const f = map[estado] ?? map.pendiente;
  const Icon = f.Icon;
  return (
    <span className={cn("inline-flex shrink-0 items-center gap-1 rounded-full px-2 py-0.5 text-[0.7rem] font-medium", f.cls)}>
      <Icon className="size-3" aria-hidden /> {f.label}
    </span>
  );
}

function ImpactoChip({ impacto }: { impacto: string }) {
  // impacto NO es un estado: chip neutro (alto en tono de marca ámbar, sin usar el rojo semántico).
  const cls =
    impacto === "alto"
      ? "text-amber-700 dark:text-amber-300"
      : impacto === "medio"
        ? "text-muted-foreground"
        : "text-muted-foreground/70";
  return <span className={cn("shrink-0 text-[0.7rem] tabular-nums", cls)}>impacto {impacto}</span>;
}
