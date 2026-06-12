# PRODUCT — ALEPH (web)

register: product

## Producto

ALEPH es la plataforma de evaluación financiera de proyectos inmobiliarios de **CG Constructora S.A.S.**
La web (`/web`) SOLO presenta: todo cálculo vive en el motor (`aleph_engine`) y se consume vía API. Ningún
número se inventa ni se recalcula en el frontend.

## Usuarios

- **Gerencia / comité**: revisa rentabilidad y estado del portafolio, muchas veces en **tablet** durante
  reuniones a media mañana. Necesita confiar en la cifra de un vistazo, sin ruido.
- **Admin (Martin y 1-2 más)**: cargan supuestos y comparan escenarios desde el escritorio, en oficina
  iluminada. No son desarrolladores.

## Tono y registro

Instrumento financiero serio y confiable, no un "SaaS bonito". La interfaz **desaparece en la tarea**: la
estrella es el dato. Densidad alta, decoración cero. Confianza por precisión (alineación, tabular-nums,
etiquetas de base), no por adorno.

## Tema

**Light primario** (la escena lo fuerza: comité diurno, tablet, lectura sin esfuerzo, confianza en finanzas).
**Dark disponible** desde el día uno para revisión nocturna / pantallas grandes. Toggle persistente.

## Principios estratégicos

- **Ninguna cifra sin etiqueta de base.** Nunca "TIR" a secas: "TIR proyecto", "TIR apal. ref.", "TIR socio".
- **Números a la derecha, `tabular-nums` siempre.** Alineados, comparables, miles con punto (es-CO).
- **Estado del proyecto** (ciclo de vida) como eje rector: pre-factibilidad → aprobado → construcción → entregado.
- **Checks de cuadre** visibles por módulo (P&G suma, recaudo = ventas, etc.).
- Consistencia pantalla a pantalla > sorpresa. El mismo vocabulario visual en portafolio, ficha, resultados.

## Anti-referencias (qué NO ser)

- El reflejo "finanzas = navy + gold". Usamos el **teal CG real**, no el cliché de categoría.
- Tableros de Excel/BI genéricos (grids de tarjetas idénticas, gradientes, hero-metric).
- "SaaS-cream" y glassmorphism decorativo.

## Referencias de calidad

Linear, Mercury, Stripe Dashboard, Tremor. Earned familiarity: un usuario fluido en esas herramientas debe
**confiar** en ALEPH al sentarse, sin pausar ante un componente raro.
