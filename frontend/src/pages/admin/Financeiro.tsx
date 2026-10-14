import { useState, type FormEvent } from 'react';
import { api } from '../../api/client';
import type { CategoriaFinanceira, Movimentacao } from '../../api/types';
import { Badge, ConfirmModal, Empty, ErrorBox, Loading, Modal, Stat, useToast } from '../../components/ui';
import { useAsync } from '../../hooks/useAsync';
import { dataHora, hojeISO, METODO_LABEL, money } from '../../utils/format';

export default function Financeiro() {
  const toast = useToast();
  const [inicio, setInicio] = useState(hojeISO(-30));
  const [fim, setFim] = useState(hojeISO());
  const [tipo, setTipo] = useState('');
  const [categoria, setCategoria] = useState('');
  const [statusMov, setStatusMov] = useState('ativa');
  const cats = useAsync(() => api<CategoriaFinanceira[]>('/financeiro/categorias'), []);
  const movs = useAsync(
    () =>
      api<Movimentacao[]>('/financeiro/movimentacoes', {
        query: { inicio, fim, tipo, id_categoria: categoria, status_mov: statusMov },
      }),
    [inicio, fim, tipo, categoria, statusMov],
  );
  const [novo, setNovo] = useState<Movimentacao | 'entrada' | 'saida' | null>(null);
  const [cancelar, setCancelar] = useState<Movimentacao | null>(null);
  const [novaCat, setNovaCat] = useState(false);

  const ativas = (movs.data || []).filter((m) => m.status === 'ativa');
  const entradas = ativas.filter((m) => m.tipo === 'entrada').reduce((s, m) => s + Number(m.valor), 0);
  const saidas = ativas.filter((m) => m.tipo === 'saida').reduce((s, m) => s + Number(m.valor), 0);

  return (
    <div>
      <div className="pagina-topo">
        <h1>Financeiro</h1>
        <div className="acoes">
          <button className="btn" onClick={() => setNovaCat(true)}>
            + Categoria
          </button>
          <button className="btn btn-ok" onClick={() => setNovo('entrada')}>
            + Entrada
          </button>
          <button className="btn btn-perigo" onClick={() => setNovo('saida')}>
            + Saída
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
        <select value={tipo} onChange={(e) => setTipo(e.target.value)}>
          <option value="">Entradas e saídas</option>
          <option value="entrada">Entradas</option>
          <option value="saida">Saídas</option>
        </select>
        <select value={categoria} onChange={(e) => setCategoria(e.target.value)}>
          <option value="">Todas as categorias</option>
          {cats.data?.map((c) => (
            <option key={c.id} value={c.id}>
              {c.tipo === 'entrada' ? '↑' : '↓'} {c.nome}
            </option>
          ))}
        </select>
        <select value={statusMov} onChange={(e) => setStatusMov(e.target.value)}>
          <option value="ativa">Ativas</option>
          <option value="cancelada">Canceladas</option>
          <option value="">Todas</option>
        </select>
      </div>

      <div className="stats">
        <Stat rotulo="Entradas" valor={money(entradas)} destaque="ok" />
        <Stat rotulo="Saídas" valor={money(saidas)} destaque="erro" />
        <Stat rotulo="Saldo" valor={money(entradas - saidas)} />
      </div>

      {movs.erro && <ErrorBox erro={movs.erro} onRetry={() => movs.recarregar()} />}
      {movs.carregando && !movs.data ? (
        <Loading />
      ) : movs.data?.length === 0 ? (
        <Empty>Nenhuma movimentação no período.</Empty>
      ) : (
        <div className="tabela-wrap">
          <table className="tabela">
            <thead>
              <tr>
                <th>Data</th>
                <th>Descrição</th>
                <th>Categoria</th>
                <th>Método</th>
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
                    {m.automatica && <span className="badge badge-info">automático</span>}
                    {m.motivo_cancelamento && <div className="small texto-erro">{m.motivo_cancelamento}</div>}
                  </td>
                  <td>{m.categoria_nome}</td>
                  <td>{m.metodo_pagamento ? METODO_LABEL[m.metodo_pagamento] || m.metodo_pagamento : '-'}</td>
                  <td className={`num ${m.tipo === 'entrada' ? 'texto-ok' : 'texto-erro'}`}>
                    {m.tipo === 'entrada' ? '+' : '−'} {money(m.valor)}
                  </td>
                  <td>
                    <Badge status={m.status} />
                  </td>
                  <td className="acoes-linha">
                    {m.status === 'ativa' && !m.automatica && (
                      <>
                        <button className="btn btn-sm" onClick={() => setNovo(m)}>
                          Editar
                        </button>
                        <button className="btn btn-sm btn-perigo-sutil" onClick={() => setCancelar(m)}>
                          Cancelar
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
        Recebimentos de vendas entram automaticamente quando um pagamento é registrado e só saem por estorno. Lançamentos
        nunca são apagados: o cancelamento fica registrado com motivo.
      </p>

      {novo && (
        <ModalMov
          mov={typeof novo === 'string' ? null : novo}
          tipo={typeof novo === 'string' ? novo : novo.tipo}
          categorias={(cats.data || []).filter((c) => c.ativo && !c.sistema)}
          onClose={() => setNovo(null)}
          onSalvo={() => {
            setNovo(null);
            toast('Lançamento salvo');
            movs.recarregar(true);
          }}
        />
      )}
      {cancelar && (
        <ConfirmModal
          titulo="Cancelar lançamento"
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
      {novaCat && (
        <ModalCategoria
          onClose={() => setNovaCat(false)}
          onSalvo={() => {
            setNovaCat(false);
            cats.recarregar(true);
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

function ModalMov({
  mov,
  tipo,
  categorias,
  onClose,
  onSalvo,
}: {
  mov: Movimentacao | null;
  tipo: 'entrada' | 'saida';
  categorias: CategoriaFinanceira[];
  onClose: () => void;
  onSalvo: () => void;
}) {
  const opcoes = categorias.filter((c) => c.tipo === tipo);
  const [f, setF] = useState({
    descricao: mov?.descricao || '',
    id_categoria: mov?.id_categoria || opcoes[0]?.id || 0,
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
      else await api('/financeiro/movimentacoes', { body: { ...body, tipo } });
      onSalvo();
    } catch (err) {
      setErro((err as Error).message);
    }
  };

  return (
    <Modal titulo={`${mov ? 'Editar' : 'Nova'} ${tipo === 'entrada' ? 'entrada' : 'saída'}`} onClose={onClose}>
      <form className="form" onSubmit={submit}>
        <label>
          Descrição
          <input value={f.descricao} onChange={(e) => setF({ ...f, descricao: e.target.value })} required maxLength={200} />
        </label>
        <div className="grid-2">
          <label>
            Categoria
            <select value={f.id_categoria} onChange={(e) => setF({ ...f, id_categoria: Number(e.target.value) })} required>
              {opcoes.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nome}
                </option>
              ))}
            </select>
          </label>
          <label>
            Valor (R$)
            <input inputMode="decimal" value={f.valor} onChange={(e) => setF({ ...f, valor: e.target.value })} required />
          </label>
        </div>
        <div className="grid-2">
          <label>
            Data e hora
            <input type="datetime-local" value={f.data_hora} onChange={(e) => setF({ ...f, data_hora: e.target.value })} required />
          </label>
          <label>
            Método
            <select value={f.metodo_pagamento} onChange={(e) => setF({ ...f, metodo_pagamento: e.target.value })}>
              <option value="">-</option>
              {Object.entries(METODO_LABEL).map(([k, v]) => (
                <option key={k} value={k}>
                  {v}
                </option>
              ))}
              <option value="boleto">Boleto</option>
              <option value="transferencia">Transferência</option>
            </select>
          </label>
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

function ModalCategoria({ onClose, onSalvo }: { onClose: () => void; onSalvo: () => void }) {
  const [nome, setNome] = useState('');
  const [tipo, setTipo] = useState<'entrada' | 'saida'>('saida');
  const [erro, setErro] = useState<string | null>(null);
  return (
    <Modal titulo="Nova categoria financeira" onClose={onClose}>
      <form
        className="form"
        onSubmit={async (e) => {
          e.preventDefault();
          try {
            await api('/financeiro/categorias', { body: { nome, tipo } });
            onSalvo();
          } catch (err) {
            setErro((err as Error).message);
          }
        }}
      >
        <div className="segmentado">
          <button type="button" className={tipo === 'entrada' ? 'ativo' : ''} onClick={() => setTipo('entrada')}>
            Entrada
          </button>
          <button type="button" className={tipo === 'saida' ? 'ativo' : ''} onClick={() => setTipo('saida')}>
            Saída
          </button>
        </div>
        <label>
          Nome
          <input value={nome} onChange={(e) => setNome(e.target.value)} required maxLength={80} />
        </label>
        {erro && <ErrorBox erro={erro} />}
        <div className="form-actions">
          <button className="btn btn-primario">Salvar</button>
        </div>
      </form>
    </Modal>
  );
}
