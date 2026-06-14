# DESIGN — ALEPH (web)

Sistema de diseño reutilizable. Valores vivos en `src/app/globals.css` (fuente de verdad de los tokens).
Registro: **product**. Estrategia de color: **Restrained** (canvas neutro tintado + un acento).

## Color (OKLCH, neutrales tintados hacia el teal CG, sin #000/#fff)

- **Acento** = teal CG `#0E5E59` ≈ `oklch(0.45 0.075 184)`. Solo para acción primaria, selección, énfasis
  positivo e indicadores de estado. **Nunca decorativo.**
- **Neutrales** tintados hacia el hue teal (~195-210), chroma 0.003-0.015. Canvas, superficies, bordes, texto.
- **Segunda capa neutra**: el sidebar/paneles van un punto más fríos/oscuros que el contenido (jerarquía).
- **Semánticos** (solo estado, no decoración): success (verde), warning (ámbar CG), danger (rojo).
- Light primario; dark equivalente por clase `.dark`. Toggle persistente (sin FOUC).

## Tipografía (Inter, una familia)

- Escala rem FIJA, ratio ~1.2: `text-xs` 0.75 / `sm` 0.875 / `base` 1 / `lg` 1.125 / `xl` 1.25 / `2xl` 1.5.
- Jerarquía por **escala + peso** (400 cuerpo, 500 labels, 600 títulos/cifras). Contraste sin exagerar.
- **`font-variant-numeric: tabular-nums` en TODO número.** Cifras alineadas a la derecha.
- Labels de métrica: `xs`, `uppercase`, `tracking-wide`, `muted`. Etiqueta de base: `[0.7rem]`, `muted-foreground` pleno (AA: la opacidad /70-/80 fallaba contraste 4.5:1).

## Layout y superficies

- App-shell: **sidebar** (segunda capa neutra, grupos PORTAFOLIO / PROYECTO) + **topbar** (breadcrumb +
  tema + usuario). Contenido `max-w-7xl`, padding responsive.
- **Las tarjetas no son la respuesta por defecto.** El resumen del portafolio es UN panel dividido por
  separadores (`StatPanel`), no un grid de tarjetas idénticas (eso es slop). Tarjeta solo cuando una métrica
  sola merece marco. Nunca tarjetas anidadas.
- Densidad financiera: tablas densas, números a la derecha, separadores sutiles, ritmo de espaciado variado.
- Responsive **estructural** (colapsa sidebar, tabla con scroll en tablet), no tipografía fluida.

## Componentes canon (default/hover/focus/active/disabled/loading)

- `Stat` (valor + etiqueta de base + delta + estado) y `StatPanel` (varios Stats con separadores).
- `KpiCard` (variante con marco, para una métrica destacada).
- `PhaseBadge` (color por fase del ciclo de vida), `ChecksBadge` (estado de cuadres), `StatusDot`.
- `DataTable` densa, ordenable, números a la derecha. `Skeleton` para carga (nunca spinner central).
- Estados vacíos que **enseñan** la interfaz, no "nada aquí".

## Motion

- Tokens: `--ease-out` (ease-out-quint) + duraciones `--dur-1/2/3` (120/180/280 ms). Salida < entrada; UI < 300 ms.
- **Solo comunica ESTADO**: hover, foco, selección, presión (`active:scale-[0.97]`), apertura (popovers con `pop-in`, origen en su esquina). Nada de coreografía al cargar.
- **Las CIFRAS, el P&G y los gráficos NO se animan** (es una herramienta de decisión financiera: nada de números que cuentan hacia arriba ni reveals gimmicky — "si fuera un gráfico de un banco, mejor sin animación").
- Solo `transform`/`opacity` (GPU). Sin bounce/elastic. `prefers-reduced-motion` ya respetado en base.
- Nada de animar propiedades de layout (`width/height/top/left`).

## Accesibilidad

- Contraste AA. Foco visible (ring teal). Targets cómodos en tablet. `aria-*` en controles e iconos.
