import Link from "next/link";
import type { ProjectItem } from "@/lib/api";
import { fmtCop, fmtInt, fmtPct } from "@/lib/format";
import { cn } from "@/lib/utils";
import { PhaseBadge } from "@/components/phase-badge";

/** Tabla densa de proyectos del portafolio. Cifras a la derecha, tabular-nums. */
export function PortfolioTable({ items }: { items: ProjectItem[] }) {
  return (
    <div className="overflow-hidden rounded-xl border bg-card">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/40 text-xs uppercase tracking-wide text-muted-foreground">
              <Th className="text-left">Proyecto</Th>
              <Th className="text-left">Fase</Th>
              <Th className="text-right">Ventas</Th>
              <Th className="text-right">TIR apal. ref.</Th>
              <Th className="text-right">VPN @TIO</Th>
              <Th className="text-right">Unidades</Th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                  Sin proyectos para mostrar.
                </td>
              </tr>
            ) : (
              items.map((p) => (
                <tr
                  key={p.slug}
                  className="border-b last:border-0 transition-colors hover:bg-muted/40"
                >
                  <Td className="text-left">
                    <Link
                      href={`/proyectos/${p.slug}`}
                      className="font-medium text-foreground hover:text-primary hover:underline"
                    >
                      {p.nombre}
                    </Link>
                    {(p.ubicacion || p.tipo) && (
                      <div className="text-xs text-muted-foreground">
                        {[p.ubicacion, p.tipo].filter(Boolean).join(" · ")}
                      </div>
                    )}
                  </Td>
                  <Td className="text-left">
                    <PhaseBadge estado={p.estado} />
                  </Td>
                  <Td className="text-right tabular-nums">{fmtCop(p.ventas)}</Td>
                  <Td className="text-right tabular-nums">{fmtPct(p.tir)}</Td>
                  <Td
                    className={cn(
                      "text-right tabular-nums",
                      p.vpn != null && p.vpn < 0 ? "text-danger" : "text-foreground",
                    )}
                  >
                    {fmtCop(p.vpn)}
                  </Td>
                  <Td className="text-right tabular-nums">{fmtInt(p.und)}</Td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Th({ children, className }: { children: React.ReactNode; className?: string }) {
  return <th className={cn("px-4 py-2.5 font-medium", className)}>{children}</th>;
}

function Td({ children, className }: { children: React.ReactNode; className?: string }) {
  return <td className={cn("px-4 py-3 align-top", className)}>{children}</td>;
}
