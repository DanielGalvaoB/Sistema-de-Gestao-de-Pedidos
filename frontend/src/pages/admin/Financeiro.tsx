import { HandCoins, Pencil, Plus, ReceiptText, Wallet, XCircle } from 'lucide-react';
import { useState, type FormEvent } from 'react';
import { api } from '../../api/client';
import type { CategoriaFinanceira, Movimentacao } from '../../api/types';
import { Badge, ConfirmModal, Empty, ErrorBox, Loading, Modal, Stat, useToast } from '../../components/ui';
import { useAsync } from '../../hooks/useAsync';
import { dataHora, hojeISO, METODO_LABEL, money } from '../../utils/format';

/** Controle do que entra: recebimentos dos pedidos e outras entradas. */
export default function Financeiro() {
  const toast = useToast();
  const [inicio, setInicio] = useState(hojeISO(-30));
  const [fim, setFim] = useState(hojeISO());
  const [categoria, setCategoria] = useState('');
  const [metodo, setMetodo] = useState('');
  const [statusMov, setStatusMov] = useState('ativa');
  const cats = useAsync(() => api<CategoriaFinanceira[]>('/financeiro/categorias'), []);
  const movs = useAsync(
    () =>
      api<Movimentacao[]>('/financeiro/movimentacoes', {
        query: { inicio, fim, id_categoria: categoria, metodo, status_mov: statusMov },
      }),
    [inicio, fim, categoria, metodo, statusMov],
  );
  const [editar, setEditar] = useState<Movimentacao | 'nova' | null>(null);
  const [cancelar, setCancelar] = useState<Movimentacao | null>(null);

  const ativas = (movs.data || []).filter((m) => m.status === 'ativa');
  const pedidos = ativas.filter((m) => m.automatica).reduce((s, m) => s + Number(m.valor), 0);
  const outras = ativas.filter((m) => !m.automatica).reduce((s, m) => s + Number(m.valor), 0);

  return (
    <div>
      <div className="pagina-topo">
        <div className="pagina-titulo">
          <span className="pagina-icone">
            <Wallet size={22} strokeWidth={1.75} />
          </span>
          <div>
            <h1>Recebimentos</h1>
            <p className="muted small">Tudo o que entrou: pagamentos dos pedidos e outras entradas</p>
          </div>
        </div>
        <div className="acoes">
          <button className="btn btn-primario" onClick={() => setEditar('nova')}>
            <Plus size={16} /> Outra entrada
          </button>
        </div>
      </div>

      <div className="filtros">
        <label>
          De <input type="date" value={inicio} onChange={(e) => setInicio(e.target.value)} />
        </label>
        <label>
          Até <input type="date" value={fim} onChange={(e) => setFim(e.target.value)} />
        </label>
        <select value={categoria} onChange={(e) => setCategoria(e.target.value)}>
          <option value="">Todas as origens</option>
          {cats.data?.map((c) => (
            <option key={c.id} value={c.id}>
              {c.sistema ? 'Pagamentos de pedidos' : c.nome}
            </option>
          ))}
        </select>
        <select value={metodo} onChange={(e) => setMetodo(e.target.value)}>
          <option value="">Todas as formas</option>
          {Object.entries(METODO_LABEL).map(([k, v]) => (
            <option key={k} value={k}>
              {v}
            </option>
          ))}
        </select>
        <select value={statusMov} onChange={(e) => setStatusMov(e.target.value)}>
          <option value="ativa">Válidas</option>
          <option value="cancelada">Canceladas/estornadas</option>
          <option value="">Todas</option>
        </select>
      </div>

      <div className="stats">
        <Stat rotulo="Pagamentos de pedidos" valor={money(pedidos)} destaque="ok" icone={ReceiptText} />
        <Stat rotulo="Outras entradas" valor={money(outras)} destaque="info" icone={HandCoins} />
        <Stat rotulo="Total recebido" valor={money(pedidos + outras)} icone={Wallet} />
      </div>

      {movs.erro && <ErrorBox erro={movs.erro} onRetry={() => movs.recarregar()} />}
      {movs.carregando && !movs.data ? (
        <Loading />
      ) : movs.data?.length === 0 ? (
        <Empty icone={Wallet}>Nenhum recebimento no período.</Empty>
      ) : (
        <div className="tabela-wrap">
          <table className="tabela">
            <thead>
              <tr>
                <th>Data</th>
                <th>Descrição</th>
                <th>Origem</th>
                <th>Forma</th>
                <th className="num">Valor</th>
                <th>Status</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {movs.data?.map((m) => (
                <tr key={m.id} className={m.status === 'cancelada' ? 'linha-inativa' : ''}>
                  <td>{dataHora(m.data_hora)}</td>
                  <td>
                    {m.descricao}
                    {m.motivo_cancelamento && <div className="small texto-erro">{m.motivo_cancelamento}</div>}
                  </td>
                  <td>{m.automatica ? <span className="badge badge-info">Pedido</span> : m.categoria_nome}</td>
                  <td>{m.metodo_pagamento ? METODO_LABEL[m.metodo_pagamento] || m.metodo_pagamento : '-'}</td>
                  <td className="num texto-ok">{money(m.valor)}</td>
                  <td>
                    <Badge status={m.status} />
                  </td>
                  <td className="acoes-linha">
                    {m.status === 'ativa' && !m.automatica && (
                      <>
                        <button className="btn btn-sm" onClick={() => setEditar(m)}>
                          <Pencil size={14} /> Editar
                        </button>
                        <button className="btn btn-sm btn-perigo-sutil" onClick={() => setCancelar(m)}>
                          <XCircle size={14} /> Cancelar
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <p className="muted small">
        Os pagamentos dos pedidos entram aqui automaticamente quando são confirmados e só saem por estorno. Nada é
        apagado: cancelamentos ficam registrados com o motivo.
      </p>

      {editar && (
        <ModalEntrada
          mov={editar === 'nova' ? null : editar}
          categorias={(cats.data || []).filter((c) => c.ativo && !c.sistema)}
          onClose={() => setEditar(null)}
          onSalvo={() => {
            setEditar(null);
            toast('Entrada salva');
            movs.recarregar(true);
          }}
        />
      )}
      {cancelar && (
        <ConfirmModal
          titulo="Cancelar entrada"
          mensagem={`${cancelar.descricao} · ${money(cancelar.valor)}`}
          pedirMotivo
          perigo
          onClose={() => setCancelar(null)}
          onConfirm={async (motivo) => {
            await api(`/financeiro/movimentacoes/${cancelar.id}/cancelar`, { body: { motivo } });
            movs.recarregar(true);
          }}
        />
      )}
    </div>
  );
}

function localInput(iso?: string): string {
  const d = iso ? new Date(/[zZ]$/.test(iso) ? iso : `${iso}Z`) : new Date();
  const off = d.getTimezoneOffset() * 60000;
  return new Date(d.getTime() - off).toISOString().slice(0, 16);
}

function ModalEntrada({
  mov,
  categorias,
  onClose,
  onSalvo,
}: {
  mov: Movimentacao | null;
  categorias: CategoriaFinanceira[];
  onClose: () => void;
  onSalvo: () => void;
}) {
  const [f, setF] = useState({
    descricao: mov?.descricao || '',
    id_categoria: mov?.id_categoria || categorias[0]?.id || 0,
    valor: mov?.valor || '',
    data_hora: localInput(mov?.data_hora),
    metodo_pagamento: mov?.metodo_pagamento || '',
    observacao: mov?.observacao || '',
  });
  const [erro, setErro] = useState<string | null>(null);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const body = {
      descricao: f.descricao,
      id_categoria: Number(f.id_categoria),
      valor: Number(String(f.valor).replace(',', '.')).toFixed(2),
      data_hora: new Date(f.data_hora).toISOString(),
      metodo_pagamento: f.metodo_pagamento || null,
      observacao: f.observacao || null,
    };
    try {
      if (mov) await api(`/financeiro/movimentacoes/${mov.id}`, { method: 'PATCH', body });
      else await api('/financeiro/movimentacoes', { body: { ...body, tipo: 'entrada' } });
      onSalvo();
    } catch (err) {
      setErro((err as Error).message);
    }
  };

  return (
    <Modal titulo={mov ? 'Editar entrada' : 'Outra entrada'} onClose={onClose}>
      <form className="form" onSubmit={submit}>
        <p className="muted small">
          Use apenas para valores recebidos fora dos pedidos. Pagamentos de pedidos são registrados automaticamente.
        </p>
        <label>
          Descrição
          <input value={f.descricao} onChange={(e) => setF({ ...f, descricao: e.target.value })} required maxLength={200} />
        </label>
        <div className="grid-2">
          <label>
            Valor (R$)
            <input inputMode="decimal" value={f.valor} onChange={(e) => setF({ ...f, valor: e.target.value })} required />
          </label>
          <label>
            Forma de recebimento
            <select value={f.metodo_pagamento} onChange={(e) => setF({ ...f, metodo_pagamento: e.target.value })}>
              <option value="">-</option>
              {Object.entries(METODO_LABEL).map(([k, v]) => (
                <option key={k} value={k}>
                  {v}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="grid-2">
          <label>
            Data e hora
            <input type="datetime-local" value={f.data_hora} onChange={(e) => setF({ ...f, data_hora: e.target.value })} required />
          </label>
          {categorias.length > 1 && (
            <label>
              Categoria
              <select value={f.id_categoria} onChange={(e) => setF({ ...f, id_categoria: Number(e.target.value) })}>
                {categorias.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nome}
                  </option>
                ))}
              </select>
            </label>
          )}
        </div>
        <label>
          Observações
          <textarea value={f.observacao} onChange={(e) => setF({ ...f, observacao: e.target.value })} maxLength={500} />
        </label>
        {erro && <ErrorBox erro={erro} />}
        <div className="form-actions">
          <button className="btn btn-primario">Salvar</button>
        </div>
      </form>
    </Modal>
  );
}
