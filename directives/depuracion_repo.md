# Depuración y limpieza del repo ALEPH

> **Para:** Claude Code en VS Code · **Objetivo:** dejar el repo ultra-profesional sin tocar el motor ni las cifras doradas.
> **Regla de oro:** después de CADA paso, correr `.\test.ps1` y confirmar que el snapshot dorado sigue verde (55+ passed). Si alguna cifra se mueve, revertir el paso y reportar a Martin. Hacer un commit por paso (mensajes claros).

---

## Paso 0 — Salvar el trabajo en riesgo (PRIMERO, antes de nada)

Hay trabajo del Monte Carlo en `web/` sin commitear (3 modificados + 3 nuevos: `monte-carlo.tsx`, `distribution-histogram.tsx`, `actions.ts`, `ficha-sensibilidad.tsx`, `ficha-tabs.tsx`, `api.ts`).

1. Revisar que compile: `cd web && npm run build` (o `npm run lint`).
2. `git add web/ && git commit -m "feat(web): vista Monte Carlo + histograma de distribución"`
3. `git push`

**Verificación:** `git status` limpio en `web/`. El trabajo ya está en GitHub.

## Paso 1 — Renormalizar fin de línea (CRLF → LF)

Causa raíz del ruido: 51 archivos trackeados con CRLF hacen que git reporte ~23.000 líneas cambiadas fantasma.

1. Confirmar que `.gitattributes` en la raíz tenga al menos:
   ```
   * text=auto eol=lf
   *.ps1 text eol=crlf
   *.bat text eol=crlf
   *.png binary
   *.xlsx binary
   *.xlsm binary
   ```
   (los `.ps1`/`.bat` se quedan en CRLF porque son scripts de Windows; los binarios marcados `binary` para que git no los toque).
2. Renormalizar: `git add --renormalize .`
3. `git commit -m "chore: renormalizar EOL a LF (.gitattributes)"`
4. `git push`

**Verificación:** tras el commit, `git status` debe quedar limpio y un cambio trivial futuro debe mostrar solo las líneas reales, no archivos enteros. Correr `.\test.ps1` → 55+ passed (las cifras NO dependen del EOL, pero verificar por disciplina).

## Paso 2 — Sincronizar CLAUDE.md = AGENTS.md (que no se vuelvan a desincronizar)

Hoy difieren; la doctrina exige réplicas idénticas.

- **Opción recomendada (a prueba de futuro):** dejar `CLAUDE.md` como único real y convertir `AGENTS.md` y `GEMINI.md` en copias generadas. Si el entorno soporta symlink en git, usarlo; si no, agregar un script `sync_docs.ps1`/`.sh` que copie `CLAUDE.md` sobre los otros dos, y correrlo antes de cada commit que toque la doctrina.
- **Opción mínima:** copiar el contenido de `CLAUDE.md` sobre `AGENTS.md` ahora mismo para igualarlos.

`git commit -m "docs: re-sincronizar AGENTS.md con CLAUDE.md"`

**Verificación:** `diff CLAUDE.md AGENTS.md` no muestra diferencias.

## Paso 3 — Quitar basura suelta de la raíz

1. Borrar `mc.png` (captura suelta) y cualquier `*.png`/`*.log`/`*.tmp` que no sea parte del proyecto.
2. Añadir al `.gitignore` de la raíz, si falta:
   ```
   /*.png
   /*.log
   *.tmp
   ```
   (las imágenes de producto que SÍ van al repo viven en `web/public/`, no en la raíz, así que ignorar PNG sueltos en raíz es seguro.)
3. `git commit -m "chore: limpiar archivos sueltos de la raíz + ignorar basura"`

**Verificación:** `ls` en la raíz no muestra `.png`/`.tmp` sueltos. `git status` limpio.

## Paso 4 — Borrar la rama vieja ya fusionada

La rama `aleph-prompt2-2-monorepo` ya está integrada en `main`.

1. `git push origin --delete aleph-prompt2-2-monorepo`
2. `git remote prune origin`

**Verificación:** `git branch -a` solo muestra `main` (local y remoto).

## Paso 5 — Archivar el historial de aprendizajes (aligerar CLAUDE.md)

`CLAUDE.md` pesa ~57 KB; la sección «Aprendizajes del Agente» creció más allá de las ~25 entradas que la propia doctrina marca como límite.

1. Crear `docs/historial_aprendizajes.md`.
2. Mover ahí las entradas **anteriores a la migración** (todo lo de 2026-05-28 y los aprendizajes ya superados de Streamlit), dejando en `CLAUDE.md` solo las ~10-15 más recientes y vigentes + un enlace al historial.
3. NO borrar ningún aprendizaje: se archivan, no se eliminan. Las cifras doradas y gotchas operativos vigentes se quedan en `CLAUDE.md`.
4. Re-sincronizar `AGENTS.md` (paso 2). `git commit -m "docs: archivar aprendizajes históricos a docs/historial_aprendizajes.md"`

**Verificación:** `CLAUDE.md` notablemente más corto; el historial completo intacto en `docs/`.

## Paso 6 — Cierre de calidad

1. Correr el linter de todo: ruff en `engine`/`api`/`app_streamlit`, eslint en `web`.
2. Confirmar que el CI de GitHub Actions pasa en verde tras todos los push.
3. `.\test.ps1` final: 55+ passed, snapshot dorado verde.

**Verificación final (Martin):** abrir GitHub → pestaña Actions todo verde; el repo se ve limpio (sin archivos sueltos, una sola rama, docs sincronizados).

---

## Prohibiciones (recordatorio)

- NO tocar `engine/aleph_engine` ni las fórmulas financieras.
- NO borrar ni modificar tests de anclas, snapshots dorados ni los JSON de proyectos.
- NO eliminar aprendizajes (archivar ≠ borrar).
- NO usar `:latest` en imágenes Docker.
- Un commit por paso, push tras cada uno, `.\test.ps1` verde como requisito para avanzar.
