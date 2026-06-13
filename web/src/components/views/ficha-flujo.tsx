"use client";

import { useMemo, useState } from "react";
import type { FlujoApalancado } from "@/lib/api";
import { fmtCop, fmtInt } from "@/lib/format";
import { CashFlowChart, type CashPoint } from "@/components/charts/cash-flow-chart";
import { cn } from "@/lib/utils";

type Modo = "proyecto" | "inversionista";

/** Último índice con magnitud significativa (para recortar la cola de ceros). */
function lastSignificant(arr: number[]): number {
  let last = 0;
  for (let i = 0; i < arr.length; i++) if (Math.abs(arr[i]) > 1) last = i;
  return last;
}

export function FlujoView({ flujo }: { flujo: FlujoApalancado }) {
  const [modo, setModo] = useState<Modo>("proyecto");

  const { data, maxExposure } = useMemo(() => {
    const monthly = modo === "proyecto" ? flujo.operativo : flujo.flujo_equity;
    const end = Math.min(
      monthly.length,
      Math.max(lastSignificant(monthly), lastSignificant(flujo.saldo_credito)) + 4,
    );
    const out: CashPoint[] = [];
    let run = 0;
    for (let m = 0; m < end; m++) {
      run += monthly[m] ?? 0;
      out.push({ m, acum: run, credito: flujo.saldo_credito[m] ?? 0 });
    }
    let minV = Infinity;
    let minM = -1;
    for (const p of out) {
      if (p.acum < minV) {
        minV = p.acum;
        minM = p.m;
      }
    }
    return {
      data: out,
      maxExposure: minM >= 0 && minV < 0 ? { m: minM, value: minV } : null,
    };
  }, [modo, flujo]);

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="inline-flex rounded-[var(--radius-data)] border bg-card p-0.5 text-sm">
          {(["proyecto", "inversionista"] as Modo[]).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => setModo(m)}
              className={cn(
                "rounded-[3px] px-3 py-1 font-medium transition-colors [transition-timing-function:var(--ease-out)]",
                modo === m
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              {m === "proyecto" ? "Proyecto" : "Inversionista"}
            </button>
          ))}
        </div>
        <div className="flex flex-wrap gap-x-5 gap-y-1 text-xs text-muted-foreground">
          <span className="flex items-center gap-1.5">
            <span className="h-0.5 w-3.5 rounded bg-primary" />
            Caja acumulada
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-0.5 w-3.5 rounded bg-cg-amber" />
            Crédito
          </span>
          <span className="flex items-center gap-1.5">
            <span className="size-2 rounded-full bg-danger" />
            Exposición máx
          </span>
        </div>
      </div>

      <div className="rounded-[var(--radius-data)] border bg-card p-3">
        <CashFlowChart data={data} maxExposure={maxExposure} />
      </div>

      <div className="mt-4 grid grid-cols-2 gap-x-6 gap-y-3 rounded-[var(--radius-data)] border bg-card p-4 sm:grid-cols-4">
        <Mini
          label="Exposición máx"
          value={maxExposure ? fmtCop(maxExposure.value) : "—"}
          note={maxExposure ? `mes ${maxExposure.m + 1}` : "sin déficit"}
          danger={!!maxExposure}
        />
        <Mini label="Crédito máx" value={fmtCop(flujo.credito_max)} note="pico de saldo" />
        <Mini label="Aportes socio" value={fmtCop(flujo.aportes_total)} note="equity" />
        <Mini
          label="Payback"
          value={flujo.payback_mes != null ? `${fmtInt(flujo.payback_mes)} m` : "n/d"}
          note="recuperación"
        />
      </div>
    </div>
  );
}

function Mini({
  label,
  value,
  note,
  danger,
}: {
  label: string;
  value: string;
  note?: string;
  danger?: boolean;
}) {
  return (
    <div>
      <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className={cn("num mt-0.5 text-base font-semibold", danger && "text-danger")}>{value}</div>
      {note ? <div className="text-[0.7rem] text-muted-foreground/80">{note}</div> : null}
    </div>
  );
}
