import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { crearLineamiento, eliminarLineamiento, listarLineamientos } from "@/api";
import type { Ambito, Lineamiento } from "@/types";
import {
  ShieldCheck,
  Upload,
  Trash2,
  FileText,
  Loader2,
  Plus,
  RotateCw,
  AlertTriangle,
  Inbox,
} from "lucide-react";

const MAX_BYTES = 2 * 1024 * 1024;
const ACEPTA = ".md,.txt,.json,.yaml,.yml,.csv,.xml,.bicep,.tf,.tfvars,.rego,.drawio";

// Espejo de los ámbitos del backend: mantiene el selector usable aunque la API no responda.
const AMBITOS_BASE: Ambito[] = [
  { id: "global", nombre: "Todos" },
  { id: "estrategia", nombre: "Estrategia" },
  { id: "arquitectura", nombre: "Arquitectura" },
  { id: "implementacion", nombre: "Implementación" },
  { id: "operacion", nombre: "Operación" },
  { id: "concierge", nombre: "Asesor general" },
];

const CATEGORIAS = ["Redes", "Seguridad", "Nomenclatura", "Costos", "Datos", "Cumplimiento"];

function fecha(iso: string): string {
  const d = new Date(iso);
  return isNaN(d.getTime()) ? "" : d.toLocaleDateString("es", { day: "2-digit", month: "short" });
}

function Chip({
  activo,
  onClick,
  title,
  children,
}: {
  activo: boolean;
  onClick: () => void;
  title?: string;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={title}
      className={`rounded-full border px-2.5 py-1 text-xs transition-colors ${
        activo
          ? "border-neutral-800 bg-foreground text-white"
          : "border-border bg-white text-neutral-700 hover:border-neutral-400 hover:bg-neutral-50"
      }`}
    >
      {children}
    </button>
  );
}

