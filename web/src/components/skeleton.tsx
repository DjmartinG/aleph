import { cn } from "@/lib/utils";

/** Bloque de carga (skeleton). Nunca un spinner en medio del contenido. */
export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("animate-pulse rounded-md bg-muted", className)} aria-hidden />;
}
