import { cn } from "@/lib/utils";

/**
 * Cifra estilo "ledger": magnitud prominente + unidad (mil M / M / %) en muted y más chica.
 * Tipografía financiera real: el sufijo recede, la magnitud manda. `parts` = [magnitud, unidad].
 */
export function Figure({
  parts,
  className,
  display = false,
}: {
  parts: [string, string];
  className?: string;
  display?: boolean;
}) {
  const [main, unit] = parts;
  return (
    <span className={cn(display ? "num-display" : "num", className)}>
      {main}
      {unit ? (
        <span className="ml-[0.15em] text-[0.62em] font-medium text-muted-foreground">{unit}</span>
      ) : null}
    </span>
  );
}
