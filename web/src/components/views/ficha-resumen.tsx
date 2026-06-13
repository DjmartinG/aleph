import type { ProjectDetail, Pyg, Results, Urbanistico } from "@/lib/api";
import { fmtCop, fmtInt, fmtPct, splitCop, splitPct } from "@/lib/format";
import { StatPanel, type StatItem } from "@/components/stat";
import { Figure } from "@/components/figure";
import { ChecksBadge } from "@/components/checks-badge";
import { SectionTitle } from "@/components/section-title";

/** "TIR proyecto · proyecto (desapalancada)" → ["TIR proyecto", "proyecto (desapalancada)"]. */
function splitLabel(s: string): [string, string] {
  const i = s.indexOf(" · ");
  return i >= 0 ? [s.slice(0, i), s.slice(i + 3)] : [s, ""];
}

export function FichaResumen({ project, results }: { project: ProjectDetail; results: Results }) {
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
    <div>
      <StatPanel items={stats} />

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
        <Ledger pyg={pyg} margen={ind.margen_oper} />
      </section>

      {project.urbanistico ? (
        <section className="mt-9">
          <SectionTitle right="áreas e índices">Ficha técnica</SectionTitle>
          <FichaTecnica u={project.urbanistico} />
        </section>
      ) : null}
    </div>
  );
}

/** Precio/costo por m² (valor en COP) → "$X.XM" (millones COP por m²). */
function fmtPorM2(v: number | null): string {
  if (v === null || v === undefined || !isFinite(v)) return "—";
  return `$${(v / 1_000_000).toFixed(2)}M`;
}

function num2(v: number | null): string {
  return v === null || v === undefined || !isFinite(v) ? "—" : v.toFixed(2);
}

function FichaTecnica({ u }: { u: Urbanistico }) {
  return (
    <div className="grid gap-4 sm:grid-cols-3">
      <TechBlock title="Áreas">
        <TechRow label="Lote bruto" value={u.lote_bruta != null ? `${fmtInt(u.lote_bruta)} m²` : "—"} />
        <TechRow label="Lote útil" value={u.lote_util != null ? `${fmtInt(u.lote_util)} m²` : "—"} />
        <TechRow label="Área construida" value={u.area_construida != null ? `${fmtInt(u.area_construida)} m²` : "—"} />
        <TechRow label="Área vendible" value={u.area_vendible != null ? `${fmtInt(u.area_vendible)} m²` : "—"} />
      </TechBlock>
      <TechBlock title="Índices">
        <TechRow label="Ratio bruta / útil" value={num2(u.ratio_bruta_util)} />
        <TechRow label="Índice de construcción" value={num2(u.indice_construccion)} />
        <TechRow label="Aprovechamiento" value={fmtPct(u.aprovechamiento)} />
        <TechRow label="Densidad" value={u.densidad_und_ha != null ? `${fmtInt(u.densidad_und_ha)} und/ha` : "—"} />
      </TechBlock>
      <TechBlock title="Por m²">
        <TechRow label="Precio de venta / m²" value={fmtPorM2(u.precio_m2_vend)} />
        <TechRow label="Costo directo / m²" value={fmtPorM2(u.costo_dir_m2_const)} />
      </TechBlock>
    </div>
  );
}

function TechBlock({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-[var(--radius-data)] border bg-card p-4">
      <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">{title}</div>
      <dl className="divide-y divide-[var(--rule)]">{children}</dl>
    </div>
  );
}

function TechRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 py-1.5">
      <dt className="text-sm text-muted-foreground">{label}</dt>
      <dd className="num text-sm tabular-nums text-foreground/90">{value}</dd>
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

function Ledger({ pyg, margen }: { pyg: Pyg; margen: number | null }) {
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
