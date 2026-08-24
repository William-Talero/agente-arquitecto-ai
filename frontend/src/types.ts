export type Especialista = {
  id: string;
  nombre: string;
  resumen: string;
  foco: string;
  acento: string;
};

export type FaseCaf = {
  id: string;
  nombre: string;
  objetivo: string;
  actividades: string[];
  entregables: string[];
};

export type PilarWaf = {
  id: string;
  nombre: string;
  pregunta_clave: string;
  consideraciones_ai: string[];
  antipatrones: string[];
};

export type EtapaCiclo = {
  id: string;
  nombre: string;
  descripcion: string;
  practicas: string[];
};

export type Estandar = {
  id: string;
  area: string;
  vigente: string;
  detalle: string;
  evitar: string[];
  url: string;
};

export type Catalogo = {
  especialistas: Especialista[];
  fases_caf: FaseCaf[];
  pilares_waf: PilarWaf[];
  ciclo_vida: EtapaCiclo[];
  estandares: Estandar[];
  estandares_revisado: string;
};

export type Ambito = { id: string; nombre: string; corto?: string };

export type Lineamiento = {
  id: string;
  nombre: string;
  ambito: string;
  categoria: string;
  caracteres: number;
  creado_en: string;
  mime_type: string;
};

export type LineamientosResponse = {
  ambitos: Ambito[];
  lineamientos: Lineamiento[];
};

export type Cita = { titulo: string; url: string; fuente: string };
export type Paso = { titulo: string; detalle: string };

export type Tarjeta = Record<string, any> & { tipo: string };

export type Adjunto = {
  name: string;
  mime_type: string;
  data_base64?: string;
  text?: string;
  previewUrl?: string;
};

export type ChatResponse = {
  especialista: string;
  especialista_titulo: string;
  runtime: string;
  texto: string;
  tarjetas: Tarjeta[];
  citas: Cita[];
  pasos: Paso[];
  duracion_ms: number;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  texto: string;
  adjuntos?: Adjunto[];
  respuesta?: ChatResponse;
};

export type Conversacion = {
  id: string;
  titulo: string;
  createdAt: number;
  updatedAt: number;
  mensajes: ChatMessage[];
};
