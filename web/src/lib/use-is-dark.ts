"use client";

import { useEffect, useState } from "react";

/**
 * ¿El tema activo es oscuro? El app togglea con `document.documentElement.classList.toggle("dark")`
 * (ver theme-toggle.tsx), sin next-themes. Este hook lee esa clase y se RE-EVALÚA en vivo (vía
 * MutationObserver) → las gráficas se re-pintan al togglear el tema sin recargar.
 */
export function useIsDark(): boolean {
  const [isDark, setIsDark] = useState<boolean>(
    () => typeof document !== "undefined" && document.documentElement.classList.contains("dark"),
  );

  useEffect(() => {
    const root = document.documentElement;
    const read = () => setIsDark(root.classList.contains("dark"));
    read(); // por si cambió entre el primer render y el montaje
    const obs = new MutationObserver(read);
    obs.observe(root, { attributes: true, attributeFilter: ["class"] });
    return () => obs.disconnect();
  }, []);

  return isDark;
}
