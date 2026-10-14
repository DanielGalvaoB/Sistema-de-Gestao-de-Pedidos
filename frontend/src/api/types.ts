export type Perfil = 'admin' | 'atendente' | 'cozinha' | 'financeiro';
export type StatusPedido = 'recebido' | 'em_preparo' | 'pronto' | 'entregue' | 'cancelado';

export interface Me {
  id: number;
  nome: string;
  email: string;
  perfil: Perfil;
  ativo: boolean;
  id_estabelecimento: number;
  nome_loja: string;
  slug: string;
}

export interface Usuario {
  id: number;
  nome: string;
  email: string;
  perfil: Perfil;
  ativo: boolean;
}

export interface Estabelecimento {
  id: number;
  nome_loja: string;
  slug: string;
  email: string;
  nome_titular: string;
  chave_pix: string;
  cidade: string;
  tempo_preparo_padrao_min: number;
  alerta_atraso_percentual: number;
  taxa_servico_percentual: string;
}

export interface Categoria {
  id: number;
  nome: string;
  ordem: number;
  ativo: boolean;
}

export interface Produto {
  id: number;
  nome: string;
  preco: string;
  descricao: string | null;
  url_imagem: string | null;
  is_disponivel: boolean;
  ativo: boolean;
  tempo_preparo_min: number | null;
  id_categoria: number;
}

export interface Mesa {
  id: number;
  numero: string;
  capacidade: number | null;
  ativo: boolean;
  token: string;
  situacao: 'livre' | 'ocupada' | 'aguardando_pagamento';
  id_sessao: number | null;
  aberta_em: string | null;
  total_consumido: string;
}

export interface ItemPedido {
  id: number;
  id_menu: number;
  nome_produto: string;
  preco_unitario: string;
  quantidade: number;
  subtotal: string;
  observacao: string | null;
  status: StatusPedido;
  iniciado_em: string | null;
  pronto_em: string | null;
  previsao_pronto: string | null;
  atrasado: boolean;
}

export interface Pedido {
  id: number;
  id_sessao: number;
  status: StatusPedido;
  observacao: string | null;
  origem: string;
  codigo_acompanhamento: string;
  created_at: string;
  iniciado_em: string | null;
  pronto_em: string | null;
  entregue_em: string | null;
  cancelado_em: string | null;
  previsao_pronto: string | null;
  motivo_atraso: string | null;
  motivo_cancelamento: string | null;
  total: string;
  tipo_atendimento: string;
  mesa_numero: string | null;
  cliente_nome: string | null;
  atrasado: boolean;
  minutos_atraso: number;
  alerta_prazo: boolean;
  itens: ItemPedido[];
  historico?: {
    id_item: number | null;
    status_anterior: string | null;
    status_novo: string;
    motivo: string | null;
    criado_em: string;
  }[];
}

export interface ResumoConta {
  subtotal: string;
  desconto: string;
  acrescimo: string;
  total: string;
  total_pago: string;
  saldo: string;
}

export interface Pagamento {
  id: number;
  valor: string;
  metodo: string;
  status: string;
  origem: string;
  observacao: string | null;
  data_hora: string;
  estornado_em: string | null;
  motivo_estorno: string | null;
}

export interface Conta {
  id: number;
  tipo: string;
  status: 'aberta' | 'aguardando_pagamento' | 'encerrada' | 'cancelada';
  id_mesa: number | null;
  mesa_numero: string | null;
  cliente_nome: string | null;
  aberta_em: string;
  encerrada_em: string | null;
  motivo_desconto: string | null;
  motivo_acrescimo: string | null;
  resumo: ResumoConta;
  pedidos?: Pedido[];
  pagamentos?: Pagamento[];
}

export interface CobrancaPix {
  id: number;
  txid: string;
  valor: string;
  copia_e_cola: string;
  provedor: string;
  status: string;
  criada_em: string;
  confirmacao_automatica: boolean;
  aviso: string;
}

export interface CategoriaFinanceira {
  id: number;
  nome: string;
  tipo: 'entrada' | 'saida';
  ativo: boolean;
  sistema: boolean;
}

export interface Movimentacao {
  id: number;
  tipo: 'entrada' | 'saida';
  descricao: string;
  id_categoria: number;
  categoria_nome: string;
  valor: string;
  data_hora: string;
  metodo_pagamento: string | null;
  observacao: string | null;
  id_pagamento: number | null;
  status: 'ativa' | 'cancelada';
  cancelado_em: string | null;
  motivo_cancelamento: string | null;
  automatica: boolean;
}

export interface ValorRotulo {
  rotulo: string;
  valor: string;
  quantidade: number;
}

export interface Relatorio {
  inicio: string;
  fim: string;
  criterios: Record<string, string>;
  total_vendas: string;
  total_recebido: string;
  total_entradas: string;
  total_despesas: string;
  saldo: string;
  pendente_recebimento: string;
  quantidade_pedidos: number;
  ticket_medio: string;
  produtos_mais_vendidos: ValorRotulo[];
  vendas_por_dia: { dia: string; vendas: string; recebido: string; despesas: string }[];
  recebido_por_metodo: ValorRotulo[];
  despesas_por_categoria: ValorRotulo[];
}

export interface CardapioPublico {
  estabelecimento: { nome_loja: string; slug: string };
  mesa_numero: string | null;
  categorias: (Categoria & { produtos: Produto[] })[];
}

export interface PedidoAcompanhamento {
  numero: number;
  nome_loja: string;
  status: StatusPedido;
  tipo_atendimento: string;
  mesa_numero: string | null;
  created_at: string;
  iniciado_em: string | null;
  pronto_em: string | null;
  entregue_em: string | null;
  previsao_pronto: string | null;
  atrasado: boolean;
  motivo_atraso: string | null;
  total: string;
  itens: { nome_produto: string; quantidade: number; status: StatusPedido }[];
}
