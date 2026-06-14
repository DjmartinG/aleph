"use client";

import { Fragment, useState } from "react";
import type { ProjectDetail, Results, Sensitivity, Schedule, Wacc, Vehiculos } from "@/lib/api";
import { cn } from "@/lib/utils";
import { FichaResumen } from "@/components/views/ficha-resumen";
import { FlujoView } from "@/components/views/ficha-flujo";
import { CronogramaView } from "@/components/views/ficha-cronograma";
import { WaccView } from "@/components/views/ficha-wacc";
import { SensibilidadView } from "@/components/views/ficha-sensibilidad";
import { VehiculosView } from "@/components/views/ficha-vehiculos";
import { PanelControl } from "@/components/views/panel-control";

type Tab = "resumen" | "flujo" | "cronograma" | "capital" | "sensibilidad" | "vehiculos" | "control";

const TABS: { key: Tab; label: string }[] = [
  { key: "resumen", label: "Resumen" },
  { key: "flujo", label: "Flujo" },
  { key: "cronograma", label: "Cronograma" },
  { key: "capital", label: "Costo de capital" },
  { key: "sensibilidad", label: "Sensibilidad" },
  { key: "vehiculos", label: "Vehículos" },
  { key: "control", label: "Simulador" },
];

export function FichaTabs({
  project,
  results,
  sensitivity,
  schedule,
  wacc,
  vehiculos,
}: {
  project: ProjectDetail;
  results: Results;
  sensitivity: Sensitivity | null;
  schedule: Schedule | null;
  wacc: Wacc | null;
  vehiculos: Vehiculos | null;
}) {
  const [tab, setTab] = useState<Tab>("resumen");

  return (
    <div>
      <div role="tablist" className="mb-6 flex gap-1 overflow-x-auto border-b [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {TABS.map((t, i) => {
          const active = tab === t.key;
          return (
            <Fragment key={t.key}>
              {/* Separador: Resumen es el lienzo; el resto son capas para "profundizar". */}
              {i === 1 ? (
                <span aria-hidden className="mx-1 my-2 w-px shrink-0 self-stretch bg-rule" />
              ) : null}
              <button
                type="button"
                role="tab"
                aria-selected={active}
                onClick={() => setTab(t.key)}
                className={cn(
                  "relative -mb-px whitespace-nowrap px-3 py-2 text-sm font-medium transition-[color,transform] [transition-duration:var(--dur-1)] [transition-timing-function:var(--ease-out)] active:scale-[0.97]",
                  active ? "text-foreground" : "text-muted-foreground hover:text-foreground",
                )}
              >
                {t.label}
                {active ? (
                  <span className="absolute inset-x-0 -bottom-px h-0.5 rounded-full bg-primary" aria-hidden />
                ) : null}
              </button>
            </Fragment>
          );
        })}
      </div>

      {tab === "resumen" ? <FichaResumen project={project} results={results} /> : null}
      {tab === "flujo" ? <FlujoView flujo={results.flujo.apalancado} /> : null}
      {tab === "cronograma" ? (
        schedule ? (
          <CronogramaView schedule={schedule} />
        ) : (
          <div className="rounded-[var(--radius-data)] border border-dashed bg-card p-10 text-center text-sm text-muted-foreground">
            Cronograma no disponible.
          </div>
        )
      ) : null}
      {tab === "capital" ? (
        wacc?.disponible ? (
          <WaccView wacc={wacc} />
        ) : (
          <div className="rounded-[var(--radius-data)] border border-dashed bg-card p-10 text-center text-sm text-muted-foreground">
            Costo de capital no disponible.
          </div>
        )
      ) : null}
      {tab === "sensibilidad" ? (
        sensitivity ? (
          <SensibilidadView sensitivity={sensitivity} slug={project.id} />
        ) : (
          <div className="rounded-[var(--radius-data)] border border-dashed bg-card p-10 text-center text-sm text-muted-foreground">
            Sensibilidad no disponible.
          </div>
        )
      ) : null}
      {tab === "vehiculos" ? (
        vehiculos ? (
          <VehiculosView data={vehiculos} />
        ) : (
          <div className="rounded-[var(--radius-data)] border border-dashed bg-card p-10 text-center text-sm text-muted-foreground">
            Comparador de vehículos no disponible.
          </div>
        )
      ) : null}
      {tab === "control" ? <PanelControl slug={project.id} /> : null}
    </div>
  );
}
