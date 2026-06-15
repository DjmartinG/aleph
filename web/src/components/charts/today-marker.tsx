/** Marcador "Hoy" para las gráficas del cronograma: línea vertical punteada (altura completa) +
 * etiqueta-pill arriba. Color neutro (var(--foreground)) para no confundirse con los datos
 * (teal/ámbar). Se renderiza DENTRO del <Group left={M.left} top={M.top}> de la gráfica, en
 * coordenadas internas (x ya escalado a píxeles). Requiere M.top >= ~20 para que la pill no se corte. */
export function TodayMarker({ x, ih, iw }: { x: number; ih: number; iw: number }) {
  const lx = Math.round(x) + 0.5; // medio píxel = línea nítida
  const px = Math.max(16, Math.min(iw - 16, x)); // centro de la pill, sin desbordar los bordes
  return (
    <g pointerEvents="none">
      <line
        x1={lx}
        x2={lx}
        y1={0}
        y2={ih}
        stroke="var(--foreground)"
        strokeWidth={1.25}
        strokeDasharray="3 3"
        strokeOpacity={0.55}
      />
      <g transform={`translate(${px}, -9)`}>
        <rect x={-15} y={-8} width={30} height={15} rx={7.5} fill="var(--foreground)" />
        <text x={0} y={2.6} textAnchor="middle" fontSize={9.5} fontWeight={600} fill="var(--background)">
          Hoy
        </text>
      </g>
    </g>
  );
}
