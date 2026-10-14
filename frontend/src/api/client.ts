export const API_URL: string = (import.meta.env.VITE_API_URL as string) || '/api';

const TOKEN_KEY = 'pdv_token';

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string | null) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* armazenamento indisponivel */
  }
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function mensagemDeErro(status: number, body: unknown): string {
  const detail = (body as { detail?: unknown })?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail.length) {
    // Erros de validacao do FastAPI
    return detail
      .map((d: { loc?: unknown[]; msg?: string }) => {
        const campo = d.loc?.filter((x) => x !== 'body').join('.');
        return campo ? `${campo}: ${d.msg}` : d.msg;
      })
      .join('; ');
  }
  if (status === 0) return 'Sem conexao com o servidor';
  return `Erro ${status}`;
}

type Opts = {
  method?: string;
  body?: unknown;
  query?: Record<string, string | number | boolean | undefined | null | string[]>;
  auth?: boolean;
  raw?: boolean;
};

export function buildUrl(path: string, query?: Opts['query']): string {
  const params = new URLSearchParams();
  Object.entries(query || {}).forEach(([k, v]) => {
    if (v === undefined || v === null || v === '') return;
    if (Array.isArray(v)) v.forEach((x) => params.append(k, x));
    else params.append(k, String(v));
  });
  const qs = params.toString();
  return `${API_URL}${path}${qs ? `?${qs}` : ''}`;
}

let onUnauthorized: (() => void) | null = null;
export function setUnauthorizedHandler(fn: () => void) {
  onUnauthorized = fn;
}

export async function api<T = unknown>(path: string, opts: Opts = {}): Promise<T> {
  const headers: Record<string, string> = {};
  if (opts.body !== undefined) headers['Content-Type'] = 'application/json';
  const token = getToken();
  if (opts.auth !== false && token) headers.Authorization = `Bearer ${token}`;

  let res: Response;
  try {
    res = await fetch(buildUrl(path, opts.query), {
      method: opts.method || (opts.body !== undefined ? 'POST' : 'GET'),
      headers,
      body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
    });
  } catch {
    throw new ApiError(0, 'Sem conexao com o servidor');
  }

  if (res.status === 401 && opts.auth !== false && token) {
    onUnauthorized?.();
  }
  if (!res.ok) {
    let body: unknown = null;
    try {
      body = await res.json();
    } catch {
      /* corpo vazio */
    }
    throw new ApiError(res.status, mensagemDeErro(res.status, body));
  }
  if (opts.raw) return res as unknown as T;
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

/** Baixa um arquivo autenticado (CSV/PDF). */
export async function baixarArquivo(path: string, query: Opts['query'], nome: string) {
  const res = await api<Response>(path, { query, raw: true });
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = nome;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function wsUrl(path: string): string {
  const base = API_URL.startsWith('http')
    ? API_URL.replace(/^http/, 'ws')
    : `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}${API_URL}`;
  return `${base}${path}`;
}

export function novaChave(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID();
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}
