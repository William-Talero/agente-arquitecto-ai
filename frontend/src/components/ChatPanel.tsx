import { useEffect, useRef, useState } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { MessageBubble } from "./MessageBubble";
import type { Adjunto, ChatMessage } from "@/types";
import { enviarConsulta } from "@/api";
import { SendHorizonal, Loader2, Paperclip, X, FileText, ImageIcon, Boxes } from "lucide-react";

const SUGERENCIAS = [
  "¿Cómo estructuro la adopción de IA con el CAF?",
  "Evalúa una arquitectura RAG con el Well-Architected Framework",
  "Diseña un agente con Microsoft Agent Framework sobre Foundry (solo GA)",
  "¿Qué estoy usando que ya esté obsoleto y cómo migro?",
];

const RASTER = /^image\/(png|jpe?g|gif|webp|bmp)$/i;
const MAX_ADJUNTOS = 5;
const MAX_BYTES = 10 * 1024 * 1024;

async function leerArchivo(file: File): Promise<Adjunto> {
  if (RASTER.test(file.type)) {
    const dataUrl: string = await new Promise((resolve, reject) => {
      const fr = new FileReader();
      fr.onload = () => resolve(fr.result as string);
      fr.onerror = reject;
      fr.readAsDataURL(file);
    });
    return {
      name: file.name,
      mime_type: file.type,
      data_base64: dataUrl.split(",")[1],
      previewUrl: dataUrl,
    };
  }
  const text = await file.text();
  return { name: file.name, mime_type: file.type || "text/plain", text };
}

type Props = {
  mensajes: ChatMessage[];
  onCambio: (mensajes: ChatMessage[]) => void;
  sessionId: string;
};

