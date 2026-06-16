# App de Microsoft Teams — ALEPH

Paquete de app personalizada de Teams para fijar un ícono de **ALEPH** en la barra (riel) de Teams.

## Cómo funciona (importante)

El login de Microsoft (Entra) **no se puede incrustar** en un iframe de Teams por seguridad. Por eso
la pestaña de Teams **no embebe ALEPH**: muestra un **lanzador** (`web/public/teams.html`, servido en
`https://aleph.cgconstructora.com/teams.html`, público) con un botón **"Abrir ALEPH"** que abre la app en
el **navegador** con el SSO intacto. Limpio y sin pantallas de login rotas.

## Archivos

| Archivo | Qué es |
|---|---|
| `manifest.json` | Manifiesto de la app (schema 1.17). `id` = GUID fijo; `staticTabs` → el lanzador. |
| `color.png` (192×192) | Ícono color de Teams. |
| `outline.png` (32×32) | Ícono outline (transparente) de Teams. |
| `aleph-teams.zip` | **El paquete listo para subir** (manifest + íconos en la raíz del zip). |

## Subir y fijar (lo hace un admin de Teams)

1. **Subir:** [Teams admin center](https://admin.teams.microsoft.com) → **Teams apps → Manage apps →
   Upload new app** → seleccioná `teams-app/aleph-teams.zip`. (Disponible en unas horas en "Built for your org".)
2. **Fijar a todos:** **Teams apps → Setup policies → Global (Org-wide default) → Pinned apps →
   Add apps → ALEPH → Add → Save**. Aparece en el riel izquierdo de Teams de todos.
   *(Permitir custom apps: Setup policies → "Upload custom apps" = On, si no lo está.)*

## Actualizar la app (subir una versión nueva)

El manifiesto ya apunta al dominio propio `aleph.cgconstructora.com` (v1.0.1 · 2026-06-15).

Para cualquier cambio futuro (dominio, ícono, nombre): editar `manifest.json`, **subir `version`**
(Teams exige una versión mayor para aceptar la actualización, mismo `id`) y regenerar el zip:

```bash
python -c "import zipfile; z=zipfile.ZipFile('teams-app/aleph-teams.zip','w',zipfile.ZIP_DEFLATED); [z.write('teams-app/'+f,f) for f in ['manifest.json','color.png','outline.png']]; z.close()"
```

Subir la nueva versión (mismo `id`) por **Teams admin center → Manage apps → ALEPH → Update**.
