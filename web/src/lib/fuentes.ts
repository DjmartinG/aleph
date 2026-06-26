/**
 * Procedencia CURADA de los datos macroeconómicos que alimentan el WACC (Fase 1 de "Fuentes y
 * metodología"). La FUENTE / método / enlace se curan aquí (no cambian); el VALOR se lee EN VIVO del
 * motor vía `getWacc` (un proyecto representativo: la calibración macro es común a todos, corte
 * jun-2026) → cero cifras hardcodeadas en el front. Fase 2 añadirá el contraste con el dato vivo de
 * cada fuente. Ver `docs/acta_rebaseline_wacc2_betad_rp_20260614.md`.
 */
import type { Wacc } from "@/lib/api";

export interface FuenteDato {
  nombre: string;
  /** Cómo se usa en el build-up. */
  descripcion: string;
  /** Lee el valor de la calibración del payload de WACC del motor. */
  get: (w: Wacc) => number | null;
  /** "pct" = fracción → %, "num" = número crudo (betas). */
  fmt: "pct" | "num";
  /** Clave del input del WACC con fuente VIVA (Fase 2): hace match con FuentesLive.datos[clave]. */
  clave?: "rp" | "pm";
}

export interface FuenteGrupo {
  fuente: string;
  url: string;
  /** Qué publica esta fuente / cómo la usamos. */
  nota: string;
  datos: FuenteDato[];
}

/** Agrupado por FUENTE de origen. El orden sigue el build-up del WACC. */
export const FUENTES: FuenteGrupo[] = [
  {
    fuente: "Damodaran · NYU Stern",
    url: "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datacurrent.html",
    nota: "Datos de mercado y de sector (homebuilding) del profesor Aswath Damodaran, base del build-up CAPM para mercados emergentes.",
    datos: [
      { nombre: "Tasa libre de riesgo (rf)", descripcion: "Bono del Tesoro de EE.UU. a 10 años; ancla del CAPM en USD.", get: (w) => w.inputs?.rf ?? null, fmt: "pct" },
      { nombre: "Prima de mercado (ERP)", descripcion: "Equity Risk Premium del mercado maduro (EE.UU.): rm − rf.", get: (w) => w.inputs?.pm ?? null, fmt: "pct", clave: "pm" },
      { nombre: "Riesgo país · Colombia (CRP)", descripcion: "Country Risk Premium de Colombia; se suma al Ke en USD.", get: (w) => w.rp ?? null, fmt: "pct", clave: "rp" },
      { nombre: "Beta del sector (apalancada, US)", descripcion: "Beta del sector construcción/homebuilding; se desapalanca y se reapalanca a la estructura CG.", get: (w) => w.beta_us ?? null, fmt: "num" },
      { nombre: "D/E del sector (US)", descripcion: "Relación deuda/equity del sector comparable; usada para desapalancar la beta.", get: (w) => w.inputs?.de_us ?? null, fmt: "pct" },
      { nombre: "Costo de deuda comparable (kd US)", descripcion: "Costo de deuda de un comparable grado de inversión (BBB); de aquí se deriva la beta de la deuda.", get: (w) => w.inputs?.kd_us ?? null, fmt: "pct" },
      { nombre: "Tasa impositiva (US)", descripcion: "Tasa efectiva del comparable US, para el escudo fiscal de su estructura.", get: (w) => w.inputs?.tax_us ?? null, fmt: "pct" },
    ],
  },
  {
    fuente: "Banco de la República · DANE",
    url: "https://www.banrep.gov.co/es/estadisticas/inflacion-total-y-meta",
    nota: "Inflación de Colombia (IPC) publicada por el Banco de la República y el DANE; entra en la paridad de inflación que lleva el Ke de USD a COP.",
    datos: [
      { nombre: "Inflación · Colombia", descripcion: "IPC esperado de Colombia; numerador de la paridad de inflación CO/US.", get: (w) => w.inputs?.inf_col ?? null, fmt: "pct" },
    ],
  },
  {
    fuente: "Reserva Federal · BLS (EE.UU.)",
    url: "https://www.bls.gov/cpi/",
    nota: "Inflación de EE.UU. (CPI) de la Reserva Federal / Bureau of Labor Statistics; denominador de la paridad de inflación.",
    datos: [
      { nombre: "Inflación · EE.UU.", descripcion: "CPI esperado de EE.UU.; denominador de la paridad de inflación CO/US.", get: (w) => w.inputs?.inf_us ?? null, fmt: "pct" },
    ],
  },
  {
    fuente: "DIAN · Estatuto Tributario (Colombia)",
    url: "https://www.dian.gov.co/",
    nota: "Tasa de renta corporativa de Colombia; define el escudo fiscal local del WACC.",
    datos: [
      { nombre: "Tasa de renta · Colombia", descripcion: "Tarifa corporativa que escuda el costo de la deuda en el WACC (E·Ke + D·Kd·(1−t)).", get: (w) => w.inputs?.tax_col ?? null, fmt: "pct" },
    ],
  },
  {
    fuente: "CG Constructora · política interna",
    url: "",
    nota: "Estructura de capital objetivo del proyecto (apalancamiento), definida por la dirección financiera de CG.",
    datos: [
      { nombre: "D/E objetivo · Colombia", descripcion: "Relación deuda/equity objetivo a la que se reapalanca la beta y se ponderan E y D.", get: (w) => w.inputs?.de_col ?? null, fmt: "pct" },
    ],
  },
];

/**
 * Datos de mercado de REFERENCIA (no entran al WACC). El texto/enlace se cura aquí; el VALOR se lee EN
 * VIVO del API (conector Banrep). El dólar (TRM) no alimenta el costo de capital —el build-up se lleva a
 * pesos por paridad de inflación, no por la tasa de cambio del día—, pero es una referencia macro útil.
 */
export const MERCADO_TRM = {
  fuente: "Banco de la República",
  url: "https://www.banrep.gov.co/es/estadisticas/trm",
  nombre: "Dólar · TRM (COP/USD)",
  descripcion: "Tasa Representativa del Mercado, último dato oficial publicado por el Banco de la República.",
  nota: "Tasa Representativa del Mercado (COP/USD) oficial del Banco de la República. Dato de mercado de referencia — no entra en el cálculo del WACC (el costo de capital se lleva a pesos por paridad de inflación, no por la tasa de cambio del día).",
};
