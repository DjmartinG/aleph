"use client";

import { usePathname } from "next/navigation";
import { ChevronRight } from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";
import { AlephMark } from "@/components/aleph-mark";

function crumbs(pathname: string): string[] {
  if (!pathname || pathname === "/") return ["Portafolio"];
  const parts = pathname.split("/").filter(Boolean);
  if (parts[0] === "proyectos") return ["Portafolio", parts[1] ?? "Proyecto"];
  return ["Portafolio", ...parts];
}

export function Topbar() {
  const pathname = usePathname();
  const trail = crumbs(pathname);

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

      <div className="ml-auto flex items-center gap-1">
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