export function LineamientosPanel({ onCambio }: { onCambio?: (total: number) => void }) {
  const [ambitos, setAmbitos] = useState<Ambito[]>(AMBITOS_BASE);
  const [items, setItems] = useState<Lineamiento[]>([]);
  const [ambito, setAmbito] = useState("global");
  const [categoria, setCategoria] = useState("");
  const [nombre, setNombre] = useState("");
  const [pegado, setPegado] = useState("");
  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [arrastrando, setArrastrando] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const recargar = useCallback(async () => {
    try {
      const datos = await listarLineamientos();
      if (datos.ambitos?.length) setAmbitos(datos.ambitos);
      setItems(datos.lineamientos);
      setError(null);
      onCambio?.(datos.lineamientos.length);
    } catch {
      setError(
        "No se pudo conectar con el servicio de lineamientos. Reinicia el backend e inténtalo de nuevo."
      );
    }
  }, [onCambio]);

  useEffect(() => {
    recargar();
  }, [recargar]);

  const totalCaracteres = useMemo(
    () => items.reduce((acc, l) => acc + (l.caracteres || 0), 0),
    [items]
  );

  async function subir(files: FileList | File[]) {
    setError(null);
    setOcupado(true);
    try {
      for (const f of Array.from(files)) {
        if (f.size > MAX_BYTES) {
          setError(`"${f.name}" supera los 2 MB.`);
          continue;
        }
        const texto = await f.text();
        if (!texto.trim()) {
          setError(`"${f.name}" está vacío.`);
          continue;
        }
        await crearLineamiento({
          nombre: f.name,
          ambito,
          categoria,
          mime_type: f.type || "text/plain",
          texto,
        });
      }
      await recargar();
    } catch (e: any) {
      setError(e.message ?? "No se pudo subir el documento");
    } finally {
      setOcupado(false);
    }
  }

  async function guardarRegla() {
    if (!pegado.trim()) return;
    setOcupado(true);
    setError(null);
    try {
      await crearLineamiento({
        nombre: nombre.trim() || categoria.trim() || "Regla escrita",
        ambito,
        categoria,
        texto: pegado,
      });
      setPegado("");
      setNombre("");
      await recargar();
    } catch (e: any) {
      setError(e.message ?? "No se pudo guardar el lineamiento");
    } finally {
      setOcupado(false);
    }
  }

  async function borrar(id: string) {
    setError(null);
    try {
      await eliminarLineamiento(id);
      await recargar();
    } catch (e: any) {
      setError(e.message ?? "No se pudo eliminar");
    }
  }

  const nombreAmbito = (id: string) => {
    const a = ambitos.find((x) => x.id === id);
    return a?.corto || a?.nombre || id;
  };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" className="gap-1.5" title="Lineamientos propios del negocio">
          <ShieldCheck className="size-4" />
          <span className="hidden sm:inline">Lineamientos</span>
          {items.length > 0 && (
            <Badge variant="secondary" className="ml-0.5 px-1.5 font-normal">
              {items.length}
            </Badge>
          )}
        </Button>
      </DialogTrigger>

      <DialogContent className="w-[calc(100%-2rem)] max-w-4xl gap-0 overflow-hidden p-0">
        <DialogHeader className="border-b border-border px-6 py-4 pr-12">
          <DialogTitle className="flex items-center gap-2">
            <ShieldCheck className="size-4" />
            Lineamientos propios del negocio
          </DialogTitle>
          <DialogDescription>
            Tus estándares internos se aplican como restricciones de diseño junto a CAF y
            Well-Architected. Si contradicen la guía oficial de Microsoft, el asesor lo advierte.
          </DialogDescription>
        </DialogHeader>

        {error && (
          <div className="flex items-start gap-2 border-b border-amber-200 bg-amber-50 px-6 py-2.5 text-xs text-amber-800">
            <AlertTriangle className="mt-[1px] size-3.5 shrink-0" />
            <span className="flex-1">{error}</span>
            <button
              className="inline-flex shrink-0 items-center gap-1 font-medium underline-offset-2 hover:underline"
              onClick={recargar}
            >
              <RotateCw className="size-3" />
              Reintentar
            </button>
          </div>
        )}

        <div className="grid max-h-[70vh] grid-cols-1 overflow-y-auto sm:grid-cols-2 sm:overflow-hidden">
          <section className="flex flex-col border-border sm:max-h-[70vh] sm:border-r">
            <div className="scrollbar-thin flex-1 space-y-4 overflow-y-auto p-5">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                1 · ¿A quién aplica?
              </p>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {ambitos.map((a) => (
                  <Chip
                    key={a.id}
                    activo={ambito === a.id}
                    title={a.nombre}
                    onClick={() => setAmbito(a.id)}
                  >
                    {a.corto || a.nombre}
                  </Chip>
                ))}
              </div>
            </div>

            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                2 · Categoría <span className="font-normal normal-case">(opcional)</span>
              </p>
              <input
                value={categoria}
                onChange={(e) => setCategoria(e.target.value)}
                placeholder="Ej.: Redes"
                className="mt-2 w-full rounded-md border border-input bg-white px-2.5 py-1.5 text-sm text-foreground outline-none focus:border-neutral-400"
              />
              <div className="mt-1.5 flex flex-wrap gap-1.5">
                {CATEGORIAS.map((c) => (
                  <Chip
                    key={c}
                    activo={categoria === c}
                    onClick={() => setCategoria(categoria === c ? "" : c)}
                  >
                    {c}
                  </Chip>
                ))}
              </div>
            </div>

            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                3 · Contenido
              </p>

              <input
                ref={fileRef}
                type="file"
                multiple
                accept={ACEPTA}
                className="hidden"
                onChange={(e) => {
                  if (e.target.files?.length) subir(e.target.files);
                  e.target.value = "";
                }}
              />
              <div
                onDragOver={(e) => {
                  e.preventDefault();
                  setArrastrando(true);
                }}
                onDragLeave={() => setArrastrando(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setArrastrando(false);
                  if (e.dataTransfer.files?.length) subir(e.dataTransfer.files);
                }}
                onClick={() => fileRef.current?.click()}
                className={`mt-2 cursor-pointer rounded-lg border border-dashed px-4 py-4 text-center transition-colors ${
                  arrastrando
                    ? "border-neutral-600 bg-neutral-100"
                    : "border-border hover:bg-neutral-50"
                }`}
              >
                <Upload className="mx-auto size-5 text-muted-foreground" />
                <p className="mt-1.5 text-sm text-foreground">
                  Arrastra tus documentos o{" "}
                  <span className="underline underline-offset-2">selecciónalos</span>
                </p>
                <p className="mt-0.5 text-[11px] text-muted-foreground">
                  .md .txt .json .yaml .csv .xml .bicep .tf · máx. 2 MB
                </p>
              </div>

              <div className="my-3 flex items-center gap-3">
                <span className="h-px flex-1 bg-border" />
                <span className="text-[11px] uppercase tracking-wide text-muted-foreground">o</span>
                <span className="h-px flex-1 bg-border" />
              </div>

              <input
                value={nombre}
                onChange={(e) => setNombre(e.target.value)}
                placeholder="Nombre de la regla (opcional)"
                className="w-full rounded-md border border-input bg-white px-2.5 py-1.5 text-sm text-foreground outline-none focus:border-neutral-400"
              />
              <textarea
                value={pegado}
                onChange={(e) => setPegado(e.target.value)}
                rows={3}
                placeholder="Escribe o pega una regla. Ej.: «Todo PaaS se expone solo por Private Endpoint; región primaria eastus2»."
                className="mt-2 w-full resize-y rounded-md border border-input bg-white px-2.5 py-2 text-sm text-foreground outline-none placeholder:text-muted-foreground focus:border-neutral-400"
              />
            </div>
            </div>

            <div className="border-t border-border bg-white p-3">
              <Button
                size="sm"
                className="w-full gap-1.5"
                disabled={ocupado || !pegado.trim()}
                onClick={guardarRegla}
              >
                {ocupado ? <Loader2 className="size-4 animate-spin" /> : <Plus className="size-4" />}
                Agregar a «{nombreAmbito(ambito)}»
              </Button>
            </div>
          </section>

          <section className="flex min-h-[15rem] flex-col bg-neutral-50/70 sm:max-h-[70vh]">
            <div className="flex items-center justify-between border-b border-border px-5 py-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Cargados
              </p>
              <span className="text-[11px] text-muted-foreground">
                {items.length} doc. · {totalCaracteres.toLocaleString("es")} caracteres
              </span>
            </div>

            <div className="scrollbar-thin flex-1 space-y-1.5 overflow-y-auto p-3">
              {ocupado && items.length === 0 && (
                <div className="flex items-center justify-center gap-2 py-10 text-sm text-muted-foreground">
                  <Loader2 className="size-4 animate-spin" /> Procesando…
                </div>
              )}
              {!ocupado && items.length === 0 && (
                <div className="flex flex-col items-center justify-center gap-1.5 px-6 py-12 text-center">
                  <Inbox className="size-6 text-neutral-300" />
                  <p className="text-sm text-foreground">Aún no hay lineamientos propios</p>
                  <p className="text-xs text-muted-foreground">
                    El asesor aplicará solo las buenas prácticas de Microsoft.
                  </p>
                </div>
              )}
              {items.map((l) => (
                <div
                  key={l.id}
                  className="group flex items-center gap-2.5 rounded-md border border-border bg-white px-3 py-2 transition-colors hover:border-neutral-300"
                >
                  <FileText className="size-4 shrink-0 text-muted-foreground" />
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm text-foreground">{l.nombre}</div>
                    <div className="mt-0.5 flex flex-wrap items-center gap-1.5 text-[11px] text-muted-foreground">
                      <Badge variant="outline" className="px-1.5 py-0 font-normal">
                        {nombreAmbito(l.ambito)}
                      </Badge>
                      {l.categoria && <span>{l.categoria}</span>}
                      <span>· {l.caracteres.toLocaleString("es")} car.</span>
                      <span>· {fecha(l.creado_en)}</span>
                    </div>
                  </div>
                  <button
                    className="shrink-0 rounded p-1 text-muted-foreground transition-colors hover:bg-red-50 hover:text-red-600 focus:opacity-100 group-hover:opacity-100 sm:opacity-0"
                    onClick={() => borrar(l.id)}
                    title="Eliminar lineamiento"
                    aria-label={`Eliminar ${l.nombre}`}
                  >
                    <Trash2 className="size-4" />
                  </button>
                </div>
              ))}
            </div>
          </section>
        </div>
      </DialogContent>
    </Dialog>
  );
}
