/**
 * Cliente tipado del API de ALEPH (`aleph_api`, FastAPI). Solo LECTURA.
 * Contrato §5. La API NO recalcula nada en el cliente: el motor produce las cifras, aquí se consumen.
 *
 * SERVER-ONLY: importa `auth()`/`redirect` (next/headers). Las páginas (Server Components) y el
 * Server Action de Monte Carlo lo usan; los client components solo importan los TIPOS (`import type`).
 *
 * Base URL: env `ALEPH_API_URL` (dev: http://localhost:8000 con la auth apagada).
 * Auth (config-driven, espeja al API): con `AUTH_MICROSOFT_ENTRA_ID_ID` cada `/v1/*` lleva el
 * access_token de Entra como `Authorization: Bearer`; sin esa env (dev local) no se adjunta nada.
 */

import { auth } from "@/auth";
import { redirect } from "next/navigation";

export const API_BASE = process.env.ALEPH_API_URL ?? "http://localhost:8000";

/** Auth encendida sólo si Entra está configurado (mismo gate que el proxy y el provider). */
const AUTH_ON = !!process.env.AUTH_MICROSOFT_ENTRA_ID_ID;

/** Adjunta el access_token de Entra (de la sesión NextAuth) si la auth está encendida. */
async function authHeaders(): Promise<Record<string, string>> {
  if (!AUTH_ON) return {};
  const session = await auth();
  const token = session?.apiToken;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/**
 * `fetch` contra el API con el Bearer adjunto y manejo central de 401/403.
 * En prod (auth on), un 401/403 = token expirado/invalidado → redirige a `/login?reason=expired`
 * (pantalla clara "sesión expirada, vuelve a entrar"). En dev (auth off) lanza un Error normal.
 */
async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = {
    ...(init.headers as Record<string, string> | undefined),
    ...(await authHeaders()),
  };
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store", ...init, headers });
  if (res.status === 401 || res.status === 403) {
    if (AUTH_ON) redirect("/login?reason=expired");
    throw new Error(`API respondió ${res.status} (no autorizado) en ${path}`);
  }
  return res;
}

/** Estados del ciclo de vida (deben coincidir con `aleph_engine.config.ESTADOS`). */
export type Estado = "prefactibilidad" | "aprobado" | "construccion" | "entregado";

/** Consolidado del portafolio (números CRUDOS, en miles COP; el cliente formatea). */
export interface PortfolioConsolidado {
  n: number;
  unidades: number;
  ventas: number;
  util_oper: number;
  udi: number;
  vpn: number;
  margen: number;
  tir_ref: number | null;
  tir_eq: number | null;
  credito_max: number;
}

export interface FunnelStage {
  estado: Estado | string;
  label: string;
  count: number;
}

/** Un proyecto en el pipeline/embudo (de `portfolio.pipeline`). */
export interface ProjectItem {
  slug: string;
  nombre: string;
  estado: Estado | string;
  tir: number | null;
  vpn: number | null;
  ventas: number | null;
  /** Margen operativo (fracción). Para el mapa de valor (TIR × margen). */
  margen: number | null;
  und: number;
  ubicacion: string;
  tipo: string;
}

export interface Portfolio {
  consolidado: PortfolioConsolidado;
  embudo: FunnelStage[];
  items: ProjectItem[];
}

/** GET /v1/portfolio. Sin caché (dato dinámico). Lanza Error con el status si la API falla. */
export async function getPortfolio(): Promise<Portfolio> {
  const res = await apiFetch(`/v1/portfolio`);
  if (!res.ok) {
    throw new Error(`API respondió ${res.status} al pedir /v1/portfolio`);
  }
  return res.json() as Promise<Portfolio>;
}

// ---------- Ficha de proyecto + resultados ----------

export interface Meta {
  nombre: string;
  ubicacion?: string;
  zona?: string;
  tipo?: string;
  unidades?: number;
  moneda?: string;
  estado?: string;
  propietario?: string;
}

export interface KpisCabecera {
  ventas: number;
  util_oper: number;
  udi: number;
  margen_oper: number;
  tir_proyecto: number | null;
  tir_socio: number | null;
  vpn_proyecto: number | null;
}

