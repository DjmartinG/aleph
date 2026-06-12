import { getPortfolio, type Portfolio } from "@/lib/api";
import { fmtCop, fmtInt, fmtPct } from "@/lib/format";
import { StatPanel, type StatItem } from "@/components/stat";
import { FunnelBar } from "@/components/funnel-bar";
import { PortfolioTable } from "@/components/portfolio-table";

export default async function Page() {
  let data: Portfolio | null = null;
  let errMsg: string | null = null;
  try {
    data = await getPortfolio();
  } catch (e) {
    errMsg = e instanceof Error ? e.message : "Error desconocido";
  }

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <header className="mb-6 flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Portafolio</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Consolidado de proyectos de CG Constructora.
          </p>
        </div>
        {data ? (
          <span className="hidden whitespace-nowrap rounded-full border bg-card px-3 py-1 text-xs text-muted-foreground sm:inline">
            {fmtInt(data.consolidado.n)} proyectos · {fmtInt(data.consolidado.unidades)} unidades
          </span>
        ) : null}
      </header>

      {errMsg ? <ErrorPanel message={errMsg} /> : data ? <Dashboard data={data} /> : null}
    </div>
  );
}

function Dashboard({ data }: { data: Portfolio }) {
  const c = data.consolidado;
  const stats: StatItem[] = [
    { label: "Ventas", value: fmtCop(c.ventas), base: "Consolidado" },
    {
      label: "Utilidad oper.",
      value: fmtCop(c.util_oper),
      base: "Consolidado",
      sub: `Margen ${fmtPct(c.margen)}`,
    },
    {
      label: "VPN @TIO",
      value: fmtCop(c.vpn),
      base: "Suma proyectos",
      state: c.vpn < 0 ? "negative" : c.vpn > 0 ? "positive" : "neutral",
    },
    { label: "TIR apal. ref.", value: fmtPct(c.tir_ref), base: "Ponderada × ventas" },
    { label: "Crédito máx", value: fmtCop(c.credito_max), base: "Pico consolidado" },
    { label: "Unidades", value: fmtInt(c.unidades), base: `${fmtInt(c.n)} proyectos` },
  ];

  return (
    <div className="space-y-8">
      <StatPanel items={stats} />

      <section>
        <h2 className="mb-3 text-sm font-medium">Embudo por fase</h2>
        <FunnelBar stages={data.embudo} />
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-medium">Proyectos</h2>
          <span className="text-xs tabular-nums text-muted-foreground">
            {fmtInt(data.items.length)}
          </span>
        </div>
        <PortfolioTable items={data.items} />
      </section>
    </div>
  );
}

function ErrorPanel({ message }: { message: string }) {
  return (
    <div className="rounded-xl border border-danger/30 bg-danger/5 p-6">
      <h2 className="font-semibold text-danger">No se pudo cargar el portafolio</h2>
      <p className="mt-1 text-sm text-muted-foreground">{message}</p>
      <p className="mt-3 text-sm text-muted-foreground">
        ¿Está corriendo el API en local? Levántalo con{" "}
        <code className="rounded bg-muted px-1 py-0.5">./dev_api.ps1</code> (puerto 8000, auth
        apagada) o define{" "}
        <code className="rounded bg-muted px-1 py-0.5">ALEPH_API_URL</code>.
      </p>
    </div>
  );
}
