import { cn } from "@/lib/utils";

/** Título de sección con tick teal (motivo de marca). */
export function SectionTitle({
  children,
  className,
  right,
  subtitle,
}: {
  children: React.ReactNode;
  className?: string;
  right?: React.ReactNode;
  subtitle?: React.ReactNode;
}) {
  return (
    <div className={cn("mb-3", className)}>
      <div className="flex items-center gap-2">
        <span className="h-3.5 w-0.5 rounded-full bg-primary" aria-hidden />
        <h2 className="text-sm font-medium">{children}</h2>
        {right ? <div className="num ml-auto text-xs text-muted-foreground">{right}</div> : null}
      </div>
      {subtitle ? <p className="mt-1 pl-2.5 text-xs text-muted-foreground">{subtitle}</p> : null}
    </div>
  );
}
