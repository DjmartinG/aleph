import { Check, X } from "lucide-react";
import { cn } from "@/lib/utils";

/** Estado de un check de cuadre (constitución: P&G suma, recaudo=ventas, flujo≈utilidad, etc.). */
export function ChecksBadge({
  nombre,
  ok,
  className,
}: {
  nombre: string;
  ok: boolean;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium",
        ok ? "bg-success/10 text-success" : "bg-danger/10 text-danger",
        className,
      )}
    >
      {ok ? <Check className="size-3.5" aria-hidden /> : <X className="size-3.5" aria-hidden />}
      {nombre}
    </span>
  );
}
