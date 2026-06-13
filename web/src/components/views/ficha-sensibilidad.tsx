"use client";

import type { Sensitivity } from "@/lib/api";
import { SectionTitle } from "@/components/section-title";
import { ScenarioCompare } from "@/components/charts/scenario-compare";
import { TornadoChart } from "@/components/charts/tornado-chart";
import { Heatmap2D } from "@/components/charts/heatmap-2d";
import { MonteCarlo } from "@/components/views/monte-carlo";

export function SensibilidadView({
  sensitivity,
  slug,
}: {
  sensitivity: Sensitivity;
  slug: string;
}) {
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

      <section>
        <SectionTitle right="margen operativo %">Sensibilidad 2D · precio × costo</SectionTitle>
        <div className="rounded-[var(--radius-data)] border bg-card p-4">
          <Heatmap2D
            pasosPrecio={sensitivity.matriz_2d.pasos_precio}
            pasosCosto={sensitivity.matriz_2d.pasos_costo}
            matriz={sensitivity.matriz_2d.margen_pct}
          />
        </div>
        <p className="mt-2 text-xs text-muted-foreground">
          Margen operativo (%) al variar precio y costo directo. La celda central (0 / 0) es la base;
          teal = mayor margen, ámbar/rojo = margen negativo.
        </p>
      </section>

      <section>
        <SectionTitle right="distribución probabilística">Monte Carlo</SectionTitle>
        <MonteCarlo slug={slug} />
      </section>
    </div>
  );
}
