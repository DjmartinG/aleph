import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, Pencil } from "lucide-react";
import { getProject, getResults, getSensitivity, getSchedule, getWacc, getVehiculos } from "@/lib/api";
import { isAdminUser } from "@/lib/session";
import { fmtInt } from "@/lib/format";
import { PhaseBadge } from "@/components/phase-badge";
import { FichaTabs } from "@/components/views/ficha-tabs";
import { AdminMenu } from "@/components/admin/admin-menu";

export default async function ProyectoPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const [project, results, sensitivity, schedule, wacc, vehiculos, admin] = await Promise.all([
    getProject(slug),
    getResults(slug),
    getSensitivity(slug),
    getSchedule(slug),
    getWacc(slug),
    getVehiculos(slug),
    isAdminUser(),
  ]);
  if (!project || !results) notFound();

  const { meta, estado, es_real } = project;

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-9 sm:px-6 lg:px-8">
      <Link
        href="/"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="size-4" aria-hidden /> Portafolio
      </Link>

      <header className="mb-7 flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-semibold tracking-tight">{meta.nombre}</h1>
            <PhaseBadge estado={estado} />
            {!es_real ? (
              <span className="rounded bg-muted px-1.5 py-0.5 text-[0.7rem] font-medium text-muted-foreground">
                ilustrativo
              </span>
            ) : null}
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            {[meta.ubicacion, meta.zona, meta.tipo].filter(Boolean).join(" · ")}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {meta.unidades ? (
            <span className="num whitespace-nowrap rounded-full border bg-card px-3 py-1 text-xs text-muted-foreground">
              {fmtInt(meta.unidades)} unidades
            </span>
          ) : null}
          {admin ? (
            <Link
              href={`/proyectos/${slug}/editar`}
              className="inline-flex items-center gap-1.5 rounded-[var(--radius-data)] border border-primary/40 px-3 py-1.5 text-sm font-medium text-primary transition-[color,background-color,transform] [transition-timing-function:var(--ease-out)] hover:bg-primary/10 active:scale-[0.98]"
            >
              <Pencil className="size-3.5" aria-hidden /> Editar
            </Link>
          ) : null}
          {admin ? <AdminMenu slug={slug} nombre={meta.nombre} esReal={es_real} /> : null}
        </div>
      </header>

      <FichaTabs project={project} results={results} sensitivity={sensitivity} schedule={schedule} wacc={wacc} vehiculos={vehiculos} />
    </div>
  );
}
