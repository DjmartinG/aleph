import { cn } from "@/lib/utils";

type Tone = "warning" | "info" | "danger";

const TONE: Record<Tone, { wrap: string; label: string }> = {
  warning: { wrap: "border-[var(--cg-amber)]/40 bg-[var(--cg-amber)]/10", label: "text-[var(--cg-amber)]" },
  info: { wrap: "border-primary/30 bg-primary/[0.06]", label: "text-primary" },
  danger: { wrap: "border-danger/30 bg-danger/5", label: "text-danger" },
};

/** Aviso canon (M7): tono semántico + etiqueta corta + contenido. Unifica los banners "[VALIDAR]". */
export function Banner({
  tone = "warning",
  label,
  children,
  className,
}: {
  tone?: Tone;
  label?: string;
  children: React.ReactNode;
  className?: string;
}) {
  const t = TONE[tone];
  return (
    <div className={cn("rounded-[var(--radius-data)] border p-3.5", t.wrap, className)}>
      <div className="flex items-start gap-2 text-sm text-foreground/80">
        {label ? <span className={cn("shrink-0 font-semibold", t.label)}>{label}</span> : null}
        <div className="min-w-0">{children}</div>
      </div>
    </div>
  );
}
