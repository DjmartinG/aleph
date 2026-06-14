-- 0003_supuestos_macro.sql
-- Spec: directives/spec_pyg_dinamico.md · Módulo M0
-- Tabla VERSIONADA de supuestos macro/financieros (tasas, EMBI, IPC, ICOCED, betas, SMMLV, tasas por banco).
-- ADITIVA: no toca tablas existentes. La poblan los conectores de M6 / carga manual.
-- Defaults numéricos espejan engine/aleph_engine/supuestos_macro.py (cero cifras nuevas).
--
-- Aplicar en el SQL Editor de Supabase cuando se llegue a M6 (o antes, sin impacto: nada la consume aún).

create table if not exists public.supuestos_macro (
    id                bigint generated always as identity primary key,
    clave             text        not null,                 -- p.ej. 'tio', 'embi', 'ipc', 'icoced', 'tasa_credito:bancolombia'
    nombre            text        not null,
    valor             numeric     not null,
    unidad            text        not null,                 -- ratio | ratio_ea | COP_miles | meses | indice
    fuente            text        not null,                 -- Banrep | DANE | SFC | Damodaran | Camacol | Comité CG | manual
    metodo            text        not null default 'manual',-- api | manual | benchmark | config
    descripcion       text        not null default '',
    fecha             date,                                 -- corte del dato (null = constante de política)
    estado_validacion text        not null default 'vigente', -- vigente | por_validar | desactualizado
    fuente_normativa  text        not null default '',
    version           integer     not null default 1,
    vigente           boolean     not null default true,    -- un solo registro vigente por clave
    created_at        timestamptz not null default now(),
    updated_at        timestamptz not null default now()
);

-- Un único registro vigente por clave (histórico se conserva con vigente=false).
create unique index if not exists supuestos_macro_clave_vigente_ux
    on public.supuestos_macro (clave) where vigente;

create index if not exists supuestos_macro_clave_ix on public.supuestos_macro (clave);

-- updated_at automático (mismo patrón que 0002).
create or replace function public.tg_supuestos_macro_touch()
returns trigger language plpgsql as $$
begin
    new.updated_at := now();
    return new;
end $$;

drop trigger if exists supuestos_macro_touch on public.supuestos_macro;
create trigger supuestos_macro_touch
    before update on public.supuestos_macro
    for each row execute function public.tg_supuestos_macro_touch();

-- RLS: gerencia LEE, admin EDITA (deny-by-default como backstop; la autorización real la hace el API).
alter table public.supuestos_macro enable row level security;

drop policy if exists supuestos_macro_read on public.supuestos_macro;
create policy supuestos_macro_read
    on public.supuestos_macro for select
    using (true);   -- lectura para usuarios autenticados (la API ya valida el token Entra)

drop policy if exists supuestos_macro_write on public.supuestos_macro;
create policy supuestos_macro_write
    on public.supuestos_macro for all
    using (false) with check (false);  -- escritura solo vía service_role del API (bypassa RLS); nadie más

comment on table public.supuestos_macro is
    'Supuestos macro/financieros versionados (M0, spec_pyg_dinamico.md). Poblada por conectores M6 / carga manual.';
