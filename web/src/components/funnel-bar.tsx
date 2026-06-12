import type { FunnelStage } from "@/lib/api";
import { fmtInt } from "@/lib/format";
import { cn } from "@/lib/utils";

/** Color del segmento (barra) y del swatch (leyenda) por fase. */
const SEG: Record<string, string> = {
  prefactibilidad: "bg-slate-300 dark:bg-slate-600",
  aprobado: "bg-amber-400 dark:bg-amber-500",
  construccion: "bg-teal-500 dark:bg-teal-400",
  entregado: "bg-emerald-500 dark:bg-emerald-400",
};

/** Embudo por fase: barras DISCRETAS proporcionales (instrumento, no progress-bar) + leyenda. */
export function FunnelBar({ stages }: { stages: FunnelStage[] }) {
  const total = stages.reduce((a, s) => a + s.count, 0);
  const active = stages.filter((s) => s.count > 0);
  return (
    <div>
      <div className="flex h-6 w-full items-stretch gap-1">
        {total > 0 ? (
          active.map((s, i) => (
            <div
              key={s.estado}
              className={cn(
                "transition-[flex-basis] duration-[240ms] [transition-timing-function:var(--ease-out)]",
                SEG[s.estado] ?? "bg-muted-foreground",
                i === 0 && "rounded-l-[3px]",
                i === active.length - 1 && "rounded-r-[3px]",
              )}
              style={{ flexBasis: `${(s.count / total) * 100}%` }}
              aria-label={`${s.label}: ${s.count}`}
            />
          ))
        ) : (
          <div className="h-full w-full rounded-[3px] bg-muted" />
        )}
      </div>
      <div className="mt-2 border-t border-rule" />
      <div className="mt-3 flex flex-wrap gap-x-6 gap-y-2">
        {stages.map((s) => (
          <div key={s.estado} className="flex items-center gap-2">
            <span
              className={cn(
                "size-2 rounded-[2px]",
                SEG[s.estado] ?? "bg-muted-foreground",
                s.count === 0 && "opacity-35",
              )}
              aria-hidden
            />
            <span className={cn("text-sm", s.count === 0 ? "text-muted-foreground" : "text-foreground")}>
              {s.label}
            </span>
            <span className="num text-sm font-semibold text-muted-foreground">{fmtInt(s.count)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