/** Ficha técnica / urbanística (áreas, índices, $/m²). Calculada por el motor. */
export interface Urbanistico {
  lote_bruta: number | null;
  lote_util: number | null;
  ratio_bruta_util: number | null;
  area_construida: number | null;
  area_vendible: number | null;
  indice_construccion: number | null;
  aprovechamiento: number | null;
  densidad_und_ha: number | null;
  precio_m2_vend: number | null;
  costo_dir_m2_const: number | null;
}

export interface ProjectDetail {
  id: string;
  es_real: boolean;
  fuente: string;
  meta: Meta;
  estado: string;
  estado_label: string;
  urbanistico?: Urbanistico | null;
  kpis_cabecera: KpisCabecera;
}

export interface Indicadores {
  base_label: string;
  fiducia_real: boolean;
  tir_proyecto: number | null;
  tir_proyecto_label: string;
  tir_socio: number | null;
  tir_socio_label: string;
  tir_apalancada_ref: number | null;
  vpn_proyecto: number | null;
  vpn_label: string;
  wacc: number | null;
  tio: number | null;
  payback_mes: number | null;
  credito_max: number | null;
  credito_prom: number | null;
  intereses_total: number | null;
  max_necesidad_caja: number | null;
  valor_financiable: number | null;
  margen_oper: number | null;
}

export interface Pyg {
  ventas: number;
  recon_codensa: number;
  total_ingresos: number;
  directos: number;
  indirectos: number;
  honorarios: number;
  gastos_fijos: number;
  indirectos_otros: number;
  costo_lote: number;
  util_oper: number;
  margen_oper: number;
  udi: number;
  cg: number;
  socio: number;
  resultados: number;
}

export interface Check {
  clave: string;
  nombre: string;
  ok: boolean;
  detalle?: string;
}

/** Series mensuales del flujo apalancado (180 meses). */
export interface FlujoApalancado {
  operativo: number[];
  acumulado: number[];
  saldo_credito: number[];
  flujo_equity: number[];
  ingresos: number[];
  costos: number[];
  credito_max: number;
  max_necesidad_caja: number;
  aportes_total: number;
  payback_mes: number | null;
}

export interface Flujo {
  apalancado: FlujoApalancado;
  simple: Record<string, unknown>;
}

export interface Results {
  scenario_id: string;
  project_id: string;
  base_label: string;
  indicadores: Indicadores;
  pyg: Pyg;
  flujo: Flujo;
  checks: Check[];
}

/** GET /v1/projects/{slug}. null si no existe (404). */
export async function getProject(slug: string): Promise<ProjectDetail | null> {
  const res = await apiFetch(`/v1/projects/${encodeURIComponent(slug)}`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`API ${res.status} en /v1/projects/${slug}`);
  return res.json() as Promise<ProjectDetail>;
}

/** GET /v1/scenarios/{slug}:base/results. null si no existe (404). */
export async function getResults(slug: string): Promise<Results | null> {
  const res = await apiFetch(`/v1/scenarios/${encodeURIComponent(slug)}:base/results`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`API ${res.status} en results de ${slug}`);
  return res.json() as Promise<Results>;
}

// ---------- Sensibilidad (escenarios + tornado + heatmap) ----------

export interface EscenarioVals {
  ventas: number;
  util_oper: number;
  margen: number;
}

export interface Sensitivity {
  scenario_id: string;
  project_id: string;
  /** { Base | Optimista | Pesimista } → métricas. */
  escenarios: Record<string, EscenarioVals>;
  /** { "Precio -10%": Δutil, "Precio +10%": Δutil, ... } impacto sobre la utilidad. */
  tornado: Record<string, number>;
  matriz_2d: { pasos_precio: number[]; pasos_costo: number[]; margen_pct: number[][] };
}

/** GET /v1/scenarios/{slug}:base/sensitivity. null si no existe (404). */
export async function getSensitivity(slug: string): Promise<Sensitivity | null> {
  const res = await apiFetch(`/v1/scenarios/${encodeURIComponent(slug)}:base/sensitivity`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`API ${res.status} en sensitivity de ${slug}`);
  return res.json() as Promise<Sensitivity>;
}

