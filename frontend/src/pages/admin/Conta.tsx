import {
  Armchair,
  ArrowLeft,
  BadgePercent,
  Banknote,
  Calculator,
  CircleCheck,
  CircleDollarSign,
  Copy,
  HandPlatter,
  Hourglass,
  Lock,
  Minus,
  Plus,
  QrCode,
  Receipt,
  ReceiptText,
  Search,
  Send,
  ShoppingBag,
  Undo2,
  Wallet,
  XCircle,
} from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';
import { useMemo, useRef, useState, type FormEvent } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api, novaChave } from '../../api/client';
import type { CobrancaPix, Conta as ContaT, Pagamento, Pedido, Produto } from '../../api/types';
import { METODOS, ModalPagamentoPedido } from '../../components/PagamentoPedido';
import { useAuth } from '../../auth/AuthContext';
import { Badge, ConfirmModal, Empty, ErrorBox, Loading, Modal, PageHeader, Stat, useToast } from '../../components/ui';
import { useAsync } from '../../hooks/useAsync';
import { useRealtime } from '../../hooks/useRealtime';
import { dataHora, hora, METODO_LABEL, money, TIPO_LABEL } from '../../utils/format';

export default function Conta() {
  const { id } = useParams();
  const { pode } = useAuth();
  const toast = useToast();
  const { data: conta, erro, carregando, recarregar } = useAsync(() => api<ContaT>(`/contas/${id}`), [id]);
  useRealtime(() => recarregar(true), 15000);
  const [modal, setModal] = useState<null | 'pedido' | 'pagamento' | 'ajuste' | 'pix' | 'encerrar' | 'cancelar'>(null);
  const [estornar, setEstornar] = useState<Pagamento | null>(null);
  const [pagandoPedido, setPagandoPedido] = useState<Pedido | null>(null);

  if (carregando && !conta) return <Loading />;
  if (erro || !conta) return <ErrorBox erro={erro || 'Conta não encontrada'} onRetry={() => recarregar()} />;

  const r = conta.resumo;
  const aberta = conta.status === 'aberta' || conta.status === 'aguardando_pagamento';
  const saldo = Number(r.saldo);
  const titulo = conta.mesa_numero ? `Mesa ${conta.mesa_numero}` : TIPO_LABEL[conta.tipo];

  const fecharESalvar = () => {
    setModal(null);
    recarregar(true);
  };

  const entregar = async (p: Pedido) => {
    try {
      await api(`/pedidos/${p.id}/status`, { method: 'PATCH', body: { status: 'entregue' } });
      recarregar(true);
    } catch (e) {
      toast((e as Error).message, 'erro');
    }
  };

  return (
    <div>
      <Link to={conta.mesa_numero ? '/admin/mesas' : '/admin/caixa'} className="voltar">
        <ArrowLeft size={16} /> Voltar
      </Link>
      <PageHeader
        icone={conta.mesa_numero ? Armchair : ShoppingBag}
        titulo={
          <>
            Conta #{conta.id} · {titulo}
            {conta.cliente_nome && ` · ${conta.cliente_nome}`} <Badge status={conta.status} />
          </>
        }
        subtitulo={`Aberta em ${dataHora(conta.aberta_em)}${conta.encerrada_em ? ` · encerrada em ${dataHora(conta.encerrada_em)}` : ''}`}
      />

      <div className="stats">
        <Stat rotulo="Subtotal" valor={money(r.subtotal)} icone={Receipt} />
        <Stat rotulo="Descontos" valor={`- ${money(r.desconto)}`} icone={BadgePercent} />
        <Stat rotulo="Acréscimos" valor={`+ ${money(r.acrescimo)}`} icone={Plus} />
        <Stat rotulo="Total" valor={money(r.total)} icone={Calculator} destaque="info" />
        <Stat rotulo="Pago" valor={money(r.total_pago)} icone={CircleCheck} destaque="ok" />
        <Stat rotulo="Saldo" valor={money(r.saldo)} icone={CircleDollarSign} destaque={saldo > 0 ? 'erro' : 'ok'} />
      </div>
      {(conta.motivo_desconto || conta.motivo_acrescimo) && (
        <p className="muted small">
          {conta.motivo_desconto && `Desconto: ${conta.motivo_desconto}. `}
          {conta.motivo_acrescimo && `Acréscimo: ${conta.motivo_acrescimo}.`}
        </p>
      )}

      {aberta && (
        <div className="barra-acoes">
          {pode('atendente') && (
            <button className="btn btn-primario" onClick={() => setModal('pedido')}>
              <Plus size={16} /> Adicionar pedido
            </button>
          )}
          <button className="btn btn-ok" disabled={saldo <= 0} onClick={() => setModal('pagamento')}>
            <Banknote size={16} /> Pagamento da conta
          </button>
          <button className="btn" disabled={saldo <= 0} onClick={() => setModal('pix')}>
            <QrCode size={16} /> Cobrança PIX
          </button>
          <button className="btn" onClick={() => setModal('ajuste')}>
            <BadgePercent size={16} /> Desconto / acréscimo
          </button>
          {conta.status === 'aberta' && (
            <button
              className="btn"
              onClick={async () => {
                try {
                  await api(`/contas/${conta.id}/solicitar-fechamento`, { method: 'POST' });
                  recarregar(true);
                } catch (e) {
                  toast((e as Error).message, 'erro');
                }
              }}
            >
              <Hourglass size={16} /> Pedir fechamento
            </button>
          )}
          <button className="btn btn-escuro" onClick={() => setModal('encerrar')}>
            <Lock size={16} /> Encerrar conta
          </button>
          {conta.pedidos?.every((p) => p.status === 'cancelado') && (
            <button className="btn btn-perigo-sutil" onClick={() => setModal('cancelar')}>
              <XCircle size={16} /> Cancelar conta
            </button>
          )}
        </div>
      )}

      <div className="grid-2-col">
        <section className="card">
          <h2 className="card-titulo">
            <ReceiptText size={18} /> Pedidos
          </h2>
          {conta.pedidos?.length === 0 && <Empty>Nenhum pedido nesta conta.</Empty>}
          {conta.pedidos?.map((p) => {
            const aguardando = aberta && ['pronto', 'entregue'].includes(p.status) && !p.pago;
            return (
              <div key={p.id} className={`pedido-bloco ${p.status === 'cancelado' ? 'cancelado' : ''}`}>
                <div className="pedido-bloco-topo">
                  <strong>
                    #{p.id} · {hora(p.created_at)}
                  </strong>
                  <Badge status={p.status} />
                  {p.status !== 'cancelado' && (
                    <Badge status={p.pago ? 'paga' : 'pendente'}>{p.pago ? 'Pago' : 'A pagar'}</Badge>
                  )}
                  <span className="num">{money(p.total)}</span>
                </div>
                <ul className="lista-itens">
                  {p.itens.map((i) => (
                    <li key={i.id} className={i.status === 'cancelado' ? 'riscado' : ''}>
                      <span>
                        {i.quantidade}x {i.nome_produto}
                        {i.observacao && <em className="muted"> ({i.observacao})</em>}
                      </span>
                      <span className="muted small">
                        {money(i.preco_unitario)} · {money(i.subtotal)}
                      </span>
                    </li>
                  ))}
                </ul>
                {p.motivo_cancelamento && <p className="small texto-erro">Cancelado: {p.motivo_cancelamento}</p>}
                {(aguardando || (p.status === 'pronto' && pode('atendente'))) && (
                  <div className="pedido-bloco-acoes">
                    {aguardando && (
                      <button className="btn btn-sm btn-pagar" onClick={() => setPagandoPedido(p)}>
                        <CircleDollarSign size={14} /> Confirmar pagamento
                        {Number(p.total_pago) > 0 && ` (resta ${money(p.saldo)})`}
                      </button>
                    )}
                    {p.status === 'pronto' && pode('atendente') && (
                      <button className="btn btn-sm btn-ok" onClick={() => entregar(p)}>
                        <HandPlatter size={14} /> Marcar entregue
                      </button>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </section>

        <section className="card">
          <h2 className="card-titulo">
            <Wallet size={18} /> Pagamentos
          </h2>
          {conta.pagamentos?.length === 0 && <Empty>Nenhum pagamento registrado.</Empty>}
          <ul className="lista-pagamentos">
            {conta.pagamentos?.map((p) => (
              <li key={p.id} className={p.status === 'estornado' ? 'riscado' : ''}>
                <div>
                  <strong>{money(p.valor)}</strong> · {METODO_LABEL[p.metodo]}
                  {p.id_pedido && <span className="muted"> · pedido #{p.id_pedido}</span>}
                  <div className="muted small">
                    {dataHora(p.data_hora)} · registro {p.origem}
                    {p.observacao && ` · ${p.observacao}`}
                    {p.motivo_estorno && ` · estorno: ${p.motivo_estorno}`}
                  </div>
                </div>
                <div className="acoes-linha">
                  <Badge status={p.status} />
                  {aberta && p.status === 'confirmado' && (
                    <button className="btn btn-sm btn-perigo-sutil" onClick={() => setEstornar(p)}>
                      <Undo2 size={14} /> Estornar
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </section>
      </div>

      {pagandoPedido && (
        <ModalPagamentoPedido pedido={pagandoPedido} onClose={() => setPagandoPedido(null)} onPago={() => recarregar(true)} />
      )}
      {modal === 'pedido' && <ModalPedido contaId={conta.id} onClose={() => setModal(null)} onSalvo={fecharESalvar} />}
      {modal === 'pagamento' && (
        <ModalPagamento contaId={conta.id} saldo={saldo} onClose={() => setModal(null)} onSalvo={fecharESalvar} />
      )}
      {modal === 'ajuste' && (
        <ModalAjuste conta={conta} podeDesconto={pode('financeiro')} onClose={() => setModal(null)} onSalvo={fecharESalvar} />
      )}
      {modal === 'pix' && <ModalPix contaId={conta.id} saldo={saldo} onClose={fecharESalvar} />}
      {modal === 'encerrar' && (
        <ConfirmModal
          titulo="Encerrar conta"
          mensagem={
            saldo > 0
              ? `Ainda há saldo de ${money(saldo)}. A conta só pode ser encerrada depois de quitada.`
              : 'Confirma o encerramento? A mesa ficará livre.'
          }
          onClose={() => setModal(null)}
          onConfirm={async () => {
            await api(`/contas/${conta.id}/encerrar`, { method: 'POST' });
            toast('Conta encerrada');
            recarregar(true);
          }}
        />
      )}
      {modal === 'cancelar' && (
        <ConfirmModal
          titulo="Cancelar conta"
          mensagem="A conta não possui pedidos ativos e será cancelada."
          perigo
          onClose={() => setModal(null)}
          onConfirm={async () => {
            await api(`/contas/${conta.id}/cancelar`, { method: 'POST' });
            recarregar(true);
          }}
        />
      )}
      {estornar && (
        <ConfirmModal
          titulo={`Estornar pagamento de ${money(estornar.valor)}`}
          mensagem="O pagamento ficará registrado como estornado e a receita correspondente será cancelada."
          pedirMotivo
          perigo
          textoConfirmar="Estornar"
          onClose={() => setEstornar(null)}
          onConfirm={async (motivo) => {
            await api(`/contas/pagamentos/${estornar.id}/estornar`, { body: { motivo } });
            recarregar(true);
          }}
        />
      )}
    </div>
  );
}

function ModalPedido({ contaId, onClose, onSalvo }: { contaId: number; onClose: () => void; onSalvo: () => void }) {
  const toast = useToast();
  const { data: produtos, carregando } = useAsync(() => api<Produto[]>('/menu/', { query: { disponivel: true } }), []);
  const [busca, setBusca] = useState('');
  const [itens, setItens] = useState<Record<number, { qtd: number; obs: string }>>({});
  const [observacao, setObservacao] = useState('');
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  const filtrados = useMemo(
    () => (produtos || []).filter((p) => p.nome.toLowerCase().includes(busca.toLowerCase())),
    [produtos, busca],
  );
  const selecionados = Object.entries(itens).filter(([, v]) => v.qtd > 0);
  const total = selecionados.reduce((s, [id, v]) => s + Number(produtos?.find((p) => p.id === +id)?.preco || 0) * v.qtd, 0);

  const mudar = (id: number, delta: number) =>
    setItens((it) => ({ ...it, [id]: { qtd: Math.max(0, (it[id]?.qtd || 0) + delta), obs: it[id]?.obs || '' } }));

  const enviar = async () => {
    setEnviando(true);
    setErro(null);
    try {
      await api('/pedidos/', {
        body: {
          id_sessao: contaId,
          observacao: observacao || undefined,
          itens: selecionados.map(([id, v]) => ({ id_menu: +id, quantidade: v.qtd, observacao: v.obs || undefined })),
        },
      });
      toast('Pedido enviado para a cozinha');
      onSalvo();
    } catch (e) {
      setErro((e as Error).message);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <Modal titulo="Adicionar pedido" onClose={onClose} largo>
      <div className="input-icone">
        <Search size={16} />
        <input placeholder="Buscar produto..." value={busca} onChange={(e) => setBusca(e.target.value)} autoFocus />
      </div>
      {carregando ? (
        <Loading />
      ) : (
        <ul className="seletor-produtos">
          {filtrados.map((p) => (
            <li key={p.id}>
              <div>
                <strong>{p.nome}</strong> <span className="muted">{money(p.preco)}</span>
                {(itens[p.id]?.qtd || 0) > 0 && (
                  <input
                    className="input-sm"
                    placeholder="Observação"
                    value={itens[p.id]?.obs || ''}
                    onChange={(e) => setItens((it) => ({ ...it, [p.id]: { ...it[p.id], obs: e.target.value } }))}
                  />
                )}
              </div>
              <div className="qtd">
                <button onClick={() => mudar(p.id, -1)} aria-label="Diminuir">
                  <Minus size={16} />
                </button>
                <span>{itens[p.id]?.qtd || 0}</span>
                <button onClick={() => mudar(p.id, 1)} aria-label="Aumentar">
                  <Plus size={16} />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
      <label>
        Observação do pedido
        <input value={observacao} onChange={(e) => setObservacao(e.target.value)} maxLength={500} />
      </label>
      {erro && <ErrorBox erro={erro} />}
      <div className="form-actions">
        <span className="muted">Total estimado: {money(total)}</span>
        <button className="btn btn-primario" disabled={!selecionados.length || enviando} onClick={enviar}>
          <Send size={16} /> {enviando ? 'Enviando...' : 'Enviar para a cozinha'}
        </button>
      </div>
    </Modal>
  );
}

function ModalPagamento({
  contaId,
  saldo,
  onClose,
  onSalvo,
}: {
  contaId: number;
  saldo: number;
  onClose: () => void;
  onSalvo: () => void;
}) {
  const toast = useToast();
  const [valor, setValor] = useState(saldo.toFixed(2));
  const [recebido, setRecebido] = useState('');
  const [metodo, setMetodo] = useState('dinheiro');
  const [obs, setObs] = useState('');
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  // Uma chave por tentativa: cliques repetidos nao duplicam o pagamento
  const chave = useRef(novaChave());
  const troco = metodo === 'dinheiro' && recebido ? Number(recebido.replace(',', '.')) - Number(valor) : 0;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setEnviando(true);
    setErro(null);
    try {
      await api(`/contas/${contaId}/pagamentos`, {
        body: {
          valor: Number(valor.replace(',', '.')).toFixed(2),
          metodo,
          chave_idempotencia: chave.current,
          observacao: obs || undefined,
        },
      });
      toast('Pagamento registrado');
      onSalvo();
    } catch (err) {
      setErro((err as Error).message);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <Modal titulo="Pagamento da conta" onClose={onClose}>
      <form className="form" onSubmit={submit}>
        <p className="muted small">
          Registre somente valores efetivamente recebidos. Saldo: <strong>{money(saldo)}</strong>
        </p>
        <div className="metodos-grid">
          {METODOS.map(({ valor: k, label, icone: Icone }) => (
            <button type="button" key={k} className={`metodo ${metodo === k ? 'ativo' : ''}`} onClick={() => setMetodo(k)}>
              <Icone size={22} strokeWidth={1.75} />
              <span>{label}</span>
            </button>
          ))}
        </div>
        <label>
          Valor a abater (R$)
          <input inputMode="decimal" value={valor} onChange={(e) => setValor(e.target.value)} required />
        </label>
        {metodo === 'dinheiro' && (
          <label>
            Valor entregue pelo cliente (para calcular troco)
            <input inputMode="decimal" value={recebido} onChange={(e) => setRecebido(e.target.value)} />
            {troco > 0 && (
              <span className="troco">
                Troco <strong>{money(troco)}</strong>
              </span>
            )}
          </label>
        )}
        {metodo === 'pix' && (
          <p className="alert alert-aviso small">
            Confirme o recebimento no extrato/app do banco antes de registrar. Não há confirmação automática.
          </p>
        )}
        <label>
          Observação
          <input value={obs} onChange={(e) => setObs(e.target.value)} maxLength={300} />
        </label>
        {erro && <ErrorBox erro={erro} />}
        <div className="form-actions">
          <button className="btn btn-ok btn-grande" disabled={enviando}>
            {enviando ? 'Registrando...' : 'Registrar pagamento'}
          </button>
        </div>
      </form>
    </Modal>
  );
}

function ModalAjuste({
  conta,
  podeDesconto,
  onClose,
  onSalvo,
}: {
  conta: ContaT;
  podeDesconto: boolean;
  onClose: () => void;
  onSalvo: () => void;
}) {
  const [desconto, setDesconto] = useState(conta.resumo.desconto);
  const [motivoDesc, setMotivoDesc] = useState(conta.motivo_desconto || '');
  const [acrescimo, setAcrescimo] = useState(conta.resumo.acrescimo);
  const [motivoAcr, setMotivoAcr] = useState(conta.motivo_acrescimo || '');
  const [erro, setErro] = useState<string | null>(null);

  const salvar = async (body: object) => {
    setErro(null);
    try {
      await api(`/contas/${conta.id}/ajustes`, { method: 'PATCH', body });
      onSalvo();
    } catch (e) {
      setErro((e as Error).message);
    }
  };

  return (
    <Modal titulo="Descontos e acréscimos" onClose={onClose}>
      <form
        className="form"
        onSubmit={(e) => {
          e.preventDefault();
          salvar({
            ...(podeDesconto ? { desconto: Number(desconto).toFixed(2), motivo_desconto: motivoDesc || null } : {}),
            acrescimo: Number(acrescimo).toFixed(2),
            motivo_acrescimo: motivoAcr || null,
          });
        }}
      >
        <button type="button" className="btn" onClick={() => salvar({ aplicar_taxa_servico: true })}>
          Aplicar taxa de serviço configurada
        </button>
        <div className="grid-2">
          <label>
            Acréscimo (R$)
            <input inputMode="decimal" value={acrescimo} onChange={(e) => setAcrescimo(e.target.value)} />
          </label>
          <label>
            Motivo do acréscimo
            <input value={motivoAcr} onChange={(e) => setMotivoAcr(e.target.value)} />
          </label>
        </div>
        {podeDesconto ? (
          <div className="grid-2">
            <label>
              Desconto (R$)
              <input inputMode="decimal" value={desconto} onChange={(e) => setDesconto(e.target.value)} />
            </label>
            <label>
              Motivo do desconto
              <input value={motivoDesc} onChange={(e) => setMotivoDesc(e.target.value)} />
            </label>
          </div>
        ) : (
          <p className="muted small">Descontos precisam ser autorizados por um administrador ou pelo financeiro.</p>
        )}
        {erro && <ErrorBox erro={erro} />}
        <div className="form-actions">
          <button className="btn btn-primario">Salvar</button>
        </div>
      </form>
    </Modal>
  );
}

function ModalPix({ contaId, saldo, onClose }: { contaId: number; saldo: number; onClose: () => void }) {
  const [valor, setValor] = useState(saldo.toFixed(2));
  const [cobranca, setCobranca] = useState<CobrancaPix | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const toast = useToast();

  const gerar = async () => {
    setErro(null);
    try {
      setCobranca(
        await api<CobrancaPix>(`/contas/${contaId}/pix`, { body: { valor: Number(valor.replace(',', '.')).toFixed(2) } }),
      );
    } catch (e) {
      setErro((e as Error).message);
    }
  };

  return (
    <Modal titulo="Cobrança PIX" onClose={onClose}>
      {!cobranca ? (
        <div className="form">
          <label>
            Valor (R$)
            <input inputMode="decimal" value={valor} onChange={(e) => setValor(e.target.value)} />
          </label>
          {erro && <ErrorBox erro={erro} />}
          <button className="btn btn-primario" onClick={gerar}>
            <QrCode size={16} /> Gerar QR Code PIX
          </button>
        </div>
      ) : (
        <div className="qr-box">
          <QRCodeSVG value={cobranca.copia_e_cola} size={240} includeMargin />
          <strong>{money(cobranca.valor)}</strong>
          <span className="small">Identificação: {cobranca.txid}</span>
          <textarea readOnly value={cobranca.copia_e_cola} rows={3} className="small" />
          <button
            className="btn"
            onClick={() => {
              navigator.clipboard?.writeText(cobranca.copia_e_cola);
              toast('Código copiado');
            }}
          >
            <Copy size={16} /> Copiar código copia e cola
          </button>
          <p className="alert alert-aviso small">{cobranca.aviso}</p>
        </div>
      )}
    </Modal>
  );
}
