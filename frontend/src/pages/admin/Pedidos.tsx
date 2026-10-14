import { CircleDollarSign, ExternalLink, MessageSquareText, ReceiptText } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../api/client';
import type { Pedido } from '../../api/types';
import { useAuth } from '../../auth/AuthContext';
import { ModalPagamentoPedido } from '../../components/PagamentoPedido';
import { Badge, Empty, ErrorBox, Loading, Modal, PageHeader } from '../../components/ui';
import { useAsync } from '../../hooks/useAsync';
import { useRealtime } from '../../hooks/useRealtime';
import { atendimento, dataHora, duracao, hojeISO, hora, money, STATUS_LABEL } from '../../utils/format';

const STATUS = ['recebido', 'em_preparo', 'pronto', 'entregue', 'cancelado'];

export default function Pedidos() {
  const { pode } = useAuth();
  const [inicio, setInicio] = useState(hojeISO());
  const [fim, setFim] = useState(hojeISO());
  const [status, setStatus] = useState<string[]>([]);
  const [soAtrasados, setSoAtrasados] = useState(false);
  const { data, erro, carregando, recarregar } = useAsync(
    () => api<Pedido[]>('/pedidos/', { query: { inicio, fim, status } }),
    [inicio, fim, status.join(',')],
  );
  useRealtime(() => recarregar(true), 20000);
  const [detalhe, setDetalhe] = useState<number | null>(null);
  const [pagando, setPagando] = useState<Pedido | null>(null);
  const podeReceber = pode('atendente', 'financeiro');

  const lista = (data || []).filter((p) => !soAtrasados || p.atrasado);

  return (
    <div>
      <PageHeader icone={ReceiptText} titulo="Pedidos" subtitulo="Histórico, prazos e pagamentos dos pedidos" />
      <div className="filtros">
        <label>
          De <input type="date" value={inicio} onChange={(e) => setInicio(e.target.value)} />
        </label>
        <label>
          Até <input type="date" value={fim} onChange={(e) => setFim(e.target.value)} />
        </label>
        <div className="chips">
          {STATUS.map((s) => (
            <button
              key={s}
              className={`chip ${status.includes(s) ? 'ativo' : ''}`}
              onClick={() => setStatus((st) => (st.includes(s) ? st.filter((x) => x !== s) : [...st, s]))}
            >
              {STATUS_LABEL[s]}
            </button>
          ))}
        </div>
        <label className="toggle">
          <input type="checkbox" checked={soAtrasados} onChange={(e) => setSoAtrasados(e.target.checked)} /> Só atrasados
        </label>
      </div>
      {erro && <ErrorBox erro={erro} onRetry={() => recarregar()} />}
      {carregando && !data ? (
        <Loading />
      ) : lista.length === 0 ? (
        <Empty>Nenhum pedido no período.</Empty>
      ) : (
        <div className="tabela-wrap">
          <table className="tabela">
            <thead>
              <tr>
                <th>#</th>
                <th>Entrada</th>
                <th>Atendimento</th>
                <th>Itens</th>
                <th>Status</th>
                <th>Prazo</th>
                <th className="num">Total</th>
                <th>Pagamento</th>
              </tr>
            </thead>
            <tbody>
              {lista.map((p) => (
                <tr key={p.id} className={p.atrasado ? 'linha-atrasada' : ''} onClick={() => setDetalhe(p.id)} style={{ cursor: 'pointer' }}>
                  <td>{p.id}</td>
                  <td>{hora(p.created_at)}</td>
                  <td>
                    {pode('atendente') ? <Link to={`/admin/contas/${p.id_sessao}`} onClick={(e) => e.stopPropagation()}>{atendimento(p)}</Link> : atendimento(p)}
                  </td>
                  <td className="small">{p.itens.map((i) => `${i.quantidade}x ${i.nome_produto}`).join(', ')}</td>
                  <td>
                    <Badge status={p.status} />
                  </td>
                  <td>
                    {p.atrasado ? (
                      <span className="texto-erro">+{duracao(p.minutos_atraso)}</span>
                    ) : p.previsao_pronto && ['recebido', 'em_preparo'].includes(p.status) ? (
                      hora(p.previsao_pronto)
                    ) : (
                      '-'
                    )}
                  </td>
                  <td className="num">{money(p.total)}</td>
                  <td onClick={(e) => e.stopPropagation()}>
                    {p.status === 'cancelado' ? (
                      '-'
                    ) : p.pago ? (
                      <Badge status="paga">Pago</Badge>
                    ) : podeReceber && ['pronto', 'entregue'].includes(p.status) ? (
                      <button className="btn btn-sm btn-pagar" onClick={() => setPagando(p)}>
                        <CircleDollarSign size={14} /> Confirmar
                      </button>
                    ) : (
                      <Badge status="pendente">A pagar</Badge>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {detalhe && <ModalDetalhe id={detalhe} onClose={() => setDetalhe(null)} />}
      {pagando && <ModalPagamentoPedido pedido={pagando} onClose={() => setPagando(null)} onPago={() => recarregar(true)} />}
    </div>
  );
}

function ModalDetalhe({ id, onClose }: { id: number; onClose: () => void }) {
  const { data: p, erro, carregando } = useAsync(() => api<Pedido>(`/pedidos/${id}`), [id]);
  return (
    <Modal titulo={`Pedido #${id}`} onClose={onClose} largo>
      {carregando ? (
        <Loading />
      ) : erro || !p ? (
        <ErrorBox erro={erro || 'Erro'} />
      ) : (
        <div className="form">
          <div>
            <Badge status={p.status} /> {atendimento(p)} · entrada {dataHora(p.created_at)} · origem {p.origem}
          </div>
          {p.observacao && (
            <p className="com-icone">
              <MessageSquareText size={16} /> {p.observacao}
            </p>
          )}
          {p.motivo_atraso && <p>Motivo do atraso: {p.motivo_atraso}</p>}
          <div className="acoes">
            <Link to={`/admin/contas/${p.id_sessao}`} className="btn btn-sm">
              <ExternalLink size={14} /> Abrir conta #{p.id_sessao}
            </Link>
          </div>
          <p className="small">
            Link de acompanhamento do cliente:{' '}
            <a href={`/pedido/${p.codigo_acompanhamento}`} target="_blank" rel="noreferrer">
              abrir
            </a>
          </p>
          <ul className="lista-itens">
            {p.itens.map((i) => (
              <li key={i.id}>
                <span>
                  {i.quantidade}x {i.nome_produto} {i.observacao && <em className="muted">({i.observacao})</em>}
                </span>
                <span>
                  <Badge status={i.status} /> {money(i.subtotal)}
                </span>
              </li>
            ))}
          </ul>
          <h3>Histórico</h3>
          <ul className="historico">
            {p.historico?.map((h, k) => (
              <li key={k}>
                <span className="muted">{dataHora(h.criado_em)}</span>{' '}
                {h.id_item ? `Item ${p.itens.find((i) => i.id === h.id_item)?.nome_produto ?? h.id_item}` : 'Pedido'}:{' '}
                {h.status_anterior ? `${STATUS_LABEL[h.status_anterior]} para ` : ''}
                {STATUS_LABEL[h.status_novo]}
                {h.motivo && <em> — {h.motivo}</em>}
              </li>
            ))}
          </ul>
        </div>
      )}
    </Modal>
  );
}
