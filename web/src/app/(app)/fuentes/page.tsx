import { unstable_rethrow } from "next/navigation";
import { ExternalLink } from "lucide-react";
import { getPortfolio, getWacc, type Wacc } from "@/lib/api";
import { fmtPct } from "@/lib/format";
import { FUENTES } from "@/lib/fuentes";
import { SourceNote } from "@/components/source-note";

/** Número crudo (betas): 1.29 → "1.29". null → "—". */
function fmtNum(x: number | null): string {
  return x === null || x === undefined || !isFinite(x) ? "—" : x.toFixed(2);
}

export default async function FuentesPage() {
  // La calibración macro es común a todos los proyectos; tomamos el WACC del primero que la tenga.
  let wacc: Wacc | null = null;
  let errMsg: string | null = null;
  try {
    const data = await getPortfolio();
    for (const it of data.items.slice(0, 5)) {
      const w = await getWacc(it.slug);
      if (w?.disponible) {
        wacc = w;
        break;
      }
    }
  } catch (e) {
    unstable_rethrow(e); // re-lanza el redirect a /login; deja pasar errores reales
    errMsg = e instanceof Error ? e.message : "Error desconocido";
  }

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-9 sm:px-6 lg:px-8">
      <header className="mb-7">
        <h1 className="text-lg font-semibold tracking-tight">Fuentes y metodología</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          De dónde salen los datos macroeconómicos que alimentan el costo de capital (WACC).
        </p>
      </header>

      <section className="mb-8 rounded-[var(--radius-data)] border bg-card p-5">
        <h2 className="text-sm font-semibold tracking-tight">Cómo se construye el costo de capital</h2>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          El WACC usa el método <strong className="text-foreground">build-up CAPM de Aswath Damodaran</strong> para
          mercados emergentes: CAPM en dólares (tasa libre de riesgo + beta × prima de mercado), más el{" "}
          <strong className="text-foreground">riesgo país</strong> de Colombia, llevado a pesos por{" "}
          <strong className="text-foreground">paridad de inflación</strong> CO/US. La estructura de capital
          (equity/deuda) pondera el costo del equity y el de la deuda.
        </p>
        <p className="mt-3 text-xs text-muted-foreground">
          Los valores de abajo son la <strong className="text-foreground">calibración que usa el modelo</strong>,
          común a todos los proyectos, con corte <strong className="text-foreground">junio 2026</strong>.
        </p>
      </section>

      {errMsg ? <ErrorPanel message={errMsg} /> : null}

      <div className="space-y-5">
        {FUENTES.map((g) => (
          <section key={g.fuente} className="rounded-[var(--radius-data)] border bg-card p-5">
            <div className="mb-1 flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
              <h3 className="text-sm font-semibold tracking-tight">{g.fuente}</h3>
              {g.url ? (
                <a
                  href={g.url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 text-xs text-primary transition-colors [transition-timing-function:var(--ease-out)] hover:underline"
                >
                  Ver fuente <ExternalLink className="size-3" aria-hidden />
                </a>
              ) : (
                <span className="text-xs text-muted-foreground">Definición interna</span>
              )}
            </div>
            <p className="mb-3 text-xs text-muted-foreground">{g.nota}</p>
            <dl className="divide-y divide-[var(--rule)]">
              {g.datos.map((d) => {
                const v = wacc ? d.get(wacc) : null;
                const txt = v === null || v === undefined ? "—" : d.fmt === "pct" ? fmtPct(v) : fmtNum(v);
                return (
                  <div key={d.nombre} className="flex items-baseline justify-between gap-4 py-2.5">
                    <div className="min-w-0">
                      <dt className="text-sm font-medium text-foreground">{d.nombre}</dt>
                      <dd className="mt-0.5 text-xs leading-relaxed text-muted-foreground">{d.descripcion}</dd>
                    </div>
                    <span className="num shrink-0 text-sm font-semibold tabular-nums text-foreground">{txt}</span>
                  </div>
                );
              })}
            </dl>
          </section>
        ))}
      </div>

      <div className="mt-8">
        <SourceNote>
          Metodología build-up CAPM (Damodaran, mercado emergente). La calibración (corte jun-2026) está
          auditada en el acta de re-baseline del comité. Los valores que ves son los que el modelo usa para
          calcular el WACC de cada proyecto; todavía no son el dato en vivo de la fuente (eso llega en una
          fase futura).
        </SourceNote>
      </div>
    </div>
  );
}

function ErrorPanel({ message }: { message: string }) {
  return (
    <div className="mb-5 rounded-[var(--radius-data)] border border-danger/30 bg-danger/5 p-6">
      <h2 className="font-semibold text-danger">No se pudieron cargar los valores de la calibración</h2>
      <p className="mt-1 text-sm text-muted-foreground">{message}</p>
      <p className="mt-2 text-sm text-muted-foreground">La metodología y las fuentes siguen disponibles arriba.</p>
    </div>
  );
}
