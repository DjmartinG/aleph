import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { getProjectSource, getResults } from "@/lib/api";
import { isAdminUser } from "@/lib/session";
import { ViabilidadForm } from "@/components/forms/viabilidad-form";

export const metadata = { title: "Editar viabilidad · ALEPH" };

export default async function EditarViabilidadPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  // Gate de UI: solo admins (el API también lo exige).
  if (!(await isAdminUser())) notFound();

  const [source, results] = await Promise.all([getProjectSource(slug), getResults(slug)]);
  if (!source || !results || !results.due_diligence) notFound();

  const nombre = (source.par.meta as { nombre?: string } | undefined)?.nombre || slug;

  return (
    <div className="mx-auto w-full max-w-4xl px-4 py-9 sm:px-6 lg:px-8">
      <Link
        href={`/proyectos/${slug}`}
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="size-4" aria-hidden /> {nombre}
      </Link>

      <header className="mb-8">
        <h1 className="text-xl font-semibold tracking-tight">Editar viabilidad</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Diligencia el due diligence (legal, ambiental, urbanístico, técnico, bancario), los límites POT
          de la zona y los comparables de mercado. Se guarda como versión nueva (v{source.version + 1}); el
          motor recalcula, pero <strong>las cifras financieras no cambian</strong> (estos registros son
          cualitativos). Esto funciona aunque el proyecto use tipologías o etapas encadenadas.
        </p>
      </header>

      <ViabilidadForm
        slug={slug}
        frentes={results.due_diligence.frentes}
        ddItems={results.due_diligence.items}
        pot={(source.par.pot as Record<string, unknown>) ?? {}}
        mercado={(source.par.mercado as Record<string, unknown>) ?? {}}
      />
    </div>
  );
}
