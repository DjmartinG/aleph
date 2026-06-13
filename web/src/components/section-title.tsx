import { cn } from "@/lib/utils";

/** Título de sección con tick teal (motivo de marca). */
export function SectionTitle({
  children,
  className,
  right,
}: {
  children: React.ReactNode;
  className?: string;
  right?: React.ReactNode;
}) {
  return (
    <div className={cn("mb-3 flex items-center gap-2", className)}>
      <span className="h-3.5 w-0.5 rounded-full bg-primary" aria-hidden />
      <h2 className="text-sm font-medium">{children}</h2>
      {right ? <div className="num ml-auto text-xs text-muted-foreground">{right}</div> : null}
    </div>
  );
}
