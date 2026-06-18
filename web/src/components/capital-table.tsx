import type { Capital } from "@/lib/api";
import { splitCop } from "@/lib/format";
import { cn } from "@/lib/utils";
import { Figure } from "@/components/figure";

/**
 * Asignación de capital (Pilar 2): rankea los proyectos por EFICIENCIA de capital (valor creado /
 * equity pico) — dónde rinde más cada peso escaso. Color SEMÁNTICO (verde genera / rojo destruye, solo
 * para estado). Greenfield → "— greenfield" (sin veredicto de valor, consistente con el resto de la app).
 */
export function CapitalTable({ data }: { data: Capital }) {
  const maxEff = Math.max(...data.filas.map((f) => Math.abs(f.eficiencia ?? 0)), 0.01);
  return (
    <div className="overflow-hidden rounded-[var(--radius-data)] border bg-card">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-rule text-xs uppercase tracking-wide text-muted-foreground">
              <Th className="text-left">Proyecto</Th>
              <Th className="text-right">Equity pico</Th>
              <Th className="text-right">Crédito máx</Th>
              <Th className="text-right">Valor creado</Th>
              <Th className="text-right">
                Eficiencia <span className="font-normal normal-case text-muted-foreground/60">valor/equity</span>
              </Th>
            </tr>
          </thead>
          <tbody>
            {data.filas.map((f, i) => (
              <tr key={f.slug} className="border-b border-rule last:border-0 transition-colors [transition-timing-function:var(--ease-out)] hover:bg-accent/40">
                <Td>
                  <div>
                    <span className="num mr-2.5 tabular-nums text-muted-foreground/70">{i + 1}</span>
                    <span className="font-medium">{f.nombre}</span>
                  </div>
                  {f.tipo ? (
                    <div className="mt-0.5 pl-[1.6rem] text-xs text-muted-foreground">{f.tipo}</div>
                  ) : null}
                </Td>
                <Td className="text-right">
                  <Figure parts={splitCop(f.equity_pico)} />
                </Td>
                <Td className="text-right text-muted-foreground">
                  <Figure parts={splitCop(f.credito_max)} />
                </Td>
                <Td className="text-right">
                  {f.valor_creado == null ? (
                    <span className="text-sm text-muted-foreground">— greenfield</span>
                  ) : (
                    <Figure
                      parts={splitCop(f.valor_creado)}
                      className={f.valor_creado >= 0 ? "text-success" : "text-danger"}
                    />
                  )}
                </Td>
                <Td className="text-right">
                  <EffBar eff={f.eficiencia} max={maxEff} />
                </Td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="border-t-2 border-border text-sm">
              <Td className="font-medium text-muted-foreground">Suma de picos individuales</Td>
              <Td className="text-right">
                <Figure parts={splitCop(data.equity_total)} />
              </Td>
              <Td className="text-right text-muted-foreground">
                <Figure parts={splitCop(data.credito_total)} />
              </Td>
              <Td className="text-right">
                <Figure
                  parts={splitCop(data.valor_creado_total)}
                  className={data.valor_creado_total >= 0 ? "text-success" : "text-danger"}
                />
              </Td>
              <Td className="text-right">
                <EffBar eff={data.eficiencia_portafolio} max={maxEff} />
              </Td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}

/** Barra divergente: eficiencia positiva (teal) a la derecha del centro, negativa (roja) a la izquierda. */
function EffBar({ eff, max }: { eff: number | null; max: number }) {
  if (eff == null) {
    return <span className="text-sm text-muted-foreground">—</span>;
  }
  const pos = eff >= 0;
  const w = Math.min(50, (Math.abs(eff) / max) * 50); // % del contenedor; el centro está al 50%
  const txt = eff.toLocaleString("es-CO", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  return (
    <div className="flex items-center justify-end gap-2.5">
      <span className={cn("num tabular-nums font-medium", pos ? "text-success" : "text-danger")}>{txt}</span>
      <div className="relative hidden h-3.5 w-24 shrink-0 sm:block" aria-hidden>
        <span className="absolute inset-y-0 left-1/2 w-px bg-rule" />
        <span
          className={cn(
            "absolute top-1/2 h-2 -translate-y-1/2 rounded-[2px]",
            pos ? "left-1/2 bg-success" : "right-1/2 bg-danger",
          )}
          style={{ width: `${w}%` }}
        />
      </div>
    </div>
  );
}

function Th({ children, className }: { children?: React.ReactNode; className?: string }) {
  return <th className={cn("px-4 py-2.5 font-medium", className)}>{children}</th>;
}

function Td({ children, className }: { children?: React.ReactNode; className?: string }) {
  return <td className={cn("px-4 py-3 align-middle", className)}>{children}</td>;
}
