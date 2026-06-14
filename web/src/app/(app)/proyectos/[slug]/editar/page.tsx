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
  // Los proyectos con `tipologias` (mezcla de unidades por torre/clase) NO son editables por este
  // formulario simple: el motor re-deriva und/precio/ventas desde el bloque de tipologías, así que un
  // cambio aquí se descartaría EN SILENCIO. Se bloquea honestamente hasta tener edición de tipologías.
  const tieneTipologias = source.par.tipologias != null;

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

      {tieneTipologias ? (
        <div className="flex items-start gap-3 rounded-[var(--radius-data)] border border-warning/30 bg-warning/5 p-5 text-sm">
          <Info className="mt-0.5 size-5 shrink-0 text-warning" aria-hidden />
          <div className="space-y-2">
            <p className="font-medium text-foreground">Este proyecto usa tipologías y aún no es editable aquí.</p>
            <p className="text-muted-foreground">
              Sus unidades y precios vienen de una <strong>mezcla de tipologías</strong> (por torre/clase). El
              motor las re-deriva de ese bloque, así que editarlas en este formulario simple se descartaría
              sin aviso. La edición de tipologías llega en una fase dedicada. Mientras tanto, los datos de
              este proyecto se conservan intactos.
            </p>
            <Link
              href={`/proyectos/${slug}`}
              className="inline-flex items-center gap-1.5 pt-1 text-sm font-medium text-primary hover:underline"
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
