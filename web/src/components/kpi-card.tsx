import { cn } from "@/lib/utils";

type State = "neutral" | "positive" | "negative";

/**
 * Tarjeta KPI canónica (constitución §componentes): valor + ETIQUETA DE BASE + sub/delta + estado.
 * Ninguna cifra sin etiqueta de base.
 */
export function KpiCard({
  label,
  value,
  base,
  sub,
  state = "neutral",
  className,
}: {
  label: string;
  value: string;
  base?: string;
  sub?: string;
  state?: State;
  className?: string;
}) {
  const valueColor =
    state === "positive"
      ? "text-success"
      : state === "negative"
        ? "text-danger"
        : "text-foreground";
  return (
    <div className={cn("rounded-xl border bg-card p-4 shadow-sm", className)}>
      <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </div>
      <div className={cn("mt-2 text-2xl font-semibold tabular-nums", valueColor)}>
        {value}
      </div>
      {base ? (
        <div className="mt-1 text-[0.7rem] font-medium uppercase tracking-wide text-muted-foreground">
          {base}
        </div>
      ) : null}
      {sub ? (
        <div className="mt-0.5 text-xs tabular-nums text-muted-foreground">{sub}</div>
      ) : null}
    </div>
  );
}
