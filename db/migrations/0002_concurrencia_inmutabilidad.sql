-- ============================================================================
-- ALEPH · Migración 0002 — Fase 3: concurrencia optimista + inmutabilidad del snapshot
-- (camino de escritura, ver directives/plan_escritura.md)
--
-- ADITIVA e IDEMPOTENTE (IF NOT EXISTS / CREATE OR REPLACE): se puede correr varias veces y NO
-- rompe nada existente. Añade a `scenarios`:
--   (1) `updated_at` + trigger que lo bumpea en cada UPDATE → ETag para concurrencia optimista
--       (el cliente manda el updated_at que leyó; si cambió, su UPDATE no afecta filas → 409 en el API).
--   (2) trigger de INMUTABILIDAD: una vez fuera de 'draft' (approved/baseline), el `snapshot` y la
--       `version` NO se pueden alterar (garantía DURA en la BD, no solo disciplina de la app). Editar
--       un aprobado = crear un escenario NUEVO (lo hace el API).
--
-- Ejecutar: pegar en el SQL Editor de Supabase. Después: redeploy del API (que usa If-Match).
-- ============================================================================

-- (1) Concurrencia optimista: updated_at + bump por trigger -------------------
alter table public.scenarios add column if not exists updated_at timestamptz not null default now();

create or replace function public.set_updated_at() returns trigger as $$
begin
  new.updated_at := now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists scenarios_set_updated_at on public.scenarios;
create trigger scenarios_set_updated_at
  before update on public.scenarios
  for each row execute function public.set_updated_at();

-- (2) Inmutabilidad del snapshot fuera de 'draft' -----------------------------
-- Si el escenario ya NO es draft (approved/baseline), rechaza cambios a snapshot o version.
-- Sí permite cambiar SOLO el status (draft→approved, approved→baseline, baseline→approved) y updated_at.
create or replace function public.scenarios_inmutable() returns trigger as $$
begin
  if old.status <> 'draft' then
    if new.snapshot is distinct from old.snapshot or new.version is distinct from old.version then
      raise exception 'scenario % es inmutable (status=%): snapshot/version no se pueden cambiar; crea un escenario nuevo',
        old.id, old.status;
    end if;
  end if;
  return new;
end;
$$ language plpgsql;

-- Nombre alfabéticamente ANTES de set_updated_at → la validación de inmutabilidad corre primero.
drop trigger if exists scenarios_inmutable on public.scenarios;
create trigger scenarios_inmutable
  before update on public.scenarios
  for each row execute function public.scenarios_inmutable();
