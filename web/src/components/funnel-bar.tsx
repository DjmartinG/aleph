import type { FunnelStage } from "@/lib/api";
import { fmtInt } from "@/lib/format";
import { cn } from "@/lib/utils";

/** Color del segmento y del punto por fase (familia del PhaseBadge). */
const SEG: Record<string, string> = {
  prefactibilidad: "bg-slate-300 dark:bg-slate-600",
  aprobado: "bg-amber-400 dark:bg-amber-500",
  construccion: "bg-teal-500 dark:bg-teal-400",
  entregado: "bg-emerald-500 dark:bg-emerald-400",
};
const DOT: Record<string, string> = {
  prefactibilidad: "bg-slate-400 dark:bg-slate-500",
  aprobado: "bg-amber-500",
  construccion: "bg-teal-500 dark:bg-teal-400",
  entregado: "bg-emerald-500 dark:bg-emerald-400",
};

/** Embudo por fase: barra segmentada proporcional + leyenda con conteos. */
export function FunnelBar({ stages }: { stages: FunnelStage[] }) {
  const total = stages.reduce((a, s) => a + s.count, 0);
  return (
    <div className="rounded-xl border bg-card p-4">
      <div className="flex h-2.5 w-full overflow-hidden rounded-full bg-muted">
        {total > 0
          ? stages
              .filter((s) => s.count > 0)
              .map((s) => (
                <div
                  key={s.estado}
                  className={cn("h-full transition-[width] duration-200", SEG[s.estado] ?? "bg-muted-foreground")}
                  style={{ width: `${(s.count / total) * 100}%` }}
                  title={`${s.label}: ${s.count}`}
                />
              ))
          : null}
      </div>
      <div className="mt-3.5 flex flex-wrap gap-x-5 gap-y-2">
        {stages.map((s) => (
          <div key={s.estado} className="flex items-center gap-2">
            <span
              className={cn(
                "size-2 rounded-full",
                DOT[s.estado] ?? "bg-muted-foreground",
                s.count === 0 && "opacity-40",
              )}
              aria-hidden
            />
            <span className={cn("text-sm", s.count === 0 ? "text-muted-foreground" : "text-foreground")}>
              {s.label}
            </span>
            <span className="text-sm font-semibold tabular-nums">{fmtInt(s.count)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
