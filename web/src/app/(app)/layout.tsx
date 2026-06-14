import { Sidebar } from "@/components/sidebar";
import { Topbar } from "@/components/topbar";
import { APP_VERSION, commitSha } from "@/lib/version";

/** Shell de la app (sidebar + topbar). Solo envuelve las rutas autenticadas; /login queda fuera. */
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar />
        <main className="flex-1">{children}</main>
        <footer className="border-t px-4 py-2.5 sm:px-6">
          <div className="mx-auto flex max-w-7xl items-center justify-between text-xs text-muted-foreground">
            <span>CG Constructora S.A.S.</span>
            <span className="num">ALEPH v{APP_VERSION}{commitSha() ? ` · ${commitSha()}` : ""}</span>
          </div>
        </footer>
      </div>
    </div>
  );
}
