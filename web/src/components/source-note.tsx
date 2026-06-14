import { cn } from "@/lib/utils";

/** Nota de PROCEDENCIA del dato (gobernanza de cifras: cada número con su origen y corte).
 *  Se coloca al pie de la sección/pantalla donde se usa el dato. */
export function SourceNote({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <p className={cn("mt-3 text-[0.72rem] leading-relaxed text-muted-foreground", className)}>
      <span className="font-medium text-foreground/70">Fuente:</span> {children}
    </p>
  );
}
