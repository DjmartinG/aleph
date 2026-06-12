/**
 * Formato único de presentación (moneda y porcentaje) — réplica EXACTA de
 * `app_streamlit/ui/format.py` (fuente de verdad). Convención CG: montos en MILES COP;
 * separador de miles con punto. NO contiene lógica financiera (solo presentación).
 */

/** `f"{v:,.Nf}".replace(",", ".")` de Python: agrupa en en-US y cambia la coma por punto. */
function enDot(v: number, decimals: number): string {
  return v
    .toLocaleString("en-US", {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    })
    .replace(/,/g, ".");
}

/**
 * Formatea un monto en MILES COP a pesos legibles (idéntico a `fmt_cop`).
 * - ≥ mil millones → "mil M" (miles de millones), 1 decimal.
 * - si no → "M" (millones), sin decimales.
 * - 0/null/undefined/NaN → "$0".
 */
export function fmtCop(x: number | null | undefined): string {
  if (!x) return "$0";
  if (Math.abs(x) >= 1_000_000) return `$${enDot(x / 1_000_000, 1)} mil M`;
  return `$${enDot(x / 1000, 0)} M`;
}

/** Formatea una fracción como porcentaje (0.2183 → "21.83%"). null/undefined → "n/d". */
export function fmtPct(x: number | null | undefined, dec = 2): string {
  if (x === null || x === undefined || !isFinite(x)) return "n/d";
  return `${(x * 100).toFixed(dec)}%`;
}

/** Entero con separador de miles es-CO (para unidades): 1234 → "1.234". */
export function fmtInt(x: number | null | undefined): string {
  if (x === null || x === undefined || !isFinite(x)) return "—";
  return Math.round(x).toLocaleString("es-CO");
}
