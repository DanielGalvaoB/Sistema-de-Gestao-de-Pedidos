const brl = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });

export function money(v: string | number | null | undefined): string {
  const n = typeof v === 'number' ? v : Number(v ?? 0);
  return brl.format(Number.isFinite(n) ? n : 0);
}

/** A API devolve datas UTC sem fuso; garante a interpretacao como UTC. */
export function parseUtc(s: string | null | undefined): Date | null {
  if (!s) return null;
  const temFuso = /[zZ]|[+-]\d{2}:?\d{2}$/.test(s);
  return new Date(temFuso ? s : `${s}Z`);
}

export function dataHora(s: string | null | undefined): string {
  const d = parseUtc(s);
  return d ? d.toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' }) : '-';
}

export function hora(s: string | null | undefined): string {
  const d = parseUtc(s);
  return d ? d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }) : '-';
}

export function minutosDesde(s: string | null | undefined, agora = Date.now()): number {
  const d = parseUtc(s);
  return d ? Math.max(0, Math.floor((agora - d.getTime()) / 60000)) : 0;
}

export function duracao(min: number): string {
  if (min < 60) return `${min} min`;
  return `${Math.floor(min / 60)}h${String(min % 60).padStart(2, '0')}`;
}

export function hojeISO(offsetDias = 0): string {
  const d = new Date();
  d.setDate(d.getDate() + offsetDias);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const dia = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${dia}`;
}

export const STATUS_LABEL: Record<string, string> = {
  recebido: 'Recebido',
  em_preparo: 'Em preparo',
  pronto: 'Pronto',
  entregue: 'Entregue',
  cancelado: 'Cancelado',
  aberta: 'Aberta',
  aguardando_pagamento: 'Aguardando pagamento',
  encerrada: 'Encerrada',
  cancelada: 'Cancelada',
  livre: 'Livre',
  ocupada: 'Ocupada',
  confirmado: 'Confirmado',
  estornado: 'Estornado',
  ativa: 'Ativa',
  pendente: 'Pendente',
  paga: 'Paga',
};

export const METODO_LABEL: Record<string, string> = {
  dinheiro: 'Dinheiro',
  cartao_credito: 'Cartão de crédito',
  cartao_debito: 'Cartão de débito',
  pix: 'PIX',
  outro: 'Outro',
};

export const TIPO_LABEL: Record<string, string> = {
  mesa: 'Mesa',
  balcao: 'Balcão',
  retirada: 'Retirada',
};

export const PERFIL_LABEL: Record<string, string> = {
  admin: 'Administrador',
  atendente: 'Atendente',
  cozinha: 'Cozinha',
  financeiro: 'Financeiro',
};

export function atendimento(p: { tipo_atendimento: string; mesa_numero: string | null; cliente_nome?: string | null }) {
  if (p.mesa_numero) return `Mesa ${p.mesa_numero}`;
  const tipo = TIPO_LABEL[p.tipo_atendimento] || p.tipo_atendimento;
  return p.cliente_nome ? `${tipo} · ${p.cliente_nome}` : tipo;
}
