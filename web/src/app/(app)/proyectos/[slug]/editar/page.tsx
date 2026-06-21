import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, Info } from "lucide-react";
import { getProjectSource } from "@/lib/api";
import { isAdminUser } from "@/lib/session";
import { ProyectoForm, parseParToForm } from "@/components/forms/nuevo-proyecto-form";

export const metadata = { title: "Editar proyecto · ALEPH" };

export default async function EditarProyectoPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  // Gate de UI: solo admins editan (el API también lo exige; esto evita renderizar la pantalla).
  if (!(await isAdminUser())) notFound();

  const source = await getProjectSource(slug);
  if (!source) notFound();

  const initial = parseParToForm(source.par);
  const nombre = initial.meta.nombre || slug;
  // Dos estructuras NO son editables por este formulario simple (lo cambiarían en silencio):
  // (1) `tipologias` (mezcla de unidades por torre/clase): el motor re-deriva und/precio/ventas de ahí.
  // (2) Cadena `sucesora` (etapas encadenadas al hito de la anterior, sin fecha propia): el formulario
  //     es DATADO (fuerza sucesora=null + exige fecha por etapa), así que editarlas moverÍa el
  //     cronograma "sin querer". Se bloquean honestamente hasta soportar cada estructura.
  const tieneTipologias = source.par.tipologias != null;
  const etapasArr = (source.par.etapas as { sucesora?: unknown }[] | undefined) ?? [];
  const tieneCadena = etapasArr.some((e) => e.sucesora != null);
  const bloqueado = tieneTipologias || tieneCadena;
  // Mostrar TODAS las causas (no solo la primera): un proyecto puede tener AMBas a la vez.
  const razones: string[] = [];
  if (tieneTipologias)
    razones.push("sus unidades y precios vienen de una mezcla de tipologías (por torre/clase) que el motor re-deriva de ese bloque");
  if (tieneCadena)
    razones.push("sus etapas están encadenadas (cada una arranca en el hito de la anterior, sin fecha propia) y este formulario usa fechas explícitas");
  const razonBloqueo = razones.join("; ") + ".";
  // La mezcla de tipologías SÍ es editable en su propio editor seguro (mientras no haya cadena de etapas).
  const puedeEditarTipologias = tieneTipologias && !tieneCadena;

  return (
    <div className="mx-auto w-full max-w-4xl px-4 py-9 sm:px-6 lg:px-8">
      <Link
        href={`/proyectos/${slug}`}
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="size-4" aria-hidden /> {nombre}
      </Link>

      <header className="mb-8">
        <h1 className="text-xl font-semibold tracking-tight">Editar proyecto</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Ajusta los datos y guarda. Se crea una versión nueva (v{source.version + 1}) y se aprueba; el
          motor recalcula los indicadores. La versión anterior queda en el historial.
        </p>
      </header>

      {bloqueado ? (
        <div className="flex items-start gap-3 rounded-[var(--radius-data)] border border-warning/30 bg-warning/5 p-5 text-sm">
          <Info className="mt-0.5 size-5 shrink-0 text-warning" aria-hidden />
          <div className="space-y-2">
            <p className="font-medium text-foreground">Este proyecto aún no es editable aquí.</p>
            <p className="text-muted-foreground">
              Este formulario simple no aplica porque {razonBloqueo} Editarlo aquí <strong>movería sus cifras
              sin querer</strong>, así que se bloquea honestamente; los datos se conservan intactos.
            </p>
            {puedeEditarTipologias ? (
              <Link
                href={`/proyectos/${slug}/tipologias`}
                className="inline-flex items-center gap-1.5 rounded-[var(--radius-data)] border border-primary/40 px-3 py-1.5 text-sm font-medium text-primary transition-[color,background-color] [transition-timing-function:var(--ease-out)] hover:bg-primary/10"
              >
                Editar la mezcla de tipologías →
              </Link>
            ) : null}
            <Link
              href={`/proyectos/${slug}`}
              className="inline-flex items-center gap-1.5 pt-1 text-sm font-medium text-muted-foreground hover:text-foreground"
            >
              <ArrowLeft className="size-4" aria-hidden /> Volver a la ficha
            </Link>
          </div>
        </div>
      ) : (
        <ProyectoForm
          mode="edit"
          slug={slug}
          projectId={source.project_id}
          originalPar={source.par}
          initial={initial}
        />
      )}
    </div>
  );
}
