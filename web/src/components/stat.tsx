import { cn } from "@/lib/utils";
import { Figure } from "@/components/figure";

export type StatState = "neutral" | "positive" | "negative";

export interface StatItem {
  label: string;
  /** [magnitud, unidad] — p. ej. ["$229.7", "mil M"] o ["37.60", "%"]. */
  parts: [string, string];
  /** Etiqueta de base (constitución: ninguna cifra sin etiqueta de base). */
  base?: string;
  sub?: string;
  state?: StatState;
  /** Métrica-héroe: cifra mayor, acento teal, ocupa 2 columnas en xl. */
  emphasis?: boolean;
}

/** Métrica atómica: valor + etiqueta de base + sub + estado. */
export function Stat({ label, parts, base, sub, state = "neutral", emphasis = false }: StatItem) {
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
      <Figure
        parts={parts}
        display={emphasis}
        className={cn("mt-1.5 block font-semibold", emphasis ? "text-[1.9rem] leading-none" : "text-lg", color)}
      />
      {base ? <div className="mt-1.5 text-[0.72rem] text-muted-foreground">{base}</div> : null}
      {sub ? <div className="num mt-0.5 text-xs text-muted-foreground">{sub}</div> : null}
    </div>
  );
}

/**
 * Panel de métricas: UN panel dividido por reglas de 1px tintadas al teal (no un grid de tarjetas
 * idénticas). La métrica-héroe lleva acento teal (barra izquierda + piso tenue) y ocupa 2 col en xl.
 */
const GRID: Record<number, string> = {
  3: "grid-cols-3",
  4: "grid-cols-2 xl:grid-cols-4",
  5: "grid-cols-2 sm:grid-cols-3 xl:grid-cols-5",
  6: "grid-cols-2 sm:grid-cols-3 xl:grid-cols-6",
};

export function StatPanel({ items }: { items: StatItem[] }) {
  const grid = GRID[items.length] ?? "grid-cols-2 sm:grid-cols-3 xl:grid-cols-6";
  return (
    <div className="shadow-card overflow-hidden rounded-[var(--radius-data)] border bg-rule">
      <div className={cn("grid gap-px", grid)}>
        {items.map((s) => (
          <div
            key={s.label}
            className={cn(
              "relative bg-card p-4",
              s.emphasis && "bg-primary/[0.045] pl-5",
            )}
          >
            {s.emphasis ? (
              <span className="absolute inset-y-3 left-0 w-0.5 rounded-full bg-primary" aria-hidden />
            ) : null}
            <Stat {...s} />
          </div>
        ))}
      </div>
    </div>
  );
}
