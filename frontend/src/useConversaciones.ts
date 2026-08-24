import { useCallback, useEffect, useState } from "react";
import type { ChatMessage, Conversacion } from "./types";

const KEY = "arqai:conversaciones";

function tituloDe(mensajes: ChatMessage[]): string {
  const primero = mensajes.find((m) => m.role === "user");
  const base = (primero?.texto || "").trim();
  if (base) return base.slice(0, 60);
  if (primero?.adjuntos?.length) return `Arquitectura adjunta (${primero.adjuntos.length})`;
  return "Nueva conversación";
}

function nueva(): Conversacion {
  const ahora = Date.now();
  return { id: crypto.randomUUID(), titulo: "Nueva conversación", createdAt: ahora, updatedAt: ahora, mensajes: [] };
}

// Aligera lo que se persiste: descarta datos binarios pesados de los adjuntos.
function paraGuardar(convs: Conversacion[]): Conversacion[] {
  return convs.map((c) => ({
    ...c,
    mensajes: c.mensajes.map((m) => ({
      ...m,
      adjuntos: m.adjuntos?.map((a) => ({ name: a.name, mime_type: a.mime_type })),
    })),
  }));
}

function cargar(): Conversacion[] {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return [];
    const datos = JSON.parse(raw);
    return Array.isArray(datos) ? datos : [];
  } catch {
    return [];
  }
}

function persistir(convs: Conversacion[]) {
  let lista = paraGuardar(convs).filter((c) => c.mensajes.length > 0);
  for (let intento = 0; intento < 6; intento++) {
    try {
      localStorage.setItem(KEY, JSON.stringify(lista));
      return;
    } catch {
      lista = lista.slice(0, Math.max(1, lista.length - 3)); // descarta las más antiguas
    }
  }
}

export function useConversaciones() {
  const [conversaciones, setConversaciones] = useState<Conversacion[]>(() => {
    const previas = cargar();
    return previas.length ? previas : [nueva()];
  });
  const [activaId, setActivaId] = useState<string>(() => "");

  useEffect(() => {
    if (!activaId && conversaciones.length) setActivaId(conversaciones[0].id);
  }, [activaId, conversaciones]);

  useEffect(() => {
    persistir(conversaciones);
  }, [conversaciones]);

  const activa = conversaciones.find((c) => c.id === activaId) || conversaciones[0];

  const actualizarMensajes = useCallback(
    (id: string, mensajes: ChatMessage[]) => {
      setConversaciones((prev) =>
        prev.map((c) =>
          c.id === id ? { ...c, mensajes, titulo: tituloDe(mensajes), updatedAt: Date.now() } : c
        )
      );
    },
    []
  );

  const nuevaConversacion = useCallback(() => {
    setConversaciones((prev) => {
      const vacia = prev.find((c) => c.mensajes.length === 0);
      if (vacia) {
        setActivaId(vacia.id);
        return prev;
      }
      const c = nueva();
      setActivaId(c.id);
      return [c, ...prev];
    });
  }, []);

  const seleccionar = useCallback((id: string) => setActivaId(id), []);

  const eliminar = useCallback((id: string) => {
    setConversaciones((prev) => {
      const resto = prev.filter((c) => c.id !== id);
      const lista = resto.length ? resto : [nueva()];
      setActivaId((actual) => (actual === id ? lista[0].id : actual));
      return lista;
    });
  }, []);

  const ordenadas = [...conversaciones].sort((a, b) => b.updatedAt - a.updatedAt);

  return { conversaciones: ordenadas, activa, actualizarMensajes, nuevaConversacion, seleccionar, eliminar };
}
