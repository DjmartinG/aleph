"use client";

import type { Wacc } from "@/lib/api";
import { fmtPct, splitPct } from "@/lib/format";

function fmtNum(x: number | null | undefined): string {
  return x === null || x === undefined || !isFinite(x) ? "—" : x.toFixed(2);
}

export function WaccView({ wacc }: { wacc: Wacc }) {
  const w = wacc;
  if (!w.disponible) {
    return (
      <div className="rounded-[var(--radius-data)] border border-dashed bg-card p-10 text-center text-sm text-muted-foreground">
        Este proyecto no tiene parámetros de costo de capital (WACC).
      </div>
    );
  }

  const [waccMag, waccUnit] = splitPct(w.wacc ?? null);
  const inp = w.inputs;

  return (
    <div className="space-y-9">
      {/* KPIs */}
      <div className="grid grid-cols-2 gap-x-6 gap-y-4 rounded-[var(--radius-data)] border bg-card p-5 sm:grid-cols-4">
        <div>
          <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">WACC</div>
          <div className="mt-1 flex items-baseline gap-1">
            <span className="num text-3xl font-semibold tracking-tight">{waccMag}</span>
            <span className="text-base text-muted-foreground">{waccUnit}</span>
          </div>
          <div className="text-[0.7rem] text-muted-foreground/80">COP · build-up CAPM</div>
        </div>
        <Mini label="Ke (equity)" value={fmtPct(w.ke_cop)} note="recursos propios" />
        <Mini label="Kd (después imp.)" value={fmtPct(w.kd_despues_imp)} note={`escudo fiscal ${fmtPct(w.t_col, 0)}`} />
        <Mini label="TIO" value={fmtPct(w.tio ?? null)} note="tasa mínima (hurdle)" />
      </div>

      {/* Composición del WACC */}
      <section>
        <Head title="Composición del WACC" right={`E ${fmtPct(w.we, 0)} · D ${fmtPct(w.wd, 0)}`} />
        <CompositionBar eq={w.aporte_equity ?? 0} debt={w.aporte_deuda ?? 0} total={w.wacc ?? 0} />
      </section>

      {/* Build-up (cadena) */}
      <section>
        <Head title="Construcción del costo de capital" subtitle="metodología Damodaran · mercado emergente" />
        <div className="grid gap-4 lg:grid-cols-3">
          <Block title="Beta (CAPM)">
            <Step label="Beta US (apalancada)" value={fmtNum(w.beta_us)} />
            <Step label="Beta de la deuda" value={fmtNum(w.beta_d)} />
            <Step label="Beta desapalancada" value={fmtNum(w.beta_u)} op="desapalancar" />
            <Step label="Beta reapalancada · Colombia" value={fmtNum(w.beta_l)} op="reapalancar" strong />
          </Block>
          <Block title="Ke · costo de equity">
            <Step label="Ke USD (CAPM)" value={fmtPct(w.ke_usd)} />
            <Step label="Riesgo país (EMBI)" value={fmtPct(w.rp)} op="+" />
            <Step label="Ke USD + EMBI" value={fmtPct(w.ke_usd_rp)} />
            <Step label="Paridad de inflación" value={fmtPct(w.rplp)} op="×" />
            <Step label="Ke COP" value={fmtPct(w.ke_cop)} strong />
          </Block>
          <Block title="Kd · costo de deuda">
            <Step label="Kd COP" value={fmtPct(w.kd_cop)} />
            <Step label="Escudo fiscal (1 − t)" value={fmtPct(1 - (w.t_col ?? 0), 0)} op="×" />
            <Step label="Kd después de impuestos" value={fmtPct(w.kd_despues_imp)} strong />
          </Block>
        </div>
      </section>

      {/* Supuestos */}
      {inp ? (
        <section>
          <Head title="Supuestos" />
          <div className="grid grid-cols-2 gap-x-6 gap-y-3 rounded-[var(--radius-data)] border bg-card p-4 sm:grid-cols-3 lg:grid-cols-6">
            <Sup label="Tasa libre de riesgo" value={fmtPct(inp.rf)} />
            <Sup label="Prima de mercado" value={fmtPct(inp.pm)} />
            <Sup label="Riesgo país (EMBI)" value={fmtPct(w.rp)} />
            <Sup label="Inflación CO / US" value={`${fmtPct(inp.inf_col, 1)} / ${fmtPct(inp.inf_us, 1)}`} />
            <Sup label="D/E US / Colombia" value={`${fmtNum(inp.de_us)} / ${fmtNum(inp.de_col)}`} />
            <Sup label="Impuesto US / Colombia" value={`${fmtPct(inp.tax_us, 0)} / ${fmtPct(inp.tax_col, 0)}`} />
          </div>
        </section>
      ) : null}
    </div>
  );
}

function CompositionBar({ eq, debt, total }: { eq: number; debt: number; total: number }) {
  const eqPct = total ? (eq / total) * 100 : 0;
  const debtPct = 100 - eqPct;
  return (
    <div className="rounded-[var(--radius-data)] border bg-card p-4">
      <div className="flex h-2.5 w-full overflow-hidden rounded-full">
        <div className="bg-primary" style={{ width: `${eqPct}%` }} />
        <div className="bg-cg-amber" style={{ width: `${debtPct}%` }} />
      </div>
      <div className="mt-3 flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1 text-sm">
        <span className="flex items-center gap-1.5 text-muted-foreground">
          <span className="size-2.5 rounded-[2px] bg-primary" /> Equity · E·Ke
          <span className="num ml-1 font-semibold text-foreground">{fmtPct(eq)}</span>
          <span className="text-xs">({Math.round(eqPct)}%)</span>
        </span>
        <span className="num text-base font-semibold">WACC {fmtPct(total)}</span>
        <span className="flex items-center gap-1.5 text-muted-foreground">
          <span className="size-2.5 rounded-[2px] bg-cg-amber" /> Deuda · D·Kd(1−t)
          <span className="num ml-1 font-semibold text-foreground">{fmtPct(debt)}</span>
          <span className="text-xs">({Math.round(debtPct)}%)</span>
        </span>
      </div>
    </div>
  );
}

function Block({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-[var(--radius-data)] border bg-card p-4">
      <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">{title}</div>
      <dl className="divide-y divide-[var(--rule)]">{children}</dl>
    </div>
  );
}

function Step({ label, value, op, strong }: { label: string; value: string; op?: string; strong?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-3 py-1.5">
      <dt className={strong ? "text-sm font-medium text-foreground" : "text-sm text-muted-foreground"}>
        {op ? <span className="mr-1.5 text-xs text-muted-foreground/70">{op}</span> : null}
        {label}
      </dt>
      <dd className={`num text-sm tabular-nums ${strong ? "font-semibold text-foreground" : "text-foreground/90"}`}>
        {value}
      </dd>
    </div>
  );
}

function Mini({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div>
      <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="num mt-1 text-xl font-semibold tracking-tight">{value}</div>
      {note ? <div className="text-[0.7rem] text-muted-foreground/80">{note}</div> : null}
    </div>
  );
}

function Sup({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-[0.7rem] uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="num mt-0.5 text-sm font-medium tabular-nums">{value}</div>
    </div>
  );
}

function Head({ title, subtitle, right }: { title: string; subtitle?: string; right?: string }) {
  return (
    <div className="mb-3 flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
      <h3 className="text-sm font-semibold tracking-tight">
        {title}
        {subtitle ? <span className="ml-2 font-normal text-muted-foreground">· {subtitle}</span> : null}
      </h3>
      {right ? <span className="num text-xs text-muted-foreground">{right}</span> : null}
    </div>
  );
}
