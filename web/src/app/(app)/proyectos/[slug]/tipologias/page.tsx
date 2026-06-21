import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, Info } from "lucide-react";
import { getProjectSource, type Tipologia } from "@/lib/api";
import { isAdminUser } from "@/lib/session";
import { TipologiasForm } from "@/components/forms/tipologias-form";

export const metadata = { title: "Editar tipologías · ALEPH" };

export default async function EditarTipologiasPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  if (!(await isAdminUser())) notFound();

  const source = await getProjectSource(slug);
  if (!source) notFound();

  const par = source.par;
  const tip = par.tipologias as Tipologia[] | undefined;
  // Este editor es SOLO para proyectos que YA usan tipologías (crear desde cero es otra fase).
  if (!Array.isArray(tip) || tip.length === 0) notFound();

  const etapas = (par.etapas as { cod?: number; sucesora?: unknown }[] | undefined) ?? [];
  const cods = etapas.map((e) => e.cod).filter((c): c is number => typeof c === "number");
  const tieneCadena = etapas.some((e) => e.sucesora != null);
  const nombre = (par.meta as { nombre?: string; tipo?: string } | undefined)?.nombre || slug;
  const esVis = ["VIS", "VIP"].includes(String((par.meta as { tipo?: string } | undefined)?.tipo ?? "").trim().toUpperCase());

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-9 sm:px-6 lg:px-8">
      <Link href={`/proyectos/${slug}`} className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground">
        <ArrowLeft className="size-4" aria-hidden /> {nombre}
      </Link>

      <header className="mb-8">
        <h1 className="text-xl font-semibold tracking-tight">Editar mezcla de tipologías</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Ajusta unidades, precio y clase por tipología. Se guarda como versión nueva (v{source.version + 1}) y
          el <strong>motor re-deriva</strong> unidades y ventas de la tabla (no se editan los campos derivados a
          mano, así no se corrompen las cifras).
        </p>
      </header>

      {tieneCadena ? (
        <div className="flex items-start gap-3 rounded-[var(--radius-data)] border border-warning/30 bg-warning/5 p-5 text-sm">
          <Info className="mt-0.5 size-5 shrink-0 text-warning" aria-hidden />
          <div className="space-y-2">
            <p className="font-medium text-foreground">Este proyecto aún no es editable aquí.</p>
            <p className="text-muted-foreground">
              Sus etapas están <strong>encadenadas</strong> (cada una arranca en el hito de la anterior); editar
              la mezcla podría mover el cronograma. Se bloquea hasta soportar esa estructura; los datos quedan intactos.
            </p>
            <Link href={`/proyectos/${slug}`} className="inline-flex items-center gap-1.5 pt-1 text-sm font-medium text-primary hover:underline">
              <ArrowLeft className="size-4" aria-hidden /> Volver a la ficha
            </Link>
          </div>
        </div>
      ) : (
        <TipologiasForm slug={slug} cods={cods} esVis={esVis} tipologias={tip} />
      )}
    </div>
  );
}
