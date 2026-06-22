# Conector SINCO — actuals de obra (Fase 1 · Paso 1)

Cimiento de la ingesta de **actuals** (valor ganado) desde el DATAMART de SINCO hacia ALEPH. Es
**aditivo**: no toca `calcular()`, `evm.py` ni el dorado. En el Paso 1 todo se prueba con **fixture**;
la conexión en vivo se enchufa en el Paso 2.

## Piezas

| Pieza | Ubicación |
|---|---|
| Esquema de actuals (migración aditiva) | `db/migrations/0004_actuals_obra.sql` |
| Conector (config-driven, solo lectura) | `api/aleph_api/conectores/sinco.py` |
| Tests con fixture (sin red) | `api/tests/test_conector_sinco.py` |
| Variables de entorno | `.env.example` |

## Configuración (variables de entorno — nunca en código)

| Variable | Ejemplo | Notas |
|---|---|---|
| `SINCO_SERVER` | `datamart.sincoerp.com,4263` | host,puerto (estilo SQL Server) |
| `SINCO_DB` | `SincoCGDW` | base del DATAMART |
| `SINCO_USER` | — | usuario **read-only** que provee SINCOSOFT |
| `SINCO_PASSWORD` | — | secreto: Key Vault / GitHub Secrets, jamás en git |

Driver SQL Server: **`pymssql`** (dependencia opcional). Instalar solo donde se conecte en vivo:

```
pip install 'aleph-api[sinco]'      # o:  pip install pymssql
```

El `import pymssql` es **perezoso** (solo al conectar), así que el módulo importa y los tests corren
**sin** el driver instalado. CI no lo instala.

## Smoke test manual (cuando ya haya credenciales) — NO en CI

Lo corre **Martín en local** (no el CI), una vez SINCOSOFT entregue el usuario read-only y el firewall
permita el acceso. Verifica conexión/firewall **e imprime los nombres de columna reales** de la view
(insumo para llenar el mapeo en el Paso 2):

```bash
# 1) define las variables (o usa un .env)
export SINCO_SERVER='datamart.sincoerp.com,4263'
export SINCO_DB='SincoCGDW'
export SINCO_USER='<usuario_readonly>'
export SINCO_PASSWORD='<secreto>'

# 2) SELECT TOP 5 contra ADP_DTM_VFACT.ControlProyecto
pip install pymssql
python -m aleph_api.conectores.sinco
```

Salida esperada: `OK — N filas leídas`, la lista de **columnas** y las 5 filas. Si falla, imprime el
tipo de error (firewall, login, driver) sin tumbar nada.

> En PowerShell (Windows): `$env:SINCO_SERVER='datamart.sincoerp.com,4263'` (y análogos) antes de correr.

## Paso 2 (pendiente — fuera de este alcance)

1. **Llenar `MAPEO_CONTROL_PROYECTO`** en `sinco.py` con las columnas reales que imprimió el smoke
   (hoy está en `# TODO`; `to_actuals(...)` con el mapeo por defecto falla en voz alta a propósito).
2. **Conexión en vivo + job programado** (Azure Functions / GitHub Actions) → upsert en `actuals_obra`
   vía la `service_role` del API.
3. **Cablear los actuals** a `engine/aleph_engine/evm.py` y al Monitor en `/web`.
