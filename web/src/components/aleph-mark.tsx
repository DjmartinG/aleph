import { cn } from "@/lib/utils";

/**
 * Marca ALEPH: anillo de precisión teal (borde + punto central). Único motivo de marca y el ÚNICO
 * marcador teal de jerarquía (wordmark, favicon, celda héroe, fila activa). El álef como un punto.
 */
export function AlephMark({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "relative inline-flex size-3.5 shrink-0 items-center justify-center rounded-full border-[1.5px] border-primary",
        className,
      )}
      aria-hidden
    >
      <span className="size-[3px] rounded-full bg-primary" />
    </span>
  );
}
