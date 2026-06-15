import { fmtPct, splitCop } from "@/lib/format";
import { Figure } from "@/components/figure";
import { cn } from "@/lib/utils";

/**
 * Veredicto de Valor (EVA del proyecto/portafolio): ¿GENERA o DESTRUYE valor sobre el costo del
 * capital (WACC)? Color SEMÁNTICO (verde/rojo SOLO para estado, no decorativo). Greenfield → neutro.
 */
export function ValorBanner({
  creaValor,
  spread,
  valorCreado,
  valorCreadoLabel = "VPN @WACC",
  metodo,
  scope = "proyecto",
  extra,
}: {
  creaValor: boolean | null;
  spread: number | null;
  valorCreado: number | null;
  valorCreadoLabel?: string;
  metodo: string;
  scope?: "proyecto" | "portafolio";
  extra?: string;
}) {
  const estado = creaValor === null ? "greenfield" : creaValor ? "genera" : "destruye";
  const veredicto =
    estado === "genera" ? "Genera valor" : estado === "destruye" ? "Destruye valor" : "Sin veredicto";
  const tone =
    estado === "genera" ? "text-success" : estado === "destruye" ? "text-danger" : "text-muted-foreground";
  const dot =
    estado === "genera" ? "bg-success" : estado === "destruye" ? "bg-danger" : "bg-muted-foreground";
  const tint =
    estado === "genera"
      ? "border-success/25 bg-success/5"
      : estado === "destruye"
      ? "border-danger/25 bg-danger/5"
      : "border bg-card";

  return (
    <div className={cn("rounded-[var(--radius-data)] border p-4", tint)}>
      <div className="flex flex-wrap items-center justify-between gap-x-8 gap-y-3">
        <div className="flex items-center gap-3">
          <span className={cn("size-2.5 shrink-0 rounded-full", dot)} aria-hidden />
          <div>
            <div className="text-[0.7rem] font-medium uppercase tracking-wide text-muted-foreground">
              Valor económico{scope === "portafolio" ? " · portafolio" : ""}
            </div>
            <div className={cn("text-lg font-semibold tracking-tight", tone)}>
              {veredicto}
              {estado === "greenfield" ? (
                <span className="ml-1.5 text-sm font-normal text-muted-foreground">— greenfield</span>
              ) : null}
            </div>
          </div>
        </div>

        {estado !== "greenfield" ? (
          <div className="flex gap-7">
            {spread != null ? (
              <Cifra label="Spread de desarrollo" base="TIR proy. − WACC">
                <span className={cn("num text-sm font-semibold tabular-nums", tone)}>
                  {spread > 0 ? "+" : ""}
                  {fmtPct(spread)}
                </span>
              </Cifra>
            ) : null}
            {valorCreado != null ? (
              <Cifra label="Valor creado" base={valorCreadoLabel}>
                <Figure parts={splitCop(valorCreado)} className="text-sm font-semibold" />
              </Cifra>
            ) : null}
            {extra ? (
              <Cifra label="Proyectos" base="que generan valor">
                <span className="num text-sm font-semibold tabular-nums">{extra}</span>
              </Cifra>
            ) : null}
          </div>
        ) : null}
      </div>
      <p className="mt-2.5 text-xs text-muted-foreground">{metodo}</p>
    </div>
  );
}

function Cifra({ label, base, children }: { label: string; base: string; children: React.ReactNode }) {
  return (
    <div className="text-right">
      <div className="text-[0.62rem] uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="mt-0.5">{children}</div>
      <div className="text-[0.6rem] text-muted-foreground/80">{base}</div>
    </div>
  );
}
