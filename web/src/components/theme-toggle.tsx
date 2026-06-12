"use client";

import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";

/** Toggle de tema (light/dark) persistente en localStorage. El no-FOUC lo aplica el script del layout. */
export function ThemeToggle() {
  const [mounted, setMounted] = useState(false);
  const [dark, setDark] = useState(false);

  useEffect(() => {
    setDark(document.documentElement.classList.contains("dark"));
    setMounted(true);
  }, []);

  function toggle() {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    try {
      localStorage.setItem("aleph-theme", next ? "dark" : "light");
    } catch {
      /* almacenamiento no disponible: el tema dura la sesión */
    }
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={dark ? "Cambiar a modo claro" : "Cambiar a modo oscuro"}
      className="inline-flex size-9 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:bg-accent"
    >
      {mounted && dark ? <Sun className="size-[18px]" /> : <Moon className="size-[18px]" />}
    </button>
  );
}
