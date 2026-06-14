"use client";

import { useEffect, useRef, useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { MoreHorizontal, Trash2, Loader2, AlertTriangle, BadgeCheck } from "lucide-react";
import { eliminarProyecto, marcarProyectoReal } from "@/lib/actions";

/**
 * Menú de administración (M7): el "⋯" del header. Esconde las acciones admin (marcar real / ELIMINAR)
 * fuera del lienzo de decisión. Solo se renderiza para admins (la ficha lo decide con isAdminUser; el
 * gate REAL lo hace el API con el rol de Entra). Borrado con confirmación escribiendo el nombre.
 */
export function AdminMenu({ slug, nombre, esReal }: { slug: string; nombre: string; esReal: boolean }) {
  const router = useRouter();
  const ref = useRef<HTMLDivElement>(null);
  const [menuOpen, setMenuOpen] = useState(false);

  const [togglePending, startToggle] = useTransition();
  const [toggleErr, setToggleErr] = useState<string | null>(null);

  const [confirming, setConfirming] = useState(false);
  const [confirmText, setConfirmText] = useState("");
  const [delErr, setDelErr] = useState<string | null>(null);
  const [delPending, startDel] = useTransition();
  const canDelete = confirmText.trim() === nombre.trim();

  useEffect(() => {
    if (!menuOpen) return;
    function onDown(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) close();
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") close();
    }
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  });

  function close() {
    setMenuOpen(false);
    setConfirming(false);
    setConfirmText("");
    setDelErr(null);
    setToggleErr(null);
  }

  function toggleReal() {
    setToggleErr(null);
    startToggle(async () => {
      const res = await marcarProyectoReal(slug, !esReal);
      if (res.ok) router.refresh();
      else setToggleErr(res.message);
    });
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
    <div ref={ref} className="relative">
      <button
        type="button"
        aria-label="Administración del proyecto"
        aria-haspopup="menu"
        aria-expanded={menuOpen}
        onClick={() => (menuOpen ? close() : setMenuOpen(true))}
        className="inline-flex size-9 items-center justify-center rounded-[var(--radius-data)] border text-muted-foreground transition-[color,background-color,transform] [transition-duration:var(--dur-1)] [transition-timing-function:var(--ease-out)] hover:bg-accent hover:text-foreground active:scale-95"
      >
        <MoreHorizontal className="size-4" aria-hidden />
      </button>

      {menuOpen ? (
        <div
          role="menu"
          className="pop-in absolute right-0 z-20 mt-1.5 w-72 origin-top-right rounded-[var(--radius-data)] border bg-card p-1.5 shadow-[0_4px_16px_-4px_var(--shadow-teal,rgba(14,94,89,0.18))]"
        >
          <div className="px-2 py-1 text-[0.7rem] font-medium uppercase tracking-wide text-muted-foreground">
            Administración
          </div>

          {/* Marcar real / ilustrativo (no destructivo) */}
          <button
            type="button"
            role="menuitem"
            onClick={toggleReal}
            disabled={togglePending}
            className="flex w-full items-center gap-2 rounded-[var(--radius-data)] px-2 py-1.5 text-left text-sm transition-colors hover:bg-accent disabled:opacity-60"
          >
            {togglePending ? (
              <Loader2 className="size-4 animate-spin text-muted-foreground" aria-hidden />
            ) : (
              <BadgeCheck className={esReal ? "size-4 text-success" : "size-4 text-muted-foreground"} aria-hidden />
            )}
            {esReal ? "Marcar como ilustrativo" : "Marcar como real"}
          </button>
          {toggleErr ? <p className="px-2 py-1 text-xs text-danger">{toggleErr}</p> : null}

          <div className="my-1 border-t" />

          {/* Eliminar (destructivo) */}
          {!confirming ? (
            <button
              type="button"
              role="menuitem"
              onClick={() => setConfirming(true)}
              className="flex w-full items-center gap-2 rounded-[var(--radius-data)] px-2 py-1.5 text-left text-sm text-danger transition-colors hover:bg-danger/10"
            >
              <Trash2 className="size-4" aria-hidden /> Eliminar proyecto
            </button>
          ) : (
            <div className="space-y-2 rounded-[var(--radius-data)] border border-danger/30 bg-danger/5 p-2.5">
              <div className="flex items-start gap-1.5 text-xs text-danger">
                <AlertTriangle className="mt-0.5 size-3.5 shrink-0" aria-hidden />
                <span>
                  Borra <strong>{nombre}</strong> y sus escenarios. Irreversible. Escribe el nombre para confirmar.
                </span>
              </div>
              <input
                value={confirmText}
                onChange={(e) => setConfirmText(e.target.value)}
                placeholder={nombre}
                aria-label="Confirma escribiendo el nombre del proyecto"
                autoFocus
                className="w-full rounded-[var(--radius-data)] border bg-background px-2 py-1.5 text-sm outline-none transition-colors focus:border-danger placeholder:text-muted-foreground/40"
              />
              {delErr ? <p className="text-xs text-danger">{delErr}</p> : null}
              <div className="flex justify-end gap-1.5">
                <button
                  type="button"
                  onClick={() => { setConfirming(false); setConfirmText(""); setDelErr(null); }}
                  disabled={delPending}
                  className="rounded-[var(--radius-data)] px-2.5 py-1 text-sm text-muted-foreground transition-colors hover:text-foreground disabled:opacity-60"
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  onClick={del}
                  disabled={!canDelete || delPending}
                  className="inline-flex items-center gap-1.5 rounded-[var(--radius-data)] bg-destructive px-2.5 py-1 text-sm font-medium text-destructive-foreground transition-[opacity,transform] [transition-timing-function:var(--ease-out)] hover:opacity-90 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {delPending ? <Loader2 className="size-4 animate-spin" aria-hidden /> : <Trash2 className="size-4" aria-hidden />}
                  Eliminar
                </button>
              </div>
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}
