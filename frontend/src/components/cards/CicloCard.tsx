import { Badge } from "@/components/ui/badge";
import type { EtapaCiclo } from "@/types";
import { Workflow, Dot } from "lucide-react";

export function CicloCard({ titulo, foco, etapas }: { titulo: string; foco?: string; etapas: EtapaCiclo[] }) {
  return (
    <div className="rounded-lg border border-border bg-white p-4">
      <div className="mb-3 flex items-center gap-2">
        <Workflow className="size-4 text-neutral-700" />
        <span className="text-sm font-semibold text-foreground">{titulo}</span>
        {foco && <Badge variant="secondary" className="ml-auto font-normal">{foco}</Badge>}
      </div>
      <div className="flex flex-col gap-2">
        {etapas.filter(Boolean).map((e, i) => (
          <div key={e.id} className="flex items-start gap-3 rounded-md border border-border bg-neutral-50 p-2.5">
            <div className="flex size-6 shrink-0 items-center justify-center rounded-full bg-neutral-800 text-xs font-semibold text-white">
              {i + 1}
            </div>
            <div className="min-w-0">
              <div className="text-sm font-medium text-foreground">{e.nombre}</div>
              <div className="text-xs text-muted-foreground">{e.descripcion}</div>
              <div className="mt-1 flex flex-wrap items-center gap-x-1 gap-y-0.5 text-[11px] text-neutral-600">
                {e.practicas.map((p, idx) => (
                  <span key={p} className="inline-flex items-center">
                    {idx > 0 && <Dot className="size-3 text-neutral-400" />}
                    {p}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

