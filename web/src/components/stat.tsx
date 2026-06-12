import { cn } from "@/lib/utils";

export type StatState = "neutral" | "positive" | "negative";

export interface StatItem {
  label: string;
  value: string;
  /** Etiqueta de base (constitución: ninguna cifra sin etiqueta de base). */
  base?: string;
  sub?: string;
  state?: StatState;
}

/** Métrica atómica: valor + etiqueta de base + sub + estado. */
export function Stat({ label, value, base, sub, state = "neutral" }: StatItem) {
  const color =
    state === "positive"
      ? "text-success"
      : state === "negative"
        ? "text-danger"
        : "text-foreground";
  return (
    <div>
      <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </div>
      <div className={cn("mt-1.5 text-xl font-semibold tabular-nums", color)}>{value}</div>
      {base ? (
        <div className="mt-1 text-[0.7rem] font-medium uppercase tracking-wide text-muted-foreground/70">
          {base}
        </div>
      ) : null}
      {sub ? <div className="mt-0.5 text-xs tabular-nums text-muted-foreground">{sub}</div> : null}
    </div>
  );
}

/**
 * Panel de métricas: UN panel dividido por separadores de 1px (no un grid de tarjetas idénticas).
 * Técnica: contenedor con `bg-border` + `gap-px`, celdas `bg-card` → hairlines limpias.
 */
export function StatPanel({ items }: { items: StatItem[] }) {
  return (
    <div className="overflow-hidden rounded-xl border bg-border">
      <div className="grid grid-cols-2 gap-px sm:grid-cols-3 xl:grid-cols-6">
        {items.map((s) => (
          <div key={s.label} className="bg-card p-4">
            <Stat {...s} />
          </div>
        ))}
      </div>
    </div>
  );
}
