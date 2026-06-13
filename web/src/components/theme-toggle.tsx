"use client";

import { Moon, Sun } from "lucide-react";

/**
 * Toggle de tema (light/dark) persistente en localStorage. El no-FOUC lo aplica el script del layout.
 * Sin estado React: el icono correcto se muestra por CSS (variante `dark:`), evitando mismatch de
 * hidratación y parpadeo.
 */
export function ThemeToggle() {
  function toggle() {
    const isDark = document.documentElement.classList.toggle("dark");
    try {
      localStorage.setItem("aleph-theme", isDark ? "dark" : "light");
    } catch {
      /* almacenamiento no disponible: el tema dura la sesión */
    }
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label="Cambiar tema (claro / oscuro)"
      className="inline-flex size-9 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:bg-accent"
    >
      <Moon className="size-[18px] dark:hidden" aria-hidden />
      <Sun className="hidden size-[18px] dark:block" aria-hidden />
    </button>
  );
}
