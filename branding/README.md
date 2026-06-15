# Marca ALEPH

Identidad visual de ALEPH, derivada de **CG Constructora** (mismo teal + ámbar) con marca propia:
**el anillo de precisión con el punto al centro** (el *álef* como un punto). Minimalista y moderno.

## Colores de marca

| Rol | Hex | Uso |
|---|---|---|
| Teal CG (primario) | `#0E5E59` | fondo del tile, anillo en versión clara, texto del wordmark claro |
| Ámbar CG (secundario) | `#F4AF20` | el punto central (el *álef*) |
| Blanco | `#FFFFFF` | anillo y texto sobre teal |

## Archivos

| Archivo | Tamaño | Para qué |
|---|---|---|
| `aleph-tile-215.png` | 215×215, fondo sólido | **Mosaico de Microsoft Entra** (App Launcher M365). Cumple el requisito de Entra (PNG cuadrado, fondo sólido, <100 KB). El nombre "ALEPH" lo muestra Entra como etiqueta debajo. |
| `aleph-teams-color-192.png` | 192×192, color | Ícono **color** de la app de Microsoft Teams (manifest `icons.color`). |
| `aleph-teams-outline-32.png` | 32×32, transparente, blanco | Ícono **outline** de Teams (manifest `icons.outline`); Teams lo recolorea según el tema. |
| `aleph-wordmark-teal.png` | 338×130 | Wordmark sobre **teal** — encabezados de la app, login, banners. |
| `aleph-wordmark-light.png` | 338×130 | Wordmark sobre **claro/blanco** — documentos, firmas de correo. |

## Regeneración

El tile y los íconos de Teams se generan por píxeles con `sharp` (el renderizador SVG de `sharp`
da negro en este entorno, por eso se dibujan a mano con anti-aliasing). Los wordmarks se rasterizan
con Chrome (agent-browser) para tener el texto con fuente real, y se recortan con `sharp`. La marca
en código vive además en `web/src/app/icon.svg` (favicon) y `web/src/components/aleph-mark.tsx`.
