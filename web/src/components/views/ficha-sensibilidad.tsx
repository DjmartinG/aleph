"use client";

import type { Sensitivity } from "@/lib/api";
import { SectionTitle } from "@/components/section-title";
import { ScenarioCompare } from "@/components/charts/scenario-compare";
import { TornadoChart } from "@/components/charts/tornado-chart";

export function SensibilidadView({ sensitivity }: { sensitivity: Sensitivity }) {
  return (
    <div className="space-y-9">
      <section>
        <SectionTitle right="utilidad operativa">Escenarios</SectionTitle>
        <div className="rounded-[var(--radius-data)] border bg-card p-4">
          <ScenarioCompare escenarios={sensitivity.escenarios} />
        </div>
      </section>

      <section>
        <SectionTitle right="impacto en la utilidad">Tornado de sensibilidad</SectionTitle>
        <div className="rounded-[var(--radius-data)] border bg-card p-4">
          <TornadoChart tornado={sensitivity.tornado} />
        </div>
        <p className="mt-2 text-xs text-muted-foreground">
          Cuánto cambia la utilidad operativa si cada variable sube o baja 10%. Ámbar = a la baja,
          teal = al alza (eje en mil M).
        </p>
      </section>
    </div>
  );
}
