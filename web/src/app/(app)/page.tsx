import Link from "next/link";
import { unstable_rethrow } from "next/navigation";
import { Plus } from "lucide-react";
import {
  getPortfolio,
  getTesoreria,
  getCapital,
  getEstres,
  getConcentracion,
  type Portfolio,
  type Tesoreria,
  type Capital,
  type Estres,
  type Concentracion,
} from "@/lib/api";
import { isAdminUser } from "@/lib/session";
import { fmtCop, fmtInt, fmtPct, splitCop, splitPct } from "@/lib/format";
import { monthLabel } from "@/lib/timeline";
import { StatPanel, type StatItem } from "@/components/stat";
import { ValorBanner } from "@/components/valor-banner";
import { FunnelBar } from "@/components/funnel-bar";
import { PortfolioTable } from "@/components/portfolio-table";
import { CapitalTable } from "@/components/capital-table";
import { ValueMap } from "@/components/charts/value-map";
import { ProjectCompare } from "@/components/charts/project-compare";
import { CashFlowChart, type CashPoint } from "@/components/charts/cash-flow-chart";
import { TesoreriaEstres } from "@/components/charts/tesoreria-estres";
import { ConcentracionPanel } from "@/components/charts/concentracion-panel";
import { MiniStat } from "@/components/mini-stat";
import { SectionTitle } from "@/components/section-title";

export default async function Page() {
  let data: Portfolio | null = null;
  let tesoreria: Tesoreria | null = null;
  let capital: Capital | null = null;
  let estres: Estres | null = null;
  let concentracion: Concentracion | null = null;
  let errMsg: string | null = null;
  try {
    data = await getPortfolio();
  } catch (e) {
    unstable_rethrow(e); // re-lanza el redirect a /login (401 = sesión expirada) y notFound; deja pasar errores reales
    errMsg = e instanceof Error ? e.message : "Error desconocido";
  }
  // Tesorería + capital + estrés + concentración (opcionales): degradan limpio si el API no los expone.
  try {
    [tesoreria, capital, estres, concentracion] = await Promise.all([
      getTesoreria(),
      getCapital(),
      getEstres(),
      getConcentracion(),
    ]);
  } catch (e) {
    unstable_rethrow(e);
    tesoreria = null;
    capital = null;
    estres = null;
    concentracion = null;
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

      {errMsg ? (
        <ErrorPanel message={errMsg} />
      ) : data ? (
        <Dashboard
          data={data}
          tesoreria={tesoreria}
          capital={capital}
          estres={estres}
          concentracion={concentracion}
        />
      ) : null}
    </div>
  );
}

