import { Badge } from "@/components/ui/badge";
import type { Estandar } from "@/types";
import { BadgeCheck, CircleSlash, ExternalLink } from "lucide-react";

type Props = { titulo: string; foco?: string; revisado?: string; estandares: Estandar[] };

export function EstandaresCard({ titulo, foco, revisado, estandares }: Props) {
  return (
    <div className="rounded-lg border border-border bg-white p-4">
      <div className="mb-3 flex items-center gap-2">
        <BadgeCheck className="size-4 text-neutral-700" />
        <span className="text-sm font-semibold text-foreground">{titulo}</span>
        {foco && <Badge variant="secondary" className="ml-auto font-normal">{foco}</Badge>}
      </div>
      <div className="space-y-3">
        {estandares.filter(Boolean).map((e) => (
          <div key={e.id} className="rounded-md border border-border bg-neutral-50 p-3">
            <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              {e.area}
            </div>
            <div className="mt-0.5 flex items-start gap-1.5 text-sm font-medium text-foreground">
              <BadgeCheck className="mt-[2px] size-3.5 shrink-0 text-emerald-600" />
              {e.vigente}
            </div>
            <p className="mt-1 text-xs text-muted-foreground">{e.detalle}</p>
            {e.evitar?.length > 0 && (
              <ul className="mt-1.5 space-y-0.5">
                {e.evitar.map((x) => (
                  <li key={x} className="flex items-start gap-1.5 text-[11px] text-neutral-700">
                    <CircleSlash className="mt-[2px] size-3 shrink-0 text-amber-600" />
                    {x}
                  </li>
                ))}
              </ul>
            )}
            {e.url && (
              <a
                href={e.url}
                target="_blank"
                rel="noreferrer"
                className="mt-1.5 inline-flex items-center gap-1 text-[11px] text-neutral-600 underline-offset-2 hover:underline"
              >
                <ExternalLink className="size-3" />
                Referencia oficial
              </a>
            )}
          </div>
        ))}
      </div>
      {revisado && (
        <p className="mt-2 text-[11px] text-muted-foreground">
          Línea base revisada en {revisado} · el asesor revalida el estado GA/Preview en Microsoft Learn.
        </p>
      )}
    </div>
  );
}
