import type { Especialista } from "@/types";
import { Card } from "@/components/ui/card";
import { Compass, ShieldCheck, Wrench, Activity } from "lucide-react";

const ICONOS: Record<string, JSX.Element> = {
  estrategia: <Compass className="size-4" />,
  arquitectura: <ShieldCheck className="size-4" />,
  implementacion: <Wrench className="size-4" />,
  operacion: <Activity className="size-4" />,
};

export function EspecialistasGrid({ especialistas }: { especialistas: Especialista[] }) {
  return (
    <div className="grid gap-2.5">
      {especialistas.map((e) => (
        <Card key={e.id} className="group flex items-start gap-3 p-3.5 transition-colors hover:border-neutral-400">
          <div className="flex size-9 shrink-0 items-center justify-center rounded-md bg-neutral-100 text-neutral-700">
            {ICONOS[e.id] ?? <Compass className="size-4" />}
          </div>
          <div className="min-w-0">
            <div className="text-sm font-semibold text-foreground">{e.nombre}</div>
            <div className="mt-0.5 text-xs leading-relaxed text-muted-foreground">{e.resumen}</div>
            <div className="mt-1.5 text-[11px] font-medium text-neutral-500">{e.foco}</div>
          </div>
        </Card>
      ))}
    </div>
  );
}

