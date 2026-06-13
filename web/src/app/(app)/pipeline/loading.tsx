import { Skeleton } from "@/components/skeleton";

export default function Loading() {
  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-9 sm:px-6 lg:px-8">
      <Skeleton className="h-6 w-28" />
      <Skeleton className="mt-2 h-4 w-56" />
      <div className="mt-7 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="space-y-3 rounded-[var(--radius-data)] border bg-sidebar/40 p-3">
            <Skeleton className="h-5 w-24" />
            <Skeleton className="h-24 w-full rounded-[var(--radius-data)]" />
            <Skeleton className="h-24 w-full rounded-[var(--radius-data)]" />
          </div>
        ))}
      </div>
    </div>
  );
}
