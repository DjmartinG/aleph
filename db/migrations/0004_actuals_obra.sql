-- 0004_actuals_obra.sql
-- Constitución (Modelo de datos objetivo): `actuals_*` para ejecutados, con campo `source`.
-- Cimiento de la INGESTA DE ACTUALS (valor ganado) desde SINCO — Fase 1 · Paso 1.
-- ADITIVA: CREATE TABLE nuevo; no altera ni toca ninguna tabla existente. No mueve cifras, no
-- toca el motor ni el dorado. Nada la consume aún (el cableado a evm.py / Monitor llega en pasos
-- posteriores), así que aplicarla antes de tiempo no tiene impacto.
--
-- Aplicar en el SQL Editor de Supabase. La poblará el conector de SINCO (api/aleph_api/conectores/sinco.py)
-- vía la service_role del API. SOLO AGREGADOS (PV/EV/AC/BAC por proyecto·nivel·periodo): sin datos personales.

create table if not exists public.actuals_obra (
    id           bigint generated always as identity primary key,
    proyecto     text        not null,                      -- slug/id de ALEPH (p.ej. 'navarra')
    nivel        text        not null default 'TOTAL',      -- capítulo / WBS ('TOTAL' = proyecto entero)
    periodo      date        not null,                      -- mes al que pertenece el dato (día 1 del mes)
    pv           numeric     not null default 0,            -- Planned Value (valor planeado)
    ev           numeric     not null default 0,            -- Earned Value (valor ganado)
    ac           numeric     not null default 0,            -- Actual Cost (costo real)
    bac          numeric,                                   -- Budget At Completion (presupuesto total); null = desconocido
    source       text        not null default 'sinco',      -- manual | excel | erp | crm | sinco
    corte        date,                                      -- fecha de corte de la extracción SINCO (as-of)
    fecha_carga  timestamptz not null default now(),        -- cuándo se insertó la fila
    updated_at   timestamptz not null default now()
);

-- Un único registro por (source, proyecto, nivel, periodo, corte): permite re-extraer el mismo
-- periodo en cortes distintos sin chocar, y hacer upsert idempotente sobre esta clave natural.
create unique index if not exists actuals_obra_natural_ux
    on public.actuals_obra (source, proyecto, nivel, periodo, coalesce(corte, periodo));

create index if not exists actuals_obra_proyecto_periodo_ix
    on public.actuals_obra (proyecto, periodo);

-- updated_at automático (mismo patrón que 0002/0003).
create or replace function public.tg_actuals_obra_touch()
returns trigger language plpgsql as $$
begin
    new.updated_at := now();
    return new;
end $$;

drop trigger if exists actuals_obra_touch on public.actuals_obra;
create trigger actuals_obra_touch
    before update on public.actuals_obra
    for each row execute function public.tg_actuals_obra_touch();

-- RLS: gerencia LEE, admin EDITA (deny-by-default como backstop; la autorización real la hace el API).
-- Mismo molde que supuestos_macro (0003).
alter table public.actuals_obra enable row level security;

drop policy if exists actuals_obra_read on public.actuals_obra;
create policy actuals_obra_read
    on public.actuals_obra for select
    using (true);   -- lectura para usuarios autenticados (la API ya valida el token Entra)

drop policy if exists actuals_obra_write on public.actuals_obra;
create policy actuals_obra_write
    on public.actuals_obra for all
    using (false) with check (false);  -- escritura solo vía service_role del API (bypassa RLS); nadie más

comment on table public.actuals_obra is
    'Actuals de obra (valor ganado) agregados por proyecto·nivel·periodo. source=''sinco'' lo puebla el '
    'conector de SINCO (Fase 1). Solo agregados PV/EV/AC/BAC; sin datos personales. Insumo futuro de evm.py.';
