import { Badge } from "@/components/ui/badge";
import type { FaseCaf } from "@/types";
import { Compass, PackageCheck } from "lucide-react";

export function CafCard({ titulo, foco, fases }: { titulo: string; foco?: string; fases: FaseCaf[] }) {
  return (
    <div className="rounded-lg border border-border bg-white p-4">
      <div className="mb-3 flex items-center gap-2">
        <Compass className="size-4 text-neutral-700" />
        <span className="text-sm font-semibold text-foreground">{titulo}</span>
        {foco && <Badge variant="secondary" className="ml-auto font-normal">{foco}</Badge>}
      </div>
      <ol className="relative space-y-3 border-l border-border pl-4">
        {fases.filter(Boolean).map((f) => (
          <li key={f.id} className="relative">
            <span className="absolute -left-[21px] top-1 size-2.5 rounded-full bg-neutral-800 ring-4 ring-white" />
            <div className="text-sm font-medium text-foreground">{f.nombre}</div>
            <div className="text-xs text-muted-foreground">{f.objetivo}</div>
            <div className="mt-1.5 flex flex-wrap gap-1.5">
              {f.actividades.map((a) => (
                <span key={a} className="rounded border border-border bg-neutral-50 px-2 py-0.5 text-[11px] text-neutral-700">
                  {a}
                </span>
              ))}
            </div>
            {f.entregables?.length > 0 && (
              <div className="mt-1 flex flex-wrap items-center gap-1 text-[11px] text-muted-foreground">
                <PackageCheck className="size-3" />
                {f.entregables.join(" · ")}
              </div>
            )}
          </li>
        ))}
      </ol>
    </div>
  );
}

