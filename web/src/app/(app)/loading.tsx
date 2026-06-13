import { Skeleton } from "@/components/skeleton";

export default function Loading() {
  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <Skeleton className="h-7 w-40" />
      <Skeleton className="mt-2 h-4 w-72" />

      <div className="mt-6 overflow-hidden rounded-xl border bg-border">
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

      <Skeleton className="mt-8 h-24 w-full rounded-xl" />
      <Skeleton className="mt-8 h-72 w-full rounded-xl" />
    </div>
  );
}
