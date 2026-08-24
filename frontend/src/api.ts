import type { Adjunto, Catalogo, ChatResponse, Lineamiento, LineamientosResponse } from "./types";

export async function obtenerCatalogo(): Promise<Catalogo> {
  const r = await fetch("/api/catalogo");
  if (!r.ok) throw new Error("No se pudo cargar el catálogo");
  return r.json();
}

export async function obtenerSalud(): Promise<{ status: string; advisor_ready: boolean }> {
  const r = await fetch("/api/health");
  return r.json();
}

export async function enviarConsulta(
  message: string,
  adjuntos: Adjunto[] = [],
  sessionId = "default"
): Promise<ChatResponse> {
  const attachments = adjuntos.map((a) => ({
    name: a.name,
    mime_type: a.mime_type,
    data_base64: a.data_base64,
    text: a.text,
  }));
  const r = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message, attachments }),
  });
  if (!r.ok) {
    const detail = await r.json().catch(() => ({ detail: r.statusText }));
    throw new Error(detail.detail || "Error al consultar al asesor");
  }
  return r.json();
}

export async function listarLineamientos(): Promise<LineamientosResponse> {
  const r = await fetch("/api/lineamientos");
  if (!r.ok) throw new Error("No se pudieron cargar los lineamientos");
  return r.json();
}

export async function crearLineamiento(payload: {
  nombre: string;
  ambito: string;
  categoria?: string;
  mime_type?: string;
  texto: string;
}): Promise<Lineamiento> {
  const r = await fetch("/api/lineamientos", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) {
    const detail = await r.json().catch(() => ({ detail: r.statusText }));
    throw new Error(detail.detail || "No se pudo guardar el lineamiento");
  }
  return r.json();
}

export async function eliminarLineamiento(id: string): Promise<void> {
  const r = await fetch(`/api/lineamientos/${id}`, { method: "DELETE" });
  if (!r.ok && r.status !== 204) throw new Error("No se pudo eliminar el lineamiento");
}
