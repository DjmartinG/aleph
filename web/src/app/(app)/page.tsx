import Link from "next/link";
import { Plus } from "lucide-react";
import { getPortfolio, type Portfolio } from "@/lib/api";
import { isAdminUser } from "@/lib/session";
import { fmtInt, fmtPct, splitCop, splitPct } from "@/lib/format";
import { StatPanel, type StatItem } from "@/components/stat";
import { FunnelBar } from "@/components/funnel-bar";
import { PortfolioTable } from "@/components/portfolio-table";
import { ValueMap } from "@/components/charts/value-map";
import { SectionTitle } from "@/components/section-title";

export default async function Page() {
  let data: Portfolio | null = null;
  let errMsg: string | null = null;
  try {
    data = await getPortfolio();
  } catch (e) {
    errMsg = e instanceof Error ? e.message : "Error desconocido";
  }
  const admin = await isAdminUser();

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-9 sm:px-6 lg:px-8">
      <header className="mb-7 flex items-end justify-between gap-4">
        <div>
          <h1 className="text-lg font-semibold tracking-tight">Portafolio</h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            Consolidado de proyectos de CG Constructora.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {data ? (
            <span className="num hidden whitespace-nowrap rounded-full border bg-card px-3 py-1 text-xs text-muted-foreground sm:inline">
              {fmtInt(data.consolidado.n)} proyectos · {fmtInt(data.consolidado.unidades)} unidades
            </span>
          ) : null}
          {admin ? (
            <Link
              href="/proyectos/nuevo"
              className="inline-flex items-center gap-1.5 rounded-[var(--radius-data)] bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground transition-[opacity,transform] [transition-timing-function:var(--ease-out)] hover:opacity-90 active:scale-[0.98]"
            >
              <Plus className="size-4" aria-hidden /> Nuevo proyecto
            </Link>
          ) : null}
        </div>
      </header>

      {errMsg ? <ErrorPanel message={errMsg} /> : data ? <Dashboard data={data} /> : null}
    </div>
  );
}

function Dashboard({ data }: { data: Portfolio }) {
  const c = data.consolidado;
  const stats: StatItem[] = [
    {
      label: "VPN @TIO",
      parts: splitCop(c.vpn),
      base: "Valor sobre la TIO, suma de proyectos",
      state: c.vpn < 0 ? "negative" : c.vpn > 0 ? "positive" : "neutral",
      emphasis: true,
    },
    { label: "Ventas", parts: splitCop(c.ventas), base: "Consolidado" },
    {
      label: "Utilidad oper.",
      parts: splitCop(c.util_oper),
      base: "Consolidado",
      sub: `Margen ${fmtPct(c.margen)}`,
    },
    { label: "TIR apal. ref.", parts: splitPct(c.tir_ref), base: "Ponderada por ventas" },
    { label: "Crédito máx", parts: splitCop(c.credito_max), base: "Pico consolidado" },
    { label: "Unidades", parts: [fmtInt(c.unidades), ""], base: `${fmtInt(c.n)} proyectos` },
  ];

  return (
    <div>
      <StatPanel items={stats} />

      <section className="mt-10">
        <SectionTitle>Embudo por fase</SectionTitle>
        <FunnelBar stages={data.embudo} />
      </section>

      <section className="mt-9">
        <SectionTitle right="TIR × margen">Mapa de valor</SectionTitle>
        <div className="rounded-[var(--radius-data)] border bg-card p-4">
          <ValueMap items={data.items} />
        </div>
      </section>

      <section className="mt-7">
        <div className="mb-3 flex items-center justify-between">
          <SectionTitle className="mb-0">Proyectos</SectionTitle>
          <span className="num text-xs text-muted-foreground">{fmtInt(data.items.length)}</span>
        </div>
        <PortfolioTable items={data.items} />
      </section>
    </div>
  );
}

function ErrorPanel({ message }: { message: string }) {
  return (
    <div className="rounded-[var(--radius-data)] border border-danger/30 bg-danger/5 p-6">
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
