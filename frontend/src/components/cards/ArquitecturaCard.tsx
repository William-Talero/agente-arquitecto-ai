import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Download, Network, Layers, ZoomIn, ZoomOut, Maximize2 } from "lucide-react";

let viewerPromise: Promise<any> | null = null;

function cargarVisor(): Promise<any> {
  const g = (window as any).GraphViewer;
  if (g) return Promise.resolve(g);
  if (viewerPromise) return viewerPromise;
  viewerPromise = new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = "https://viewer.diagrams.net/js/viewer-static.min.js";
    s.async = true;
    s.onload = () => resolve((window as any).GraphViewer);
    s.onerror = reject;
    document.body.appendChild(s);
  });
  return viewerPromise;
}

function slug(t: string) {
  return (t || "arquitectura")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 60) || "arquitectura";
}

type Props = {
  titulo: string;
  drawio: string;
  zonas?: string[];
  n_servicios?: number;
  n_conexiones?: number;
};

export function ArquitecturaCard({ titulo, drawio, zonas = [], n_servicios, n_conexiones }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const [error, setError] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [natural, setNatural] = useState<{ w: number; h: number } | null>(null);
  const fitRef = useRef(1);

  const anchoDisponible = () => {
    const main = document.querySelector("main");
    return Math.max(240, (main?.clientWidth ?? window.innerWidth) - 112);
  };

  useEffect(() => {
    let cancelado = false;

    const medir = () => {
      const holder = ref.current?.querySelector<HTMLElement>(".mxgraph");
      if (!holder) return;
      holder.style.transform = "none";
      const w = holder.offsetWidth;
      const h = holder.offsetHeight;
      if (!w || !h || cancelado) return;
      const fit = Math.min(1, anchoDisponible() / w);
      fitRef.current = fit;
      setNatural({ w, h });
      setZoom(fit);
    };

    cargarVisor()
      .then((GV) => {
        if (cancelado || !ref.current || !GV) return;
        ref.current.innerHTML = "";
        const holder = document.createElement("div");
        holder.className = "mxgraph";
        holder.setAttribute(
          "data-mxgraph",
          JSON.stringify({ highlight: "#0067b8", nav: false, resize: false, toolbar: null, xml: drawio })
        );
        ref.current.appendChild(holder);
        try {
          GV.createViewerForElement(holder);
          requestAnimationFrame(() => requestAnimationFrame(medir));
          [300, 700, 1300].forEach((t) => setTimeout(medir, t));
        } catch {
          setError(true);
        }
      })
      .catch(() => setError(true));
    return () => {
      cancelado = true;
    };
  }, [drawio]);

  // Aplica el zoom al diagrama y ajusta el tamaño del lienzo para permitir paneo.
  useEffect(() => {
    const holder = ref.current?.querySelector<HTMLElement>(".mxgraph");
    if (!holder || !natural) return;
    holder.style.transformOrigin = "top left";
    holder.style.transform = `scale(${zoom})`;
    ref.current!.style.width = `${Math.round(natural.w * zoom)}px`;
    ref.current!.style.height = `${Math.round(natural.h * zoom)}px`;
  }, [zoom, natural]);

  function descargar() {
    const blob = new Blob([drawio], { type: "application/xml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${slug(titulo)}.drawio`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="max-w-full overflow-hidden rounded-lg border border-border bg-white p-4">
      <div className="mb-2 flex items-start gap-2">
        <Network className="mt-0.5 size-4 shrink-0 text-neutral-700" />
        <div className="min-w-0 flex-1">
          <div className="text-sm font-semibold text-foreground">{titulo}</div>
          <div className="mt-0.5 text-[11px] text-muted-foreground">
            Diagrama draw.io · iconos de Azure · alineado a CAF, Well-Architected y AI Landing Zone
          </div>
        </div>
        <Button size="sm" onClick={descargar} className="shrink-0 gap-1.5">
          <Download className="size-4" />
          .drawio
        </Button>
      </div>

      <div className="mb-3 flex flex-wrap items-center gap-1.5">
        {typeof n_servicios === "number" && (
          <Badge variant="secondary" className="gap-1 font-normal">
            <Layers className="size-3" />
            {n_servicios} servicios
          </Badge>
        )}
        {typeof n_conexiones === "number" && n_conexiones > 0 && (
          <Badge variant="secondary" className="gap-1 font-normal">
            <Network className="size-3" />
            {n_conexiones} flujos
          </Badge>
        )}
        {zonas.map((z) => (
          <Badge key={z} variant="outline" className="font-normal text-muted-foreground">
            {z}
          </Badge>
        ))}
      </div>

      {error ? (
        <div className="rounded-md border border-dashed border-border bg-neutral-50 p-4 text-center text-xs text-muted-foreground">
          Vista previa no disponible sin conexión. Descarga el archivo <strong>.drawio</strong> y ábrelo en
          draw.io o diagrams.net.
        </div>
      ) : (
        <>
          <div className="mb-2 flex items-center gap-2">
            <Button
              variant="outline"
              size="icon"
              className="size-7"
              onClick={() => setZoom((z) => Math.max(0.2, +(z - 0.15).toFixed(2)))}
              aria-label="Alejar"
            >
              <ZoomOut className="size-3.5" />
            </Button>
            <input
              type="range"
              min={0.2}
              max={2}
              step={0.05}
              value={zoom}
              onChange={(e) => setZoom(Number(e.target.value))}
              className="h-1 flex-1 cursor-pointer accent-[#0067b8]"
              aria-label="Zoom del diagrama"
            />
            <Button
              variant="outline"
              size="icon"
              className="size-7"
              onClick={() => setZoom((z) => Math.min(2, +(z + 0.15).toFixed(2)))}
              aria-label="Acercar"
            >
              <ZoomIn className="size-3.5" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              className="size-7"
              onClick={() => setZoom(fitRef.current)}
              aria-label="Ajustar al ancho"
            >
              <Maximize2 className="size-3.5" />
            </Button>
            <span className="w-10 text-right text-[11px] tabular-nums text-muted-foreground">
              {Math.round(zoom * 100)}%
            </span>
          </div>
          <div className="scrollbar-thin w-full max-h-[70vh] max-w-full overflow-auto rounded-md border border-border bg-white p-2">
            <div ref={ref} />
          </div>
          <p className="mt-1.5 text-[11px] text-muted-foreground">
            Usa el control de zoom y arrastra la barra de desplazamiento para explorar el diagrama.
          </p>
        </>
      )}
    </div>
  );
}
