import { cn } from "@/lib/utils";

/** Etiqueta + color por estado del ciclo de vida (constitución §ciclo de vida). */
const FASE: Record<string, { label: string; cls: string }> = {
  prefactibilidad: {
    label: "Pre-factibilidad",
    cls: "bg-slate-100 text-slate-700 dark:bg-slate-800/70 dark:text-slate-300",
  },
  aprobado: {
    label: "Aprobado",
    cls: "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300",
  },
  construccion: {
    label: "Construcción",
    cls: "bg-teal-100 text-teal-800 dark:bg-teal-950/60 dark:text-teal-300",
  },
  entregado: {
    label: "Entregado",
    cls: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300",
  },
};

export function PhaseBadge({
  estado,
  label,
  className,
}: {
  estado: string;
  label?: string;
  className?: string;
}) {
  const f = FASE[estado] ?? { label: label ?? estado, cls: "bg-muted text-muted-foreground" };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium whitespace-nowrap",
        f.cls,
        className,
      )}
    >
      <span className="size-1.5 rounded-full bg-current opacity-80" aria-hidden />
      {label ?? f.label}
    </span>
  );
}
