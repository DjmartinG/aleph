import { getPortfolio, type Portfolio } from "@/lib/api";
import { fmtCop, fmtInt, fmtPct } from "@/lib/format";
import { KpiCard } from "@/components/kpi-card";
import { PhaseBadge } from "@/components/phase-badge";
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
    <div className="flex min-h-full flex-col">
      <Header />
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold tracking-tight">Portafolio</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Consolidado de proyectos de CG Constructora.
          </p>
        </div>

        {errMsg ? (
          <ErrorPanel message={errMsg} />
        ) : data ? (
          <Dashboard data={data} />
        ) : null}
      </main>
      <Footer />
    </div>
  );
}

function Dashboard({ data }: { data: Portfolio }) {
  const c = data.consolidado;
  return (
    <div className="space-y-8">
      {/* KPIs consolidados */}
      <section className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
        <KpiCard label="Proyectos" value={fmtInt(c.n)} sub={`${fmtInt(c.unidades)} unidades`} />
        <KpiCard label="Ventas" value={fmtCop(c.ventas)} base="Consolidado" />
        <KpiCard
          label="Utilidad operativa"
          value={fmtCop(c.util_oper)}
          base="Consolidado"
          sub={`Margen ${fmtPct(c.margen)}`}
        />
        <KpiCard
          label="VPN @TIO"
          value={fmtCop(c.vpn)}
          base="Suma proyectos"
          state={c.vpn < 0 ? "negative" : c.vpn > 0 ? "positive" : "neutral"}
        />
        <KpiCard label="TIR apal. ref." value={fmtPct(c.tir_ref)} base="Ponderada por ventas" />
        <KpiCard label="Crédito máx" value={fmtCop(c.credito_max)} base="Pico consolidado" />
      </section>

      {/* Embudo por fase */}
      <section>
        <h2 className="mb-3 text-sm font-medium text-muted-foreground">Embudo por fase</h2>
        <div className="flex flex-wrap gap-2">
          {data.embudo.map((f) => (
            <div
              key={f.estado}
              className="flex items-center gap-2 rounded-lg border bg-card px-3 py-2"
            >
              <PhaseBadge estado={f.estado} label={f.label} />
              <span className="text-sm font-semibold tabular-nums">{fmtInt(f.count)}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Tabla de proyectos */}
      <section>
        <h2 className="mb-3 text-sm font-medium text-muted-foreground">Proyectos</h2>
        <PortfolioTable items={data.items} />
      </section>
    </div>
  );
}

function Header() {
  return (
    <header className="sticky top-0 z-10 border-b bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-14 w-full max-w-7xl items-center gap-3 px-4 sm:px-6 lg:px-8">
        <span className="size-2.5 rounded-full bg-primary" aria-hidden />
        <span className="font-semibold tracking-tight">ALEPH</span>
        <span className="text-sm text-muted-foreground">· CG Constructora</span>
        <span className="ml-auto text-sm text-muted-foreground">Portafolio</span>
      </div>
    </header>
  );
}

function Footer() {
  return (
    <footer className="border-t">
      <div className="mx-auto w-full max-w-7xl px-4 py-4 text-xs text-muted-foreground sm:px-6 lg:px-8">
        ALEPH · plataforma de evaluación financiera — datos del motor <code>aleph_engine</code>.
      </div>
    </footer>
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
        apagada) o define <code className="rounded bg-muted px-1 py-0.5">ALEPH_API_URL</code>.
      </p>
    </div>
  );
}
