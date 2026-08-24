import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import mermaid from "mermaid";
import type { ChatMessage } from "@/types";
import { Badge } from "@/components/ui/badge";
import { MessageCards, Citas } from "./MessageCards";
import { Boxes, FileText } from "lucide-react";

mermaid.initialize({
  startOnLoad: false,
  theme: "neutral",
  securityLevel: "strict",
  suppressErrorRendering: true,
  fontFamily: '"Segoe UI", system-ui, sans-serif',
});

/** Repara errores frecuentes de Mermaid generados por el modelo. */
function repararMermaid(code: string): string {
  let c = code.replace(/<br\s*>/gi, "<br/>").replace(/[""]/g, '"').replace(/['']/g, "'");
  // Comilla etiquetas de nodo con caracteres problemáticos: A[Azure OpenAI (GPT-4o)] -> A["..."]
  const quote = (m: string, open: string, inner: string, close: string) => {
    const t = inner.trim();
    if (t.startsWith('"') || t.startsWith("'")) return m;
    if (!/[()/:,&%<>{}|]/.test(t)) return m;
    return `${open}"${inner.replace(/"/g, "'")}"${close}`;
  };
  c = c.replace(/(\[)([^\]\n"']+)(\])/g, quote);
  c = c.replace(/(\{)([^}\n"']+)(\})/g, quote);
  // Etiquetas de arista con paréntesis: -->|texto (x)| -> -->|"texto (x)"|
  c = c.replace(/\|([^|\n"']*[()/][^|\n"']*)\|/g, (_m, inner) => `|"${inner.replace(/"/g, "'")}"|`);
  return c;
}

async function esValido(code: string): Promise<boolean> {
  try {
    return (await mermaid.parse(code, { suppressErrors: true })) !== false;
  } catch {
    return false;
  }
}

function Mermaid({ chart }: { chart: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    let cancelado = false;
    (async () => {
      let usable: string | null = null;
      if (await esValido(chart)) usable = chart;
      else {
        const rep = repararMermaid(chart);
        if (await esValido(rep)) usable = rep;
      }
      if (cancelado) return;
      if (!usable) {
        setError(true);
        return;
      }
      try {
        const id = "mmd-" + Math.random().toString(36).slice(2);
        const { svg } = await mermaid.render(id, usable);
        if (!cancelado && ref.current) ref.current.innerHTML = svg;
      } catch {
        if (!cancelado) setError(true);
      }
    })();
    return () => {
      cancelado = true;
    };
  }, [chart]);
  if (error) {
    return (
      <details className="my-2 rounded-lg border border-border bg-neutral-50 p-2 text-xs text-neutral-500">
        <summary className="cursor-pointer select-none">Diagrama (ver código)</summary>
        <pre className="mt-2 overflow-x-auto whitespace-pre-wrap">{chart}</pre>
      </details>
    );
  }
  return (
    <div className="mermaid-figure my-3 overflow-x-auto rounded-lg border border-border bg-white p-3">
      <div ref={ref} className="flex justify-center" />
    </div>
  );
}

function Adjuntos({ message }: { message: ChatMessage }) {
  if (!message.adjuntos?.length) return null;
  return (
    <div className="mb-2 flex flex-wrap justify-end gap-2">
      {message.adjuntos.map((a, i) =>
        a.previewUrl ? (
          <img
            key={i}
            src={a.previewUrl}
            alt={a.name}
            className="max-h-40 rounded-md border border-border object-cover"
          />
        ) : (
          <div
            key={i}
            className="flex items-center gap-2 rounded-md border border-border bg-white px-2.5 py-1.5"
          >
            <FileText className="size-4 text-neutral-500" />
            <span className="max-w-[160px] truncate text-xs text-foreground">{a.name}</span>
          </div>
        )
      )}
    </div>
  );
}

export function MessageBubble({ message }: { message: ChatMessage }) {
  const esUsuario = message.role === "user";
  if (esUsuario) {
    return (
      <div className="flex flex-col items-end">
        <Adjuntos message={message} />
        {message.texto && (
          <div className="max-w-[80%] rounded-lg rounded-tr-sm bg-foreground px-4 py-2.5 text-sm text-white">
            {message.texto}
          </div>
        )}
      </div>
    );
  }

  const r = message.respuesta;
  return (
    <div className="flex gap-3">
      <div className="flex size-8 shrink-0 items-center justify-center rounded-md bg-foreground">
        <Boxes className="size-4 text-white" />
      </div>
      <div className="min-w-0 flex-1">
        {r && (
          <div className="mb-1.5 flex flex-wrap items-center gap-1.5">
            <span className="text-sm font-semibold text-foreground">{r.especialista_titulo}</span>
            <Badge variant="outline" className="font-normal text-muted-foreground">
              {r.runtime}
            </Badge>
            {r.pasos?.slice(1).map((p, i) => (
              <Badge key={i} variant="secondary" className="font-normal">
                {p.titulo}
              </Badge>
            ))}
          </div>
        )}
        <div className="markdown rounded-lg rounded-tl-sm border border-border bg-white px-4 py-3 text-sm leading-relaxed text-foreground">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              code({ className, children, ...props }) {
                const texto = String(children ?? "");
                if (className?.includes("language-mermaid")) {
                  return <Mermaid chart={texto.replace(/\n$/, "")} />;
                }
                return (
                  <code className={className} {...props}>
                    {children}
                  </code>
                );
              },
              table({ children, ...props }) {
                return (
                  <div className="table-scroll overflow-x-auto">
                    <table {...props}>{children}</table>
                  </div>
                );
              },
            }}
          >
            {message.texto}
          </ReactMarkdown>
        </div>
        {r && <MessageCards tarjetas={r.tarjetas} />}
        {r && <Citas citas={r.citas} />}
        {r && (
          <div className="mt-1.5 text-[11px] text-muted-foreground">
            {(r.duracion_ms / 1000).toFixed(1)} s
          </div>
        )}
      </div>
    </div>
  );
}
