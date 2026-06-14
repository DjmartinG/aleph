import { cn } from "@/lib/utils";

/** Mini-métrica canon (M7): label + valor + nota. `size="md"` para KPIs destacados (p. ej. WACC).
 *  Unifica las 4 copias locales `Mini` que vivían en cada vista. */
export function MiniStat({
  label,
  value,
  note,
  danger,
  size = "sm",
}: {
  label: string;
  value: string;
  note?: string;
  danger?: boolean;
  size?: "sm" | "md";
}) {
  return (
    <div>
      <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</div>
      <div
        className={cn(
          "num font-semibold",
          size === "md" ? "mt-1 text-xl tracking-tight" : "mt-0.5 text-base",
          danger && "text-danger",
        )}
      >
        {value}
      </div>
      {note ? <div className="text-[0.7rem] text-muted-foreground">{note}</div> : null}
    </div>
  );
}
