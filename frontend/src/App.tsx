import { useEffect, useState } from "react";
import type { Catalogo } from "./types";
import { obtenerCatalogo, obtenerSalud } from "./api";
import { useConversaciones } from "./useConversaciones";
import { EspecialistasGrid } from "./components/EspecialistasGrid";
import { MarcoExplorer } from "./components/MarcoExplorer";
import { ChatPanel } from "./components/ChatPanel";
import { LineamientosPanel } from "./components/LineamientosPanel";
import { Button } from "./components/ui/button";
import { ScrollArea } from "./components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogTrigger,
} from "./components/ui/dialog";
import { Boxes, BookOpen, Globe, LayoutGrid, SquarePen, History, Trash2, MessageSquare, ShieldCheck } from "lucide-react";

function fechaRelativa(ts: number): string {
  const s = Math.floor((Date.now() - ts) / 1000);
  if (s < 60) return "hace un momento";
  if (s < 3600) return `hace ${Math.floor(s / 60)} min`;
  if (s < 86400) return `hace ${Math.floor(s / 3600)} h`;
  return new Date(ts).toLocaleDateString("es", { day: "2-digit", month: "short" });
}

export default function App() {
  const [catalogo, setCatalogo] = useState<Catalogo | null>(null);
  const [listo, setListo] = useState<boolean | null>(null);
  const [histOpen, setHistOpen] = useState(false);
  const { conversaciones, activa, actualizarMensajes, nuevaConversacion, seleccionar, eliminar } =
    useConversaciones();

  useEffect(() => {
    obtenerCatalogo().then(setCatalogo).catch(() => setCatalogo(null));
    obtenerSalud()
      .then((s) => setListo(s.advisor_ready))
      .catch(() => setListo(false));
  }, []);

  return (
    <div className="flex h-screen flex-col">
      <header className="shrink-0 border-b border-border bg-white">
        <div className="mx-auto flex w-full max-w-4xl items-center gap-3 px-4 py-3">
          <div className="flex size-9 items-center justify-center rounded-md bg-foreground">
            <Boxes className="size-5 text-white" />
          </div>
          <div className="min-w-0">
            <h1 className="truncate text-[15px] font-semibold tracking-tight text-foreground">
              Arquitecto de Soluciones AI
            </h1>
            <p className="hidden truncate text-xs text-muted-foreground sm:block">
              Asesor de arquitectura y ciclo de vida de IA · CAF · Well-Architected
            </p>
          </div>
          <div className="ml-auto flex items-center gap-1.5">
            <div className="mr-1 hidden items-center gap-1.5 rounded-full border border-border px-2.5 py-1 text-xs text-muted-foreground md:flex">
              <span
                className={`size-1.5 rounded-full ${
                  listo === null ? "bg-neutral-300" : listo ? "bg-emerald-500" : "bg-amber-500"
                }`}
              />
              {listo === null ? "Conectando" : listo ? "Asesor activo" : "Sin conexión"}
            </div>

            <Button variant="ghost" size="icon" onClick={nuevaConversacion} title="Nueva conversación">
              <SquarePen className="size-4" />
            </Button>

            <LineamientosPanel />

            <Dialog open={histOpen} onOpenChange={setHistOpen}>
              <DialogTrigger asChild>
                <Button variant="ghost" size="icon" title="Historial de conversaciones">
                  <History className="size-4" />
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-lg">
                <DialogHeader>
                  <DialogTitle>Historial de conversaciones</DialogTitle>
                  <DialogDescription>Se guardan en este navegador.</DialogDescription>
                </DialogHeader>
                <Button
                  variant="outline"
                  className="w-full justify-start gap-2"
                  onClick={() => {
                    nuevaConversacion();
                    setHistOpen(false);
                  }}
                >
                  <SquarePen className="size-4" />
                  Nueva conversación
                </Button>
                <ScrollArea className="scrollbar-thin -mr-2 max-h-[55vh] pr-2">
                  <div className="space-y-1.5">
                    {conversaciones.filter((c) => c.mensajes.length > 0).length === 0 && (
                      <p className="px-1 py-6 text-center text-sm text-muted-foreground">
                        Aún no tienes conversaciones guardadas.
                      </p>
                    )}
                    {conversaciones
                      .filter((c) => c.mensajes.length > 0)
                      .map((c) => (
                        <div
                          key={c.id}
                          className={`group flex items-center gap-2 rounded-md border px-3 py-2 transition-colors ${
                            c.id === activa?.id ? "border-neutral-400 bg-neutral-50" : "border-border hover:bg-neutral-50"
                          }`}
                        >
                          <button
                            className="flex min-w-0 flex-1 items-center gap-2 text-left"
                            onClick={() => {
                              seleccionar(c.id);
                              setHistOpen(false);
                            }}
                          >
                            <MessageSquare className="size-4 shrink-0 text-muted-foreground" />
                            <span className="min-w-0 flex-1">
                              <span className="block truncate text-sm text-foreground">{c.titulo}</span>
                              <span className="block text-[11px] text-muted-foreground">
                                {c.mensajes.filter((m) => m.role === "user").length} mensajes · {fechaRelativa(c.updatedAt)}
                              </span>
                            </span>
                          </button>
                          <button
                            className="shrink-0 text-muted-foreground opacity-0 transition-opacity hover:text-red-600 group-hover:opacity-100"
                            onClick={() => eliminar(c.id)}
                            title="Eliminar conversación"
                          >
                            <Trash2 className="size-4" />
                          </button>
                        </div>
                      ))}
                  </div>
                </ScrollArea>
              </DialogContent>
            </Dialog>

            {catalogo && (
              <Dialog>
                <DialogTrigger asChild>
                  <Button variant="outline" size="sm" className="gap-1.5">
                    <LayoutGrid className="size-4" />
                    <span className="hidden sm:inline">Especialistas y marcos</span>
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-3xl">
                  <DialogHeader>
                    <DialogTitle>Especialistas y marcos de referencia</DialogTitle>
                    <DialogDescription>
                      Marcos CAF, Well-Architected y ciclo de vida de IA que aplica el asesor.
                    </DialogDescription>
                  </DialogHeader>
                  <ScrollArea className="scrollbar-thin -mr-2 max-h-[70vh] pr-2">
                    <div className="space-y-6 pb-1">
                      <EspecialistasGrid especialistas={catalogo.especialistas} />
                      <MarcoExplorer catalogo={catalogo} />
                    </div>
                  </ScrollArea>
                </DialogContent>
              </Dialog>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col px-4 py-4">
        <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-lg border border-border bg-white shadow-sm">
          {activa && (
            <ChatPanel
              key={activa.id}
              mensajes={activa.mensajes}
              onCambio={(m) => actualizarMensajes(activa.id, m)}
              sessionId={activa.id}
            />
          )}
        </div>
        <p className="mt-2 flex flex-wrap items-center justify-center gap-3 text-[11px] text-muted-foreground">
          <span className="inline-flex items-center gap-1">
            <BookOpen className="size-3" /> Microsoft Learn
          </span>
          <span className="inline-flex items-center gap-1">
            <Globe className="size-3" /> Web
          </span>
          <span className="inline-flex items-center gap-1">
            <ShieldCheck className="size-3" /> Lineamientos propios
          </span>
          <span>Microsoft Foundry · Agentes persistentes · Estándares en GA</span>
        </p>
      </main>
    </div>
  );
}



