"use client";

import { useTransition } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Check, ChevronRight, RefreshCw, X } from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";
import { AlephMark } from "@/components/aleph-mark";
import { PhaseBadge } from "@/components/phase-badge";
import { useProjectHeader } from "@/components/project-context";
import { cn } from "@/lib/utils";

function crumbs(pathname: string, nombre?: string): string[] {
  if (!pathname || pathname === "/") return ["Portafolio"];
  const parts = pathname.split("/").filter(Boolean);
  if (parts[0] === "proyectos") return ["Portafolio", nombre ?? parts[1] ?? "Proyecto"];
  return ["Portafolio", ...parts];
}

export function Topbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [refreshing, startRefresh] = useTransition();
  const project = useProjectHeader();
  const trail = crumbs(pathname, project?.nombre);

  return (
    <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b bg-background/75 px-4 backdrop-blur sm:px-6">
      {/* Wordmark compacto en móvil (sidebar oculto). */}
      <div className="flex items-center gap-2 md:hidden">
        <AlephMark />
        <span className="text-sm font-semibold uppercase tracking-[0.2em]">ALEPH</span>
      </div>

      <nav aria-label="Ruta" className="hidden items-center gap-1.5 text-sm md:flex">
        {trail.map((c, i) => (
          <span key={`${c}-${i}`} className="flex items-center gap-1.5">
            {i > 0 ? <ChevronRight className="size-3.5 text-muted-foreground/50" aria-hidden /> : null}
            <span
              className={
                i === trail.length - 1 ? "font-medium text-foreground" : "text-muted-foreground"
              }
            >
              {c}
            </span>
          </span>
        ))}
      </nav>

      {/* Contexto del proyecto activo (header permanente): Fase · Escenario · estado de Cuadres.
          El badge de cuadres queda visible desde cualquier pestaña/módulo de la ficha. */}
      {project ? (
        <div className="hidden shrink-0 items-center gap-2 lg:flex">
          <span aria-hidden className="h-4 w-px bg-rule" />
          <PhaseBadge estado={project.estado} />
          <span className="num whitespace-nowrap rounded-full border bg-card px-2 py-0.5 text-xs text-muted-foreground">
            Escenario · {project.escenario}
          </span>
          {project.checks ? (
            <span
              title={
                project.checks.allOk
                  ? "Todos los cuadres del modelo pasan"
                  : `${project.checks.nFail} de ${project.checks.total} cuadres por revisar`
              }
              className={cn(
                "inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium",
                project.checks.allOk ? "bg-success/10 text-success" : "bg-danger/10 text-danger",
              )}
            >
              {project.checks.allOk ? (
                <Check className="size-3.5" aria-hidden />
              ) : (
                <X className="size-3.5" aria-hidden />
              )}
              {project.checks.allOk ? "Cuadres OK" : `Cuadres: revisar ${project.checks.nFail}`}
            </span>
          ) : null}
        </div>
      ) : null}

      <div className="ml-auto flex items-center gap-1.5">
        {/* Recargar: vuelve a traer los datos del servidor sin recargar la página ni re-loguear. */}
        <button
          type="button"
          aria-label="Recargar datos"
          title="Recargar datos del servidor"
          onClick={() => startRefresh(() => router.refresh())}
          disabled={refreshing}
          className="inline-flex items-center gap-1.5 rounded-[var(--radius-data)] border px-2.5 py-1.5 text-sm text-muted-foreground transition-[color,background-color,transform] [transition-duration:var(--dur-1)] [transition-timing-function:var(--ease-out)] hover:bg-accent hover:text-foreground active:scale-95 disabled:opacity-60"
        >
          <RefreshCw className={cn("size-4", refreshing && "animate-spin")} aria-hidden />
          <span className="hidden sm:inline">{refreshing ? "Recargando…" : "Recargar"}</span>
        </button>
        <ThemeToggle />
        <div className="flex items-center gap-2 rounded-full border bg-card py-1 pl-1 pr-3">
          <span className="flex size-7 items-center justify-center rounded-full bg-primary text-xs font-semibold text-primary-foreground">
            CG
          </span>
          <span className="hidden text-sm text-muted-foreground sm:inline">CG Constructora</span>
        </div>
      </div>
    </header>
  );
}
