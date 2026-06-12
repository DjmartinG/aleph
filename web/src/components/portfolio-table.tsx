import Link from "next/link";
import { ChevronRight } from "lucide-react";
import type { ProjectItem } from "@/lib/api";
import { fmtInt, splitCop, splitPct } from "@/lib/format";
import { cn } from "@/lib/utils";
import { Figure } from "@/components/figure";
import { PhaseBadge } from "@/components/phase-badge";

/** Tabla densa de proyectos. Cifras a la derecha (unidad de-enfatizada); fila navegable con acento teal. */
export function PortfolioTable({ items }: { items: ProjectItem[] }) {
  return (
    <div className="overflow-hidden rounded-[var(--radius-data)] border bg-card">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-rule text-xs uppercase tracking-wide text-muted-foreground">
              <Th className="text-left">Proyecto</Th>
              <Th className="text-left">Fase</Th>
              <Th className="text-right">Ventas</Th>
              <Th className="text-right">TIR apal. ref.</Th>
              <Th className="text-right">VPN @TIO</Th>
              <Th className="text-right">Unidades</Th>
              <Th className="w-8" aria-label="" />
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-10 text-center text-sm text-muted-foreground">
                  Sin proyectos para mostrar.
                </td>
              </tr>
            ) : (
              items.map((p) => (
                <tr
                  key={p.slug}
                  className="group relative border-b border-rule last:border-0 transition-colors [transition-timing-function:var(--ease-out)] hover:bg-accent/40 before:absolute before:inset-y-0 before:left-0 before:w-0.5 before:bg-primary before:opacity-0 before:transition-opacity hover:before:opacity-100"
                >
                  <Td>
                    <Link
                      href={`/proyectos/${p.slug}`}
                      className="font-medium text-foreground transition-colors group-hover:text-primary"
                    >
                      {p.nombre}
                    </Link>
                    {p.ubicacion || p.tipo ? (
                      <div className="text-xs text-muted-foreground">
                        {[p.ubicacion, p.tipo].filter(Boolean).join(" · ")}
                      </div>
                    ) : null}
                  </Td>
                  <Td>
                    <PhaseBadge estado={p.estado} />
                  </Td>
                  <Td className="text-right">
                    <Figure parts={splitCop(p.ventas)} />
                  </Td>
                  <Td className="text-right">
                    <Figure
                      parts={splitPct(p.tir)}
                      className={p.tir == null ? "text-muted-foreground" : undefined}
                    />
                  </Td>
                  <Td className="text-right">
                    <Figure
                      parts={splitCop(p.vpn)}
                      className={p.vpn != null && p.vpn < 0 ? "text-danger" : undefined}
                    />
                  </Td>
                  <Td className="num text-right">{fmtInt(p.und)}</Td>
                  <Td className="pl-0 pr-3 text-right">
                    <ChevronRight className="ml-auto size-4 text-muted-foreground/40 transition-all [transition-timing-function:var(--ease-out)] group-hover:translate-x-0.5 group-hover:text-primary" />
                  </Td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Th({ children, className }: { children?: React.ReactNode; className?: string }) {
  return <th className={cn("px-4 py-2.5 font-medium", className)}>{children}</th>;
}

function Td({ children, className }: { children?: React.ReactNode; className?: string }) {
  return <td className={cn("px-4 py-3 align-top", className)}>{children}</td>;
}
