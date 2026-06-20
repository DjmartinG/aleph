"use client";

import { createContext, useContext, useEffect, useState } from "react";

/**
 * Contexto del HEADER PERMANENTE (constitución §diseño: "header permanente con Proyecto · Fase ·
 * Escenario · estado de Cuadres"). La ficha de proyecto publica aquí su contexto y el Topbar lo
 * consume, así la barra superior refleja el proyecto activo desde cualquier pestaña/módulo. En las
 * demás rutas queda `null` y el Topbar muestra solo el breadcrumb (comportamiento previo).
 *
 * Honestidad de datos: solo se publica lo que el motor expone de verdad (Fase, base del escenario,
 * estado de los checks de cuadre). NO se inventan "vN" ni "corte de datos" (el API de lectura aún no
 * expone versión/estado del escenario ni hay actuals para un corte).
 */
export interface ProjectHeader {
  nombre: string;
  estado: string;
  /** Base del escenario, honesta (del motor): "base auditada (fiducia)" / "base · modelo aprobado". */
  escenario: string;
  /** Resumen de los checks de cuadre del proyecto para el badge persistente; null si no hay. */
  checks: { allOk: boolean; total: number; nFail: number } | null;
}

interface Ctx {
  header: ProjectHeader | null;
  setHeader: (h: ProjectHeader | null) => void;
}

const ProjectHeaderCtx = createContext<Ctx | null>(null);

export function ProjectHeaderProvider({ children }: { children: React.ReactNode }) {
  const [header, setHeader] = useState<ProjectHeader | null>(null);
  return (
    <ProjectHeaderCtx.Provider value={{ header, setHeader }}>{children}</ProjectHeaderCtx.Provider>
  );
}

/** El Topbar lo consume. Fuera del provider devuelve null (no rompe). */
export function useProjectHeader(): ProjectHeader | null {
  return useContext(ProjectHeaderCtx)?.header ?? null;
}

/**
 * Componente sin render: la ficha de proyecto (Server Component) lo monta para publicar su contexto
 * al Topbar; al navegar fuera se desmonta y lo limpia. Recibe primitivos para deps estables del
 * efecto (`setHeader` de useState es referencialmente estable → sin bucle).
 */
export function SetProjectHeader({
  nombre,
  estado,
  escenario,
  checksAllOk,
  checksTotal,
  checksFail,
}: {
  nombre: string;
  estado: string;
  escenario: string;
  checksAllOk: boolean;
  checksTotal: number;
  checksFail: number;
}) {
  const setHeader = useContext(ProjectHeaderCtx)?.setHeader;
  useEffect(() => {
    if (!setHeader) return;
    setHeader({
      nombre,
      estado,
      escenario,
      checks: checksTotal > 0 ? { allOk: checksAllOk, total: checksTotal, nFail: checksFail } : null,
    });
    return () => setHeader(null);
  }, [setHeader, nombre, estado, escenario, checksAllOk, checksTotal, checksFail]);
  return null;
}
