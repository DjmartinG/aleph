"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, GitBranch, type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

type NavItem = { href: string; label: string; icon: LucideIcon; soon?: boolean };
type NavGroup = { group: string; items: NavItem[] };

const NAV: NavGroup[] = [
  {
    group: "Portafolio",
    items: [
      { href: "/", label: "Tablero", icon: LayoutDashboard },
      { href: "/pipeline", label: "Pipeline", icon: GitBranch, soon: true },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="hidden w-60 shrink-0 flex-col border-r bg-sidebar text-sidebar-foreground md:flex">
      <div className="flex h-14 items-center gap-2.5 border-b px-5">
        <span className="size-2.5 rounded-full bg-primary" aria-hidden />
        <span className="font-semibold tracking-tight text-foreground">ALEPH</span>
      </div>

      <nav className="flex-1 space-y-6 px-3 py-5">
        {NAV.map((g) => (
          <div key={g.group}>
            <div className="mb-1.5 px-2 text-[0.7rem] font-semibold uppercase tracking-wider text-muted-foreground">
              {g.group}
            </div>
            <ul className="space-y-0.5">
              {g.items.map((it) => {
                const active = pathname === it.href;
                const Icon = it.icon;
                const content = (
                  <>
                    <Icon
                      className={cn("size-4", active ? "text-primary" : "text-muted-foreground")}
                    />
                    <span className="flex-1">{it.label}</span>
                    {it.soon ? (
                      <span className="rounded bg-muted px-1.5 py-0.5 text-[0.65rem] font-medium text-muted-foreground">
                        pronto
                      </span>
                    ) : null}
                  </>
                );
                if (it.soon) {
                  return (
                    <li key={it.href}>
                      <span className="flex cursor-default items-center gap-2.5 rounded-md px-2 py-1.5 text-sm font-medium text-muted-foreground/70">
                        {content}
                      </span>
                    </li>
                  );
                }
                return (
                  <li key={it.href}>
                    <Link
                      href={it.href}
                      aria-current={active ? "page" : undefined}
                      className={cn(
                        "flex items-center gap-2.5 rounded-md px-2 py-1.5 text-sm font-medium transition-colors",
                        active
                          ? "bg-accent text-accent-foreground"
                          : "text-sidebar-foreground hover:bg-accent/60 hover:text-accent-foreground",
                      )}
                    >
                      {content}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      <div className="border-t px-5 py-3 text-xs text-muted-foreground">
        CG Constructora S.A.S.
      </div>
    </aside>
  );
}
