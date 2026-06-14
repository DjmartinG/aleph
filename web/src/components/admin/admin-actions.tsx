"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { Trash2, Loader2, AlertTriangle, ShieldAlert, BadgeCheck } from "lucide-react";
import { eliminarProyecto, marcarProyectoReal } from "@/lib/actions";

/**
 * Acciones de administrador sobre un proyecto: marcar datos reales/ilustrativos y ELIMINAR (borrado
 * duro, irreversible). El gate REAL lo hace el API (revalida el JWT + exige rol admin); este componente
 * solo se renderiza para admins (la ficha lo decide con isAdminUser). Confirmación de borrado in-place
 * (escribir el nombre), sin modal.
 */
export function AdminActions({ slug, nombre, esReal }: { slug: string; nombre: string; esReal: boolean }) {
  const router = useRouter();

  // --- Marcar real / ilustrativo ---
  const [togglePending, startToggle] = useTransition();
  const [toggleErr, setToggleErr] = useState<string | null>(null);
  function toggleReal() {
    setToggleErr(null);
    startToggle(async () => {
      const res = await marcarProyectoReal(slug, !esReal);
      if (res.ok) router.refresh();
      else setToggleErr(res.message);
    });
  }

  // --- Eliminar ---
  const [open, setOpen] = useState(false);
  const [confirmText, setConfirmText] = useState("");
  const [delErr, setDelErr] = useState<string | null>(null);
  const [delPending, startDel] = useTransition();
  const canDelete = confirmText.trim() === nombre.trim();
  function reset() {
    setOpen(false);
    setConfirmText("");
    setDelErr(null);
  }
  function del() {
    if (!canDelete) return;
    setDelErr(null);
    startDel(async () => {
      const res = await eliminarProyecto(slug);
      if (res.ok) router.push("/");
      else setDelErr(res.message);
    });
  }

  return (
    <section className="mt-10">
      <div className="mb-3 flex items-center gap-2">
        <ShieldAlert className="size-4 text-muted-foreground" aria-hidden />
        <h2 className="text-sm font-medium">Zona de administración</h2>
        <span className="text-xs text-muted-foreground">solo administradores</span>
      </div>

      {/* Tipo de datos (no destructivo) */}
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3 rounded-[var(--radius-data)] border bg-card p-4">
        <div className="flex items-center gap-2">
          <BadgeCheck className={esReal ? "size-4 text-success" : "size-4 text-muted-foreground"} aria-hidden />
          <div>
            <div className="text-sm font-medium">
              Tipo de datos: {esReal ? "reales" : "ilustrativos"}
            </div>
            <div className="text-xs text-muted-foreground">
              Controla la etiqueta del proyecto (no afecta las cifras).
            </div>
          </div>
        </div>
        <button
          type="button"
          onClick={toggleReal}
          disabled={togglePending}
          className="inline-flex items-center gap-1.5 rounded-[var(--radius-data)] border px-3 py-1.5 text-sm font-medium transition-colors [transition-timing-function:var(--ease-out)] hover:bg-accent disabled:opacity-60"
        >
          {togglePending ? <Loader2 className="size-4 animate-spin" aria-hidden /> : null}
          {esReal ? "Marcar como ilustrativo" : "Marcar como real"}
        </button>
      </div>
      {toggleErr ? <p className="mb-3 text-sm text-danger">{toggleErr}</p> : null}

      {/* Eliminar (destructivo) */}
      <div className="rounded-[var(--radius-data)] border border-danger/30 bg-danger/5 p-4">
        {!open ? (
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="text-sm font-medium">Eliminar proyecto</div>
              <div className="text-xs text-muted-foreground">
                Borra el proyecto y todos sus escenarios. Irreversible.
              </div>
            </div>
            <button
              type="button"
              onClick={() => setOpen(true)}
              className="inline-flex items-center gap-1.5 rounded-[var(--radius-data)] border border-danger/40 px-3 py-1.5 text-sm font-medium text-danger transition-colors [transition-timing-function:var(--ease-out)] hover:bg-danger/10"
            >
              <Trash2 className="size-4" aria-hidden /> Eliminar
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex items-start gap-2 text-sm text-danger">
              <AlertTriangle className="mt-0.5 size-4 shrink-0" aria-hidden />
              <span>
                Esto borra <strong>{nombre}</strong> y todos sus escenarios de forma permanente. Para
                confirmar, escribe el nombre del proyecto.
              </span>
            </div>
            <input
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)}
              placeholder={nombre}
              aria-label="Confirma escribiendo el nombre del proyecto"
              autoFocus
              className="w-full rounded-[var(--radius-data)] border bg-card px-2.5 py-1.5 text-sm text-foreground outline-none transition-colors [transition-timing-function:var(--ease-out)] focus:border-danger placeholder:text-muted-foreground/40"
            />
            {delErr ? <p className="text-sm text-danger">{delErr}</p> : null}
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={reset}
                disabled={delPending}
                className="rounded-[var(--radius-data)] px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground disabled:opacity-60"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={del}
                disabled={!canDelete || delPending}
                className="inline-flex items-center gap-1.5 rounded-[var(--radius-data)] bg-destructive px-3 py-1.5 text-sm font-medium text-destructive-foreground transition-[opacity,transform] [transition-timing-function:var(--ease-out)] hover:opacity-90 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
              >
                {delPending ? <Loader2 className="size-4 animate-spin" aria-hidden /> : <Trash2 className="size-4" aria-hidden />}
                Eliminar definitivamente
              </button>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
