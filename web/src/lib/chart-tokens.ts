/**
 * Tokens de color para las gráficas (ECharts), modo claro Y oscuro. Espíritu "vintage" anclado al
 * teal CG. Semánticos (verde/ámbar/rojo) SOLO para estados, nunca como color de serie decorativo.
 * El host pone el fondo (las gráficas usan backgroundColor: 'transparent').
 */
export interface ChartTokens {
  palette: string[]; // roles de serie: [primary teal, accent teal vivo, s2..s8 rampa vintage]
  primary: string; // teal CG
  accent: string; // teal vivo
  positivo: string; // mediana/positivo (= accent)
  grid: string; // splitLine
  axisLabel: string;
  axisLine: string;
  tooltipBg: string;
  tooltipBorder: string;
  tooltipText: string;
  areaOpacity: number;
  // Semánticos (estados): éxito / alerta / peligro.
  exito: string;
  alerta: string;
  peligro: string;
}

const LIGHT: ChartTokens = {
  palette: ["#0F6E56", "#1D9E75", "#61A0A8", "#919E8B", "#D7AB82", "#CC7E63", "#D87C7C", "#787464", "#6E7074"],
  primary: "#0F6E56",
  accent: "#1D9E75",
  positivo: "#1D9E75",
  grid: "rgba(120,118,100,0.14)",
  axisLabel: "#6F6E68",
  axisLine: "rgba(120,118,100,0.25)",
  tooltipBg: "#FFFFFF",
  tooltipBorder: "rgba(120,118,100,0.25)",
  tooltipText: "#2C2C2A",
  areaOpacity: 0.13,
  exito: "#639922",
  alerta: "#BA7517",
  peligro: "#CC4B3C",
};

const DARK: ChartTokens = {
  palette: ["#2FB68C", "#45C99E", "#7FBFC7", "#A8B3A2", "#E2C19A", "#E0997A", "#E29B9C", "#ABA694", "#9A9EA8"],
  primary: "#2FB68C",
  accent: "#45C99E",
  positivo: "#45C99E",
  grid: "rgba(225,223,212,0.10)",
  axisLabel: "#9A988F",
  axisLine: "rgba(225,223,212,0.18)",
  tooltipBg: "#232326",
  tooltipBorder: "rgba(225,223,212,0.16)",
  tooltipText: "#E9E7E0",
  areaOpacity: 0.16,
  exito: "#8FB85B",
  alerta: "#E0A23A",
  peligro: "#E0775F",
};

/** Tokens del modo activo. El host (claro/oscuro por clase `.dark`) decide `isDark`. */
export function chartTokens(isDark: boolean): ChartTokens {
  return isDark ? DARK : LIGHT;
}
