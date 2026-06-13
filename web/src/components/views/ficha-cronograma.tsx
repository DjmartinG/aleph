"use client";

import { useMemo } from "react";
import type { Schedule } from "@/lib/api";
import { fmtCop, fmtInt } from "@/lib/format";
import { monthLabel } from "@/lib/timeline";
import { GanttChart } from "@/components/charts/gantt-chart";
import { AbsorptionChart } from "@/components/charts/absorption-chart";
import { RecaudoChart } from "@/components/charts/recaudo-chart";

export function CronogramaView({ schedule }: { schedule: Schedule }) {
  const s = schedule;
  const kpis = useMemo(() => {
    const ventasMeses = s.absorcion.ventas.filter((v) => v > 0).length;
    const firstVenta = s.absorcion.ventas.findIndex((v) => v > 0);
    let lastEntrega = -1;
    for (let i = 0; i < s.absorcion.entregas.length; i++) if (s.absorcion.entregas[i] > 0) lastEntrega = i;
    const recaudoTotal = s.recaudo.total.reduce((a, b) => a + b, 0);
    return { ventasMeses, firstVenta, lastEntrega, recaudoTotal };
  }, [s]);

  if (!s.etapas.length) {
    return (
      <div className="rounded-[var(--radius-data)] border border-dashed bg-card p-10 text-center text-sm text-muted-foreground">
        Sin cronograma para este proyecto (no tiene etapas con fechas).
      </div>
    );
  }

  return (
    <div className="space-y-9">
      <div className="grid grid-cols-2 gap-x-6 gap-y-3 rounded-[var(--radius-data)] border bg-card p-4 sm:grid-cols-4">
        <Mini label="Unidades" value={fmtInt(s.unidades_total)} note={`${s.etapas.length} etapas`} />
        <Mini
          label="Inicio ventas"
          value={kpis.firstVenta >= 0 ? monthLabel(s.base_date, kpis.firstVenta) : "—"}
          note="primera venta"
        />
        <Mini label="Meses con ventas" value={fmtInt(kpis.ventasMeses)} note="ritmo de absorción" />
        <Mini label="Recaudo total" value={fmtCop(kpis.recaudoTotal)} note="separ. + CI + subrog." />
      </div>

      <Section
        title="Cronograma por etapa"
        legend={
          <>
            <Swatch color="var(--primary)" label="Ventas (IV→FV)" />
            <Ring label="Equilibrio" />
            <Swatch color="var(--cg-amber)" label="Construcción (IC→FC)" />
          </>
        }
      >
        <GanttChart etapas={s.etapas} horizonte={s.horizonte} baseDate={s.base_date} />
      </Section>

      <Section
        title="Absorción de ventas"
        legend={
          <>
            <Swatch color="var(--primary)" faint label="Unidades / mes" />
            <LineSw label="Acumulado" />
          </>
        }
      >
        <AbsorptionChart
          ventas={s.absorcion.ventas}
          acum={s.absorcion.acum_ventas}
          baseDate={s.base_date}
          total={s.unidades_total}
        />
      </Section>

      <Section
        title="Recaudo mensual"
        subtitle="miles de millones COP"
        legend={
          <>
            <Swatch color="var(--primary)" faint label="Subrogación" />
            <Swatch color="var(--muted-foreground)" faint label="Cuota inicial" />
            <Swatch color="var(--cg-amber)" faint label="Separación" />
          </>
        }
      >
        <RecaudoChart
          separacion={s.recaudo.separacion}
          cuotaInicial={s.recaudo.cuota_inicial}
          subrogacion={s.recaudo.subrogacion}
          baseDate={s.base_date}
        />
      </Section>
    </div>
  );
}

function Section({
  title,
  subtitle,
  legend,
  children,
}: {
  title: string;
  subtitle?: string;
  legend?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section>
      <div className="mb-3 flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <h3 className="text-sm font-semibold tracking-tight">
          {title}
          {subtitle ? <span className="ml-2 font-normal text-muted-foreground">· {subtitle}</span> : null}
        </h3>
        {legend ? <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">{legend}</div> : null}
      </div>
      <div className="rounded-[var(--radius-data)] border bg-card p-3">{children}</div>
    </section>
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

function Swatch({ color, label, faint }: { color: string; label: string; faint?: boolean }) {
  return (
    <span className="flex items-center gap-1.5">
      <span className="size-2.5 rounded-[2px]" style={{ background: color, opacity: faint ? 0.45 : 0.85 }} />
      {label}
    </span>
  );
}

function LineSw({ label }: { label: string }) {
  return (
    <span className="flex items-center gap-1.5">
      <span className="h-0.5 w-3.5 rounded bg-primary" />
      {label}
    </span>
  );
}

function Ring({ label }: { label: string }) {
  return (
    <span className="flex items-center gap-1.5">
      <span className="size-2.5 rounded-full border-[1.5px] border-primary bg-card" />
      {label}
    </span>
  );
}
