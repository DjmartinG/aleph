"use client";

import { useState } from "react";
import type { ProjectDetail, Results, Sensitivity } from "@/lib/api";
import { cn } from "@/lib/utils";
import { FichaResumen } from "@/components/views/ficha-resumen";
import { FlujoView } from "@/components/views/ficha-flujo";
import { SensibilidadView } from "@/components/views/ficha-sensibilidad";

type Tab = "resumen" | "flujo" | "sensibilidad";

const TABS: { key: Tab; label: string }[] = [
  { key: "resumen", label: "Resumen" },
  { key: "flujo", label: "Flujo" },
  { key: "sensibilidad", label: "Sensibilidad" },
];

export function FichaTabs({
  project,
  results,
  sensitivity,
}: {
  project: ProjectDetail;
  results: Results;
  sensitivity: Sensitivity | null;
}) {
  const [tab, setTab] = useState<Tab>("resumen");

  return (
    <div>
      <div role="tablist" className="mb-6 flex gap-1 border-b">
        {TABS.map((t) => {
          const active = tab === t.key;
          return (
            <button
              key={t.key}
              type="button"
              role="tab"
              aria-selected={active}
              onClick={() => setTab(t.key)}
              className={cn(
                "relative -mb-px px-3 py-2 text-sm font-medium transition-colors [transition-timing-function:var(--ease-out)]",
                active ? "text-foreground" : "text-muted-foreground hover:text-foreground",
              )}
            >
              {t.label}
              {active ? (
                <span className="absolute inset-x-0 -bottom-px h-0.5 rounded-full bg-primary" aria-hidden />
              ) : null}
            </button>
          );
        })}
      </div>

      {tab === "resumen" ? <FichaResumen project={project} results={results} /> : null}
      {tab === "flujo" ? <FlujoView flujo={results.flujo.apalancado} /> : null}
      {tab === "sensibilidad" ? (
        sensitivity ? (
          <SensibilidadView sensitivity={sensitivity} />
        ) : (
          <div className="rounded-[var(--radius-data)] border border-dashed bg-card p-10 text-center text-sm text-muted-foreground">
            Sensibilidad no disponible.
          </div>
        )
      ) : null}
    </div>
  );
}
