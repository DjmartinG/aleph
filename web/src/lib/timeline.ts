/** Utilidades de línea de tiempo para el cronograma: convierte offsets de mes (desde `base_date`)
 * en marcas de año y etiquetas legibles. `base_date` es ISO 'YYYY-MM-DD' (el mes 0 de las series). */

const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];

/** Marcas de año (el primer mes de cada año natural) dentro del horizonte. */
export function yearTicks(baseDate: string | null, horizonte: number): { m: number; label: string }[] {
  if (!baseDate) return [];
  const [y, mo] = baseDate.split("-").map(Number);
  const out: { m: number; label: string }[] = [];
  for (let m = 0; m < horizonte; m++) {
    const abs = mo - 1 + m; // mes absoluto 0-based desde el año y
    if (abs % 12 === 0) out.push({ m, label: String(y + Math.floor(abs / 12)) });
  }
  return out;
}

/** Etiqueta 'mmm aa' de un offset de mes desde base_date (p.ej. 'ago 22'). */
export function monthLabel(baseDate: string | null, m: number): string {
  if (!baseDate) return `mes ${m + 1}`;
  const [y, mo] = baseDate.split("-").map(Number);
  const abs = mo - 1 + m;
  const yy = y + Math.floor(abs / 12);
  return `${MESES[((abs % 12) + 12) % 12]} ${String(yy).slice(2)}`;
}
