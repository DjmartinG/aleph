import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { ProyectoForm } from "@/components/forms/nuevo-proyecto-form";

export const metadata = { title: "Nuevo proyecto · ALEPH" };

export default function NuevoProyectoPage() {
  return (
    <div className="mx-auto w-full max-w-4xl px-4 py-9 sm:px-6 lg:px-8">
      <Link
        href="/"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="size-4" aria-hidden /> Portafolio
      </Link>

      <header className="mb-8">
        <h1 className="text-xl font-semibold tracking-tight">Nuevo proyecto</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Ingresa los datos del proyecto. Al guardar, el motor de ALEPH calcula los indicadores y el
          proyecto queda en el portafolio.
        </p>
      </header>

      <ProyectoForm />
    </div>
  );
}