// ---------- Cronograma (hitos + absorción + recaudo) ----------

/** Una etapa con sus hitos (fechas ISO + offset de mes desde base_date para el Gantt). */
export interface ScheduleEtapa {
  cod: number | string;
  nombre: string;
  unidades: number;
  iv: string; pe: string; fv: string; ic: string; fc: string;
  dur_obra: number | null;
  iv_mes: number; pe_mes: number; fv_mes: number; ic_mes: number; fc_mes: number;
}

export interface Schedule {
  scenario_id: string;
  project_id: string;
  /** Mes 0 de las series (= IV de la etapa raíz), ISO o null si no hay cronograma. */
  base_date: string | null;
  horizonte: number;
  unidades_total: number;
  etapas: ScheduleEtapa[];
  /** Series mensuales globales de unidades. */
  absorcion: { ventas: number[]; entregas: number[]; acum_ventas: number[]; acum_entregas: number[] };
  /** Series mensuales de caja (miles COP). */
  recaudo: { separacion: number[]; cuota_inicial: number[]; subrogacion: number[]; total: number[] };
}

/** GET /v1/scenarios/{slug}:base/schedule. null si no existe (404). */
export async function getSchedule(slug: string): Promise<Schedule | null> {
  const res = await apiFetch(`/v1/scenarios/${encodeURIComponent(slug)}:base/schedule`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`API ${res.status} en schedule de ${slug}`);
  return res.json() as Promise<Schedule>;
}

// ---------- Costo de capital (WACC build-up CAPM) ----------

export interface WaccInputs {
  rf: number | null; rm: number | null; pm: number | null;
  kd_us: number | null; de_us: number | null; tax_us: number | null;
  de_col: number | null; tax_col: number | null;
  inf_col: number | null; inf_us: number | null;
}

/** Build-up CAPM completo. Tasas como fracción decimal (0.2154 = 21.54%). */
export interface Wacc {
  scenario_id: string;
  project_id: string;
  disponible: boolean;
  wacc?: number;
  tio?: number | null;
  beta_us?: number; beta_d?: number; beta_u?: number; beta_l?: number;
  ke_usd?: number; rp?: number; ke_usd_rp?: number; rplp?: number; ke_cop?: number;
  kd_cop?: number; kd_despues_imp?: number;
  we?: number; wd?: number; t_col?: number;
  /** Contribuciones que suman al WACC: E·Ke y D·Kd·(1−t). */
  aporte_equity?: number; aporte_deuda?: number;
  inputs?: WaccInputs;
}

/** GET /v1/scenarios/{slug}:base/wacc. null si no existe (404). */
export async function getWacc(slug: string): Promise<Wacc | null> {
  const res = await apiFetch(`/v1/scenarios/${encodeURIComponent(slug)}:base/wacc`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`API ${res.status} en wacc de ${slug}`);
  return res.json() as Promise<Wacc>;
}

// ---------- Monte Carlo (POST run) ----------

export interface MCStats {
  p10: number;
  p50: number;
  p90: number;
  media: number;
  std: number;
  n: number;
}

export interface MonteCarloResult {
  tir_proyecto: number[];
  tir_equity: number[];
  vpn_proyecto: number[];
  stats_tir: MCStats;
  stats_equity: MCStats;
  stats_vpn: MCStats;
  hurdle: number;
  prob_tir_hurdle: number;
  prob_vpn_pos: number;
  n: number;
  n_validas: number;
}

export interface MonteCarloParams {
  tipo?: "tir" | "margen";
  n?: number;
  seed?: number;
  rango_precio?: [number, number];
  rango_costo?: [number, number];
  rango_ventas?: [number, number];
}

/** POST /v1/scenarios/{slug}:base/run — Monte Carlo (único cálculo intensivo). */
export async function postRun(slug: string, params: MonteCarloParams): Promise<MonteCarloResult> {
  const res = await apiFetch(`/v1/scenarios/${encodeURIComponent(slug)}:base/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(`API ${res.status} al correr Monte Carlo de ${slug}`);
  return res.json() as Promise<MonteCarloResult>;
}
