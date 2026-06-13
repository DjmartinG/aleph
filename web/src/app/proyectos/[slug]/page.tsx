import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { getProject, getResults, type Pyg, type Results } from "@/lib/api";
import { fmtCop, fmtInt, fmtPct, splitCop, splitPct } from "@/lib/format";
import { StatPanel, type StatItem } from "@/components/stat";
import { Figure } from "@/components/figure";
import { PhaseBadge } from "@/components/phase-badge";
import { ChecksBadge } from "@/components/checks-badge";
import { SectionTitle } from "@/components/section-title";

/** "TIR proyecto · proyecto (desapalancada)" → ["TIR proyecto", "proyecto (desapalancada)"]. */
function splitLabel(s: string): [string, string] {
  const i = s.indexOf(" · ");
  return i >= 0 ? [s.slice(0, i), s.slice(i + 3)] : [s, ""];
}

export default async function ProyectoPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const [project, results] = await Promise.all([getProject(slug), getResults(slug)]);
  if (!project || !results) notFound();

  const { meta, estado, es_real } = project;
  const ind = results.indicadores;
  const pyg = results.pyg;
  const [tpL, tpB] = splitLabel(ind.tir_proyecto_label);
  const [tsL, tsB] = splitLabel(ind.tir_socio_label);

  const stats: StatItem[] = [
    { label: tpL, parts: splitPct(ind.tir_proyecto), base: tpB || "desapalancada", emphasis: true },
    { label: tsL, parts: splitPct(ind.tir_socio), base: tsB || "apalancada" },
    {
      label: ind.vpn_label || "VPN @TIO",
      parts: splitCop(ind.vpn_proyecto),
      base: "sobre la TIO",
      state: ind.vpn_proyecto != null && ind.vpn_proyecto < 0 ? "negative" : "positive",
    },
    { label: "Margen oper.", parts: splitPct(ind.margen_oper), base: "sobre ventas" },
    { label: "Ventas", parts: splitCop(pyg.ventas), base: "totales" },
    { label: "Utilidad oper.", parts: splitCop(pyg.util_oper), base: "consolidada" },
  ];

  const okAll = results.checks.every((c) => c.ok);

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-9 sm:px-6 lg:px-8">
      <Link
        href="/"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="size-4" aria-hidden /> Portafolio
      </Link>

      <header className="mb-7 flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-semibold tracking-tight">{meta.nombre}</h1>
            <PhaseBadge estado={estado} />
            {!es_real ? (
              <span className="rounded bg-muted px-1.5 py-0.5 text-[0.7rem] font-medium text-muted-foreground">
                ilustrativo
              </span>
            ) : null}
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            {[meta.ubicacion, meta.zona, meta.tipo].filter(Boolean).join(" · ")}
          </p>
        </div>
        {meta.unidades ? (
          <span className="num whitespace-nowrap rounded-full border bg-card px-3 py-1 text-xs text-muted-foreground">
            {fmtInt(meta.unidades)} unidades
          </span>
        ) : null}
      </header>

      <StatPanel items={stats} />

      {/* Costo de capital + crédito (indicadores secundarios). */}
      <div className="mt-4 grid grid-cols-2 gap-x-6 gap-y-3 rounded-[var(--radius-data)] border bg-card p-4 sm:grid-cols-4">
        <Mini label="WACC" value={fmtPct(ind.wacc)} note="Damodaran" />
        <Mini label="TIO" value={fmtPct(ind.tio)} note="tasa objetivo" />
        <Mini label="Crédito máx" value={fmtCop(ind.credito_max)} note="pico" />
        <Mini
          label="Payback"
          value={ind.payback_mes != null ? `${fmtInt(ind.payback_mes)} m` : "n/d"}
          note="meses"
        />
      </div>

      <section className="mt-9">
        <SectionTitle right={okAll ? "todos OK" : "revisar"}>Cuadres</SectionTitle>
        <div className="flex flex-wrap gap-2 rounded-[var(--radius-data)] border bg-card p-4">
          {results.checks.map((c) => (
            <ChecksBadge key={c.clave} nombre={c.nombre} ok={c.ok} />
          ))}
        </div>
      </section>

      <section className="mt-9">
        <SectionTitle>Estado de resultados (P&amp;G)</SectionTitle>
        <Ledger pyg={pyg} indicadores={results} />
      </section>
    </div>
  );
}

function Mini({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div>
      <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="num mt-0.5 text-base font-semibold">{value}</div>
      {note ? <div className="text-[0.7rem] text-muted-foreground/80">{note}</div> : null}
    </div>
  );
}

function Ledger({ pyg, indicadores }: { pyg: Pyg; indicadores: Results }) {
  const margen = indicadores.indicadores.margen_oper;
  return (
    <div className="overflow-hidden rounded-[var(--radius-data)] border bg-card">
      <table className="w-full text-sm">
        <tbody>
          <Group>Ingresos</Group>
          <Row label="Ventas" value={pyg.ventas} />
          {pyg.recon_codensa ? <Row label="Reconocimiento" value={pyg.recon_codensa} /> : null}
          <Row label="Total ingresos" value={pyg.total_ingresos} strong />

          <Group>Costos</Group>
          <Row label="Costo directo" value={pyg.directos} muted />
          <Row label="Indirectos" value={pyg.indirectos} muted />
          <Row label="Honorarios" value={pyg.honorarios} muted />
          {pyg.gastos_fijos ? <Row label="Gastos fijos" value={pyg.gastos_fijos} muted /> : null}
          <Row label="Lote" value={pyg.costo_lote} muted />

          <Group>Resultado</Group>
          <Row label="Utilidad operativa" value={pyg.util_oper} strong />
          <RowText label="Margen operativo" text={fmtPct(margen)} />

          <Group>Reparto</Group>
          <Row label="CG Constructora" value={pyg.cg} />
          <Row label="Socio" value={pyg.socio} />
        </tbody>
      </table>
    </div>
  );
}

function Group({ children }: { children: React.ReactNode }) {
  return (
    <tr className="border-b border-rule bg-muted/30">
      <th
        colSpan={2}
        className="px-4 py-1.5 text-left text-[0.7rem] font-semibold uppercase tracking-wider text-muted-foreground"
      >
        {children}
      </th>
    </tr>
  );
}

function Row({
  label,
  value,
  strong,
  muted,
}: {
  label: string;
  value: number;
  strong?: boolean;
  muted?: boolean;
}) {
  return (
    <tr className="border-b border-rule last:border-0">
      <td className={`px-4 py-2.5 ${strong ? "font-semibold" : ""}`}>{label}</td>
      <td className="px-4 py-2.5 text-right">
        <Figure
          parts={splitCop(value)}
          className={`${strong ? "font-semibold" : ""} ${muted ? "text-muted-foreground" : ""}`}
        />
      </td>
    </tr>
  );
}

function RowText({ label, text }: { label: string; text: string }) {
  return (
    <tr className="border-b border-rule last:border-0">
      <td className="px-4 py-2.5">{label}</td>
      <td className="num px-4 py-2.5 text-right">{text}</td>
    </tr>
  );
}
