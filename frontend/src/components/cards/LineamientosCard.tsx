import { Badge } from "@/components/ui/badge";
import { ShieldCheck, FileText } from "lucide-react";

type Item = { id: string; nombre: string; ambito: string; categoria?: string; caracteres?: number };

export function LineamientosCard({
  titulo,
  foco,
  lineamientos,
}: {
  titulo: string;
  foco?: string;
  lineamientos: Item[];
}) {
  return (
    <div className="rounded-lg border border-border bg-white p-4">
      <div className="mb-3 flex items-center gap-2">
        <ShieldCheck className="size-4 text-neutral-700" />
        <span className="text-sm font-semibold text-foreground">{titulo}</span>
        {foco && <Badge variant="secondary" className="ml-auto font-normal">{foco}</Badge>}
      </div>
      <ul className="space-y-1.5">
        {lineamientos.filter(Boolean).map((l) => (
          <li key={l.id} className="flex items-start gap-2 rounded-md border border-border bg-neutral-50 px-2.5 py-1.5">
            <FileText className="mt-[2px] size-3.5 shrink-0 text-muted-foreground" />
            <span className="min-w-0">
              <span className="block truncate text-sm text-foreground">{l.nombre}</span>
              <span className="block text-[11px] text-muted-foreground">
                {l.ambito === "global" ? "Todos los especialistas" : l.ambito}
                {l.categoria ? ` · ${l.categoria}` : ""}
              </span>
            </span>
          </li>
        ))}
      </ul>
      <p className="mt-2 text-[11px] text-muted-foreground">
        Reglas propias del negocio aplicadas a esta recomendación.
      </p>
    </div>
  );
}
