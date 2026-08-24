import { Badge } from "@/components/ui/badge";
import type { PilarWaf } from "@/types";
import { ShieldCheck, Check, AlertTriangle } from "lucide-react";

export function WafCard({ titulo, foco, pilares }: { titulo: string; foco?: string; pilares: PilarWaf[] }) {
  return (
    <div className="rounded-lg border border-border bg-white p-4">
      <div className="mb-3 flex items-center gap-2">
        <ShieldCheck className="size-4 text-neutral-700" />
        <span className="text-sm font-semibold text-foreground">{titulo}</span>
        {foco && <Badge variant="secondary" className="ml-auto font-normal">{foco}</Badge>}
      </div>
      <div className="grid gap-2.5 sm:grid-cols-2">
        {pilares.filter(Boolean).map((p) => (
          <div key={p.id} className="rounded-md border border-border bg-neutral-50 p-3">
            <div className="text-sm font-medium text-foreground">{p.nombre}</div>
            <div className="mt-0.5 text-[11px] italic text-muted-foreground">{p.pregunta_clave}</div>
            <ul className="mt-2 space-y-1">
              {p.consideraciones_ai.map((c) => (
                <li key={c} className="flex items-start gap-1.5 text-[11px] text-neutral-700">
                  <Check className="mt-[1px] size-3 shrink-0 text-neutral-500" />
                  {c}
                </li>
              ))}
            </ul>
            {p.antipatrones?.length > 0 && (
              <div className="mt-1.5 flex items-start gap-1.5 text-[11px] text-amber-700">
                <AlertTriangle className="mt-[1px] size-3 shrink-0" />
                {p.antipatrones.join(" · ")}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