export function ChatPanel({ mensajes, onCambio, sessionId }: Props) {
  const [texto, setTexto] = useState("");
  const [adjuntos, setAdjuntos] = useState<Adjunto[]>([]);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [arrastrando, setArrastrando] = useState(false);
  const finRef = useRef<HTMLDivElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    finRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [mensajes, cargando]);

  async function agregarArchivos(files: FileList | File[]) {
    setError(null);
    const lista = Array.from(files);
    const nuevos: Adjunto[] = [];
    for (const f of lista) {
      if (f.size > MAX_BYTES) {
        setError(`"${f.name}" supera los 10 MB.`);
        continue;
      }
      try {
        nuevos.push(await leerArchivo(f));
      } catch {
        setError(`No se pudo leer "${f.name}".`);
      }
    }
    setAdjuntos((prev) => [...prev, ...nuevos].slice(0, MAX_ADJUNTOS));
  }

  function quitarAdjunto(i: number) {
    setAdjuntos((prev) => prev.filter((_, idx) => idx !== i));
  }

  async function enviar(pregunta?: string) {
    const contenido = (pregunta ?? texto).trim();
    if ((!contenido && adjuntos.length === 0) || cargando) return;
    setError(null);
    setTexto("");
    const usados = adjuntos;
    setAdjuntos([]);
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      texto: contenido,
      adjuntos: usados,
    };
    const base = [...mensajes, userMsg];
    onCambio(base);
    setCargando(true);
    try {
      const respuesta = await enviarConsulta(contenido, usados, sessionId);
      onCambio([
        ...base,
        { id: crypto.randomUUID(), role: "assistant", texto: respuesta.texto, respuesta },
      ]);
    } catch (e: any) {
      setError(e.message ?? "Ocurrió un error");
    } finally {
      setCargando(false);
    }
  }

  return (
    <div
      className="flex h-full flex-col"
      onDragOver={(e) => {
        e.preventDefault();
        setArrastrando(true);
      }}
      onDragLeave={() => setArrastrando(false)}
      onDrop={(e) => {
        e.preventDefault();
        setArrastrando(false);
        if (e.dataTransfer.files?.length) agregarArchivos(e.dataTransfer.files);
      }}
    >
      <ScrollArea className="scrollbar-thin flex-1 px-4">
        <div className="space-y-6 py-5">
          {mensajes.length === 0 && (
            <div className="rounded-lg border border-border bg-neutral-50 p-6">
              <div className="flex items-center gap-2.5">
                <div className="flex size-8 items-center justify-center rounded-md bg-foreground">
                  <Boxes className="size-4 text-white" />
                </div>
                <p className="text-sm font-medium text-foreground">¿En qué puedo ayudarte hoy?</p>
              </div>
              <p className="mt-2 text-sm text-muted-foreground">
                Consúltame sobre arquitectura, desarrollo, adopción, mejora u operación de
                soluciones de IA. Aplico CAF, Well-Architected y lo último en disponibilidad
                general (GA) de Microsoft, citando Microsoft Learn y la web. Puedes{" "}
                <strong className="font-medium text-foreground">adjuntar un diagrama o archivo de
                arquitectura</strong> para evaluarlo, y cargar tus{" "}
                <strong className="font-medium text-foreground">lineamientos propios</strong> para que
                mis recomendaciones cumplan las reglas de tu negocio.
              </p>
              <div className="mt-4 grid gap-2 sm:grid-cols-2">
                {SUGERENCIAS.map((s) => (
                  <button
                    key={s}
                    onClick={() => enviar(s)}
                    className="rounded-md border border-border bg-white px-3 py-2 text-left text-xs text-foreground transition-colors hover:border-neutral-400 hover:bg-neutral-50"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
          {mensajes.map((m) => (
            <MessageBubble key={m.id} message={m} />
          ))}
          {cargando && (
            <div className="flex items-center gap-2.5 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" />
              Analizando con las herramientas de Foundry…
            </div>
          )}
          {error && (
            <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </div>
          )}
          <div ref={finRef} />
        </div>
      </ScrollArea>

      <div className="border-t border-border bg-white p-3">
        {adjuntos.length > 0 && (
          <div className="mb-2 flex flex-wrap gap-2">
            {adjuntos.map((a, i) => (
              <div key={i} className="group relative flex items-center gap-2 rounded-md border border-border bg-neutral-50 py-1 pl-1 pr-2">
                {a.previewUrl ? (
                  <img src={a.previewUrl} alt={a.name} className="size-8 rounded object-cover" />
                ) : (
                  <div className="flex size-8 items-center justify-center rounded bg-neutral-200">
                    <FileText className="size-4 text-neutral-600" />
                  </div>
                )}
                <span className="max-w-[140px] truncate text-xs text-foreground">{a.name}</span>
                <button
                  onClick={() => quitarAdjunto(i)}
                  className="text-muted-foreground hover:text-foreground"
                  aria-label="Quitar adjunto"
                >
                  <X className="size-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}
        <div
          className={`flex items-end gap-2 rounded-lg border bg-white p-1.5 transition-colors ${
            arrastrando ? "border-neutral-500 bg-neutral-50" : "border-input"
          }`}
        >
          <input
            ref={fileRef}
            type="file"
            multiple
            accept="image/png,image/jpeg,image/gif,image/webp,.drawio,.xml,.svg,.json,.yaml,.yml,.md,.txt,.bicep,.tf"
            className="hidden"
            onChange={(e) => {
              if (e.target.files?.length) agregarArchivos(e.target.files);
              e.target.value = "";
            }}
          />
          <Button
            variant="ghost"
            size="icon"
            className="shrink-0 text-muted-foreground"
            onClick={() => fileRef.current?.click()}
            title="Adjuntar imagen o archivo de arquitectura"
          >
            <Paperclip className="size-4" />
          </Button>
          <Textarea
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                enviar();
              }
            }}
            placeholder={
              arrastrando
                ? "Suelta aquí tus archivos…"
                : "Escribe tu consulta o adjunta un diagrama de arquitectura…"
            }
            rows={1}
            className="border-0 bg-transparent shadow-none focus-visible:ring-0"
          />
          <Button
            size="icon"
            className="shrink-0"
            onClick={() => enviar()}
            disabled={cargando || (!texto.trim() && adjuntos.length === 0)}
          >
            {cargando ? <Loader2 className="animate-spin" /> : <SendHorizonal />}
          </Button>
        </div>
        <p className="mt-1.5 flex items-center gap-1 px-1 text-[11px] text-muted-foreground">
          <ImageIcon className="size-3" />
          Adjunta PNG/JPG o archivos .drawio/.xml/.json para evaluar arquitecturas.
        </p>
      </div>
    </div>
  );
}

