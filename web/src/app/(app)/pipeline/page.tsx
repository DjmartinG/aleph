import Link from "next/link";
import { getPortfolio, type Portfolio, type ProjectItem } from "@/lib/api";
import { fmtCop, fmtInt, splitCop, splitTir } from "@/lib/format";
import { Figure } from "@/components/figure";
import { PhaseBadge } from "@/components/phase-badge";

export default async function PipelinePage() {
  let data: Portfolio | null = null;
  let errMsg: string | null = null;
  try {
    data = await getPortfolio();
  } catch (e) {
    errMsg = e instanceof Error ? e.message : "Error desconocido";
  }

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-9 sm:px-6 lg:px-8">
      <header className="mb-7">
        <h1 className="text-lg font-semibold tracking-tight">Pipeline</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Proyectos por fase del ciclo de vida.
        </p>
      </header>

      {errMsg ? (
        <ErrorPanel message={errMsg} />
      ) : data ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {data.embudo.map((f) => {
            const items = data!.items.filter((i) => i.estado === f.estado);
            const ventas = items.reduce((a, i) => a + (i.ventas ?? 0), 0);
            return (
              <Column
                key={f.estado}
                estado={f.estado}
                label={f.label}
                count={f.count}
                ventas={ventas}
                items={items}
              />
            );
          })}
        </div>
      ) : null}
    </div>
  );
}

function Column({
  estado,
  label,
  count,
  ventas,
  items,
}: {
  estado: string;
  label: string;
  count: number;
  ventas: number;
  items: ProjectItem[];
}) {
  return (
    <section className="flex flex-col rounded-[var(--radius-data)] border bg-sidebar/40">
      <header className="flex items-center justify-between gap-2 border-b border-rule px-3 py-2.5">
        <PhaseBadge estado={estado} label={label} />
        <span className="num text-xs font-semibold tabular-nums text-muted-foreground">{fmtInt(count)}</span>
      </header>
      <div className="border-b border-rule px-3 py-2 text-[0.7rem] text-muted-foreground">
        Ventas <span className="num font-medium text-foreground">{fmtCop(ventas)}</span>
      </div>
      <div className="flex-1 space-y-2 p-2">
        {items.length === 0 ? (
          <p className="px-1 py-6 text-center text-xs text-muted-foreground">Sin proyectos en esta fase.</p>
        ) : (
          items.map((p) => <Card key={p.slug} p={p} />)
        )}
      </div>
    </section>
  );
}

function Card({ p }: { p: ProjectItem }) {
  return (
    <Link
      href={`/proyectos/${p.slug}`}
      className="group block rounded-[var(--radius-data)] border bg-card p-3 transition-colors [transition-timing-function:var(--ease-out)] hover:border-primary/40 hover:bg-accent/40"
    >
      <div className="font-medium text-foreground transition-colors group-hover:text-primary">
        {p.nombre}
      </div>
      {p.ubicacion || p.tipo ? (
        <div className="mt-0.5 text-xs text-muted-foreground">
          {[p.ubicacion, p.tipo].filter(Boolean).join(" · ")}
        </div>
      ) : null}
      <dl className="mt-2.5 grid grid-cols-3 gap-2 border-t border-rule pt-2.5 text-xs">
        <Metric label="Ventas" parts={splitCop(p.ventas)} />
        <Metric label="TIR ref." parts={splitTir(p.tir)} />
        <Metric label="VPN" parts={splitCop(p.vpn)} danger={p.vpn != null && p.vpn < 0} />
      </dl>
    </Link>
  );
}

function Metric({
  label,
  parts,
  danger,
}: {
  label: string;
  parts: [string, string];
  danger?: boolean;
}) {
  return (
    <div>
      <dt className="text-[0.65rem] uppercase tracking-wide text-muted-foreground">{label}</dt>
      <dd className={`mt-0.5 font-medium ${danger ? "text-danger" : "text-foreground"}`}>
        <Figure parts={parts} />
      </dd>
    </div>
  );
}

function ErrorPanel({ message }: { message: string }) {
  return (
    <div className="rounded-[var(--radius-data)] border border-danger/30 bg-danger/5 p-6">
      <h2 className="font-semibold text-danger">No se pudo cargar el pipeline</h2>
      <p className="mt-1 text-sm text-muted-foreground">{message}</p>
    </div>
  );
}