function Dashboard({
  data,
  tesoreria,
  capital,
  estres,
  concentracion,
}: {
  data: Portfolio;
  tesoreria: Tesoreria | null;
  capital: Capital | null;
  estres: Estres | null;
  concentracion: Concentracion | null;
}) {
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

      {/* Veredicto de Valor del PORTAFOLIO (EVA). Solo si el API ya lo expone (degrada limpio). */}
      {c.valor_metodo ? (
        <div className="mt-6">
          <ValorBanner
            scope="portafolio"
            creaValor={c.crea_valor}
            spread={null}
            valorCreado={c.valor_creado}
            metodo={c.valor_metodo}
            extra={`${c.n_genera}/${c.n_evaluados}`}
          />
        </div>
      ) : null}

      {/* Tesorería consolidada (Pilar 2): la caja y la financiación de TODOS los proyectos en el
          tiempo. Degrada limpio si el API aún no expone el endpoint. */}
      {tesoreria?.disponible ? (
        <section className="mt-10">
          <SectionTitle right="todos los proyectos en el tiempo">Tesorería consolidada</SectionTitle>
          <div className="rounded-[var(--radius-data)] border bg-card p-4">
            <div className="mb-4 grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-3">
              <MiniStat
                label="Necesidad máx. de caja"
                value={fmtCop(Math.abs(tesoreria.exposicion_maxima.valor))}
                note={`combinada · pico ${monthLabel(tesoreria.base_date, tesoreria.exposicion_maxima.mes)}`}
              />
              <MiniStat
                label="Crédito máx. combinado"
                value={fmtCop(tesoreria.credito_maximo.valor)}
                note={`pico ${monthLabel(tesoreria.base_date, tesoreria.credito_maximo.mes)}`}
              />
              <MiniStat label="Proyectos" value={fmtInt(tesoreria.n)} note="con cronograma datado" />
            </div>
            <CashFlowChart
              data={tesoreria.caja.map<CashPoint>((v, m) => ({ m, acum: v, credito: tesoreria.credito[m] ?? 0 }))}
              maxExposure={{ m: tesoreria.exposicion_maxima.mes, value: tesoreria.exposicion_maxima.valor }}
              baseDate={tesoreria.base_date}
            />
            <p className="mt-2 text-xs text-muted-foreground">
              Caja y crédito de todos los proyectos sumados mes a mes. La necesidad combinada es{" "}
              <strong className="text-foreground">menor</strong> que sumar los picos individuales: no
              coinciden en el tiempo.
            </p>
          </div>
        </section>
      ) : null}

      {/* Estrés de tesorería (Pilar 2): cuánto se profundiza el valle si el mercado se enfría. */}
      {estres?.disponible && estres.escenarios.length > 0 ? (
        <section className="mt-10">
          <SectionTitle right="resistencia ante una desaceleración">Estrés de tesorería</SectionTitle>
          <TesoreriaEstres data={estres} />
        </section>
      ) : null}

      {/* Asignación de capital (Pilar 2): dónde rinde más cada peso de capital escaso. */}
      {capital && capital.filas.length > 0 ? (
        <section className="mt-10">
          <SectionTitle right="dónde rinde más el capital escaso">Asignación de capital</SectionTitle>
          <CapitalTable data={capital} />
          <p className="mt-2 text-xs text-muted-foreground">
            <strong className="text-foreground">Eficiencia</strong> = valor creado (EVA) por cada peso
            de <strong className="text-foreground">equity pico</strong> (necesidad máxima de caja propia
            tras el crédito). Rankea dónde priorizar el capital; greenfield aún sin veredicto de valor.
          </p>
        </section>
      ) : null}

      {/* Concentración / diversificación (Pilar 2): exposición por dimensión. */}
      {concentracion && concentracion.dimensiones.length > 0 ? (
        <section className="mt-10">
          <SectionTitle right="exposición por dimensión">Concentración del portafolio</SectionTitle>
          <ConcentracionPanel data={concentracion} />
          <p className="mt-2 text-xs text-muted-foreground">
            Reparto de las ventas por dimensión. El <strong className="text-foreground">número efectivo</strong>{" "}
            (1/HHI) dice a cuántas categorías iguales equivale la concentración: pocas efectivas o un líder
            dominante = cartera expuesta a una ciudad, un segmento o un solo proyecto.
          </p>
        </section>
      ) : null}

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

      {data.items.length >= 2 ? (
        <section className="mt-9">
          <SectionTitle right="elige proyectos y métrica">Comparador</SectionTitle>
          <div className="rounded-[var(--radius-data)] border bg-card p-4">
            <ProjectCompare items={data.items} />
          </div>
        </section>
      ) : null}

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
  const authOn = !!process.env.AUTH_MICROSOFT_ENTRA_ID_ID;
  return (
    <div className="rounded-[var(--radius-data)] border border-danger/30 bg-danger/5 p-6">
      <h2 className="font-semibold text-danger">No se pudo cargar el portafolio</h2>
      <p className="mt-1 text-sm text-muted-foreground">{message}</p>
      <p className="mt-3 text-sm text-muted-foreground">
        {authOn ? (
          "No se pudo conectar con el servicio. Reintenta en unos segundos; si el problema persiste, vuelve a iniciar sesión o avisa a soporte."
        ) : (
          <>
            ¿Está corriendo el API en local? Levántalo con{" "}
            <code className="rounded bg-muted px-1 py-0.5">./dev_api.ps1</code> (puerto 8000, auth
            apagada) o define <code className="rounded bg-muted px-1 py-0.5">ALEPH_API_URL</code>.
          </>
        )}
      </p>
    </div>
  );
}
