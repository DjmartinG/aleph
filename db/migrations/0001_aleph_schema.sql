-- ============================================================================
-- ALEPH · Migración 0001 — modelo destino (companies/projects/scenarios/…)
-- PROMPT 4 · Fase 4b. Constitución §"Modelo de datos objetivo" + plan_migracion §4.3.
--
-- SEGURO Y ADITIVO: crea tablas NUEVAS, NO toca la tabla `proyectos` actual (el Streamlit sigue
-- leyendo/escribiendo como hoy). Idempotente (IF NOT EXISTS): se puede correr varias veces.
-- El ETL (db/etl_import_v1.py) puebla estas tablas desde `proyectos` y verifica contra el dorado.
--
-- Ejecutar: pegar en el SQL Editor de Supabase, o vía MCP apply_migration.
-- ============================================================================

-- Para gen_random_uuid()
create extension if not exists pgcrypto;

-- 1) Empresas -----------------------------------------------------------------
create table if not exists public.companies (
  id          uuid primary key default gen_random_uuid(),
  slug        text unique not null,
  nombre      text not null,
  created_at  timestamptz not null default now()
);

-- 2) Proyectos (la `fase` —ciclo de vida— se promueve de meta.estado a columna) -
create table if not exists public.projects (
  id          uuid primary key default gen_random_uuid(),
  company_id  uuid not null references public.companies(id) on delete restrict,
  slug        text unique not null,
  nombre      text not null,
  es_real     boolean not null default false,
  fase        text not null default 'construccion'
              check (fase in ('prefactibilidad','aprobado','construccion','entregado')),
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now(),
  updated_by  text
);

-- 3) Escenarios versionados (snapshot JSONB = el `par` COMPLETO, sin tocar) -----
create table if not exists public.scenarios (
  id          uuid primary key default gen_random_uuid(),
  project_id  uuid not null references public.projects(id) on delete cascade,
  version     integer not null,
  status      text not null default 'draft'
              check (status in ('draft','approved','baseline')),
  snapshot    jsonb not null,
  label       text,
  created_at  timestamptz not null default now(),
  created_by  text,
  unique (project_id, version)
);
-- A lo sumo UN baseline activo por proyecto (la constitución: "un solo baseline por proyecto").
create unique index if not exists scenarios_un_baseline_por_proyecto
  on public.scenarios (project_id) where (status = 'baseline');

-- 4) Caché de resultados (derivada: se puede borrar y recomputar) --------------
--    Clave de invalidación: hash(snapshot) + engine_version.
create table if not exists public.results_cache (
  id             uuid primary key default gen_random_uuid(),
  scenario_id    uuid not null unique references public.scenarios(id) on delete cascade,
  engine_version text not null,
  inputs_hash    text not null,
  results        jsonb not null,
  computed_at    timestamptz not null default now()
);

-- 5) Ejecutados (datos ex-post, solo fases con seguimiento) --------------------
--    OJO: fecha_corte NO es hoy; es el corte de los datos del comité.
create table if not exists public.actuals_evm (
  id           uuid primary key default gen_random_uuid(),
  project_id   uuid not null references public.projects(id) on delete cascade,
  fecha_corte  date not null,
  pv numeric, ev numeric, ac numeric, spi numeric, cpi numeric,
  fuente       text check (fuente in ('manual','excel','erp','crm')),
  created_at   timestamptz not null default now(),
  unique (project_id, fecha_corte)
);
create table if not exists public.actuals_recaudo (
  id          uuid primary key default gen_random_uuid(),
  project_id  uuid not null references public.projects(id) on delete cascade,
  periodo     text not null,                    -- 'YYYY-MM'
  und         numeric, valor numeric,
  fuente      text check (fuente in ('manual','excel','erp','crm')),
  unique (project_id, periodo)
);

-- 6) Auditoría de cambios -----------------------------------------------------
create table if not exists public.audit_log (
  id           uuid primary key default gen_random_uuid(),
  entity_type  text not null,                   -- 'project' | 'scenario' | …
  entity_id    uuid,
  action       text not null,                   -- 'import_v1' | 'create_draft' | 'approve' | …
  actor        text,
  diff         jsonb,
  at           timestamptz not null default now()
);

-- Índices de apoyo
create index if not exists projects_company_idx  on public.projects(company_id);
create index if not exists scenarios_project_idx on public.scenarios(project_id);
create index if not exists audit_entity_idx      on public.audit_log(entity_type, entity_id);

-- RLS: se ACTIVA (deny-by-default). La app y la API usan la `service_role`, que BYPASEA RLS, así que
-- esto NO rompe nada hoy y bloquea acceso anónimo/authenticated accidental. Las políticas granulares
-- por rol (admin edita / gerencia lee) se añaden cuando /web acceda con tokens de usuario (no hoy).
alter table public.companies     enable row level security;
alter table public.projects      enable row level security;
alter table public.scenarios     enable row level security;
alter table public.results_cache enable row level security;
alter table public.actuals_evm   enable row level security;
alter table public.actuals_recaudo enable row level security;
alter table public.audit_log     enable row level security;

-- Seed: empresa CG Constructora (idempotente por slug)
insert into public.companies (slug, nombre)
values ('cg-constructora', 'CG Constructora S.A.S.')
on conflict (slug) do nothing;
