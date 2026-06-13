import { Skeleton } from "@/components/skeleton";

export default function Loading() {
  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-9 sm:px-6 lg:px-8">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="mt-5 h-7 w-56" />
      <Skeleton className="mt-2 h-4 w-44" />

      <div className="mt-7 overflow-hidden rounded-[var(--radius-data)] border bg-rule">
        <div className="grid grid-cols-2 gap-px sm:grid-cols-3 xl:grid-cols-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="space-y-2 bg-card p-4">
              <Skeleton className="h-3 w-16" />
              <Skeleton className="h-6 w-24" />
              <Skeleton className="h-2.5 w-14" />
            </div>
          ))}
        </div>
      </div>

      <Skeleton className="mt-4 h-20 w-full rounded-[var(--radius-data)]" />
      <Skeleton className="mt-9 h-16 w-full rounded-[var(--radius-data)]" />
      <Skeleton className="mt-9 h-80 w-full rounded-[var(--radius-data)]" />
    </div>
  );
}
