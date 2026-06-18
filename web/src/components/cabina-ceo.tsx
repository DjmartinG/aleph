import { AlertOctagon, TriangleAlert, Sparkles, type LucideIcon } from "lucide-react";
import { fmtCop } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Alerta, Salud } from "@/lib/api";

/**
 * Cabina del CEO: las ALERTAS accionables del portafolio, priorizadas (crítico → alerta → nota). El
 * motor manda las alertas ESTRUCTURADAS (nivel + tipo + datos); aquí se arma el texto en español. Sin
 * side-stripe borders (prohibido): el nivel se marca con icono de color + un tinte de fondo sutil.
 */
export function CabinaCeo({ data }: { data: Salud }) {
  if (!data.alertas.length) {
    return (
      <div className="rounded-[var(--radius-data)] border bg-card p-4 text-sm text-muted-foreground">
        Sin alertas: el portafolio está en orden.
      </div>
    );
  }
  const { critico, alerta, info } = data.resumen;
  return (
    <div className="rounded-[var(--radius-data)] border bg-card p-4">
      <div className="mb-3 flex flex-wrap items-center gap-2 text-xs">
        {critico > 0 ? <Chip tone="critico">{critico} crítica{critico > 1 ? "s" : ""}</Chip> : null}
        {alerta > 0 ? <Chip tone="alerta">{alerta} alerta{alerta > 1 ? "s" : ""}</Chip> : null}
        {info > 0 ? <Chip tone="info">{info} nota{info > 1 ? "s" : ""}</Chip> : null}
      </div>
      <ul className="space-y-1.5">
        {data.alertas.map((a, i) => (
          <AlertaRow key={`${a.tipo}-${i}`} alerta={a} />
        ))}
      </ul>
    </div>
  );
}

const ICONO: Record<Alerta["nivel"], LucideIcon> = {
  critico: AlertOctagon,
  alerta: TriangleAlert,
  info: Sparkles,
};

function AlertaRow({ alerta }: { alerta: Alerta }) {
  const Icon = ICONO[alerta.nivel];
  const { titulo, detalle } = contenido(alerta);
  return (
    <li
      className={cn(
        "flex items-start gap-3 rounded-md px-3 py-2.5 transition-colors",
        alerta.nivel === "critico" && "bg-danger/[0.06]",
        alerta.nivel === "alerta" && "bg-[var(--cg-amber)]/[0.06]",
      )}
    >
      <Icon
        className={cn(
          "mt-0.5 size-4 shrink-0",
          alerta.nivel === "critico" && "text-danger",
          alerta.nivel === "alerta" && "text-[var(--cg-amber)]",
          alerta.nivel === "info" && "text-primary",
        )}
        aria-hidden
      />
      <div className="min-w-0">
        <p className="text-sm font-medium leading-snug">{titulo}</p>
        {detalle ? <p className="num mt-0.5 text-xs tabular-nums text-muted-foreground">{detalle}</p> : null}
      </div>
    </li>
  );
}

function Chip({ tone, children }: { tone: Alerta["nivel"]; children: React.ReactNode }) {
  return (
    <span
      className={cn(
        "num inline-flex items-center rounded-full border px-2 py-0.5 font-medium tabular-nums",
        tone === "critico" && "border-danger/30 bg-danger/10 text-danger",
        tone === "alerta" && "border-[var(--cg-amber)]/30 bg-[var(--cg-amber)]/10 text-[var(--cg-amber)]",
        tone === "info" && "border-rule text-muted-foreground",
      )}
    >
      {children}
    </span>
  );
}

function pct(x: number): string {
  return `${(x * 100).toFixed(0)}%`;
}

/** Mapea el tipo de alerta (enum del motor) + sus datos → texto en español. */
function contenido(a: Alerta): { titulo: string; detalle: string } {
  const d = a.datos;
  switch (a.tipo) {
    case "destruye_valor": {
      const n = Number(d.n);
      return {
        titulo: `${n} ${n === 1 ? "proyecto destruye" : "proyectos destruyen"} valor sobre el WACC`,
        detalle: (d.proyectos as string[]).join(", "),
      };
    }
    case "concentracion":
      return {
        titulo: `El ${pct(Number(d.share))} de las ventas se concentra en ${d.categoria}`,
        detalle: `${d.dimension}: ${Number(d.n_efectivo).toFixed(1)} categorías efectivas de ${d.n_categorias}`,
      };
    case "resiliencia":
      return {
        titulo: "Bajo una recesión severa, la caja consolidada quedaría en déficit",
        detalle: `≈ ${fmtCop(Number(d.caja_cierre))} al cierre · valle ${fmtCop(Number(d.valle))}`,
      };
    case "greenfield": {
      const n = Number(d.n);
      return {
        titulo: `${n} ${n === 1 ? "proyecto" : "proyectos"} sin veredicto de valor (greenfield)`,
        detalle: (d.proyectos as string[]).join(", "),
      };
    }
    case "mejor_capital":
      return {
        titulo: `El capital rinde más en ${d.proyecto}`,
        detalle: `eficiencia ${Number(d.eficiencia).toFixed(2)} — valor creado por peso de equity`,
      };
    default:
      return { titulo: a.tipo, detalle: "" };
  }
}
