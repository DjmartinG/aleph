/** Versión del software (M7). Fuente única; el footer del shell la muestra. El SHA viene del build
 *  de Vercel (VERCEL_GIT_COMMIT_SHA), para trazar exactamente qué commit está en producción. */
export const APP_VERSION = "0.7.0";

/** SHA corto del commit desplegado (server-side; en dev local no existe → null). */
export function commitSha(): string | null {
  const s = process.env.VERCEL_GIT_COMMIT_SHA;
  return s ? s.slice(0, 7) : null;
}
