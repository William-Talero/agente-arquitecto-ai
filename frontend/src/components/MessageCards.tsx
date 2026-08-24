import type { Cita, Tarjeta } from "@/types";
import { CafCard } from "./cards/CafCard";
import { WafCard } from "./cards/WafCard";
import { CicloCard } from "./cards/CicloCard";
import { ArquitecturaCard } from "./cards/ArquitecturaCard";
import { EstandaresCard } from "./cards/EstandaresCard";
import { LineamientosCard } from "./cards/LineamientosCard";
import { BookOpen, Globe, Link2 } from "lucide-react";

export function MessageCards({ tarjetas }: { tarjetas: Tarjeta[] }) {
  if (!tarjetas?.length) return null;
  return (
    <div className="mt-3 space-y-3">
      {tarjetas.map((t, i) => {
        if (t.tipo === "caf") return <CafCard key={i} titulo={t.titulo} foco={t.foco} fases={t.fases} />;
        if (t.tipo === "waf") return <WafCard key={i} titulo={t.titulo} foco={t.foco} pilares={t.pilares} />;
        if (t.tipo === "ciclo") return <CicloCard key={i} titulo={t.titulo} foco={t.foco} etapas={t.etapas} />;
        if (t.tipo === "estandares")
          return (
            <EstandaresCard
              key={i}
              titulo={t.titulo}
              foco={t.foco}
              revisado={t.revisado}
              estandares={t.estandares}
            />
          );
        if (t.tipo === "lineamientos")
          return (
            <LineamientosCard key={i} titulo={t.titulo} foco={t.foco} lineamientos={t.lineamientos} />
          );
        if (t.tipo === "arquitectura")
          return (
            <ArquitecturaCard
              key={i}
              titulo={t.titulo}
              drawio={t.drawio}
              zonas={t.zonas}
              n_servicios={t.n_servicios}
              n_conexiones={t.n_conexiones}
            />
          );
        return null;
      })}
    </div>
  );
}

export function Citas({ citas }: { citas: Cita[] }) {
  if (!citas?.length) return null;
  return (
    <div className="mt-3 rounded-lg border border-border bg-neutral-50 p-3">
      <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-muted-foreground">
        <Link2 className="size-3.5" />
        Fuentes citadas
      </div>
      <div className="flex flex-col gap-1.5">
        {citas.map((c) => (
          <a
            key={c.url}
            href={c.url}
            target="_blank"
            rel="noreferrer"
            className="group flex items-start gap-2 text-xs text-neutral-700 hover:text-[hsl(var(--brand))]"
          >
            {c.fuente === "learn" ? (
              <BookOpen className="mt-[1px] size-3.5 shrink-0 text-neutral-500" />
            ) : (
              <Globe className="mt-[1px] size-3.5 shrink-0 text-neutral-500" />
            )}
            <span className="truncate underline-offset-2 group-hover:underline">{c.titulo}</span>
          </a>
        ))}
      </div>
    </div>
  );
}
