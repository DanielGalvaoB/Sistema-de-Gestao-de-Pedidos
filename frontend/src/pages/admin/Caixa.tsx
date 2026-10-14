import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../../api/client';
import type { Conta } from '../../api/types';
import { useAuth } from '../../auth/AuthContext';
import { Badge, Empty, ErrorBox, Loading, Modal } from '../../components/ui';
import { useAsync } from '../../hooks/useAsync';
import { useRealtime } from '../../hooks/useRealtime';
import { dataHora, money, TIPO_LABEL } from '../../utils/format';

export default function Caixa() {
  const { pode } = useAuth();
  const [filtro, setFiltro] = useState<'abertas' | 'encerradas'>('abertas');
  const status = filtro === 'abertas' ? ['aberta', 'aguardando_pagamento'] : ['encerrada', 'cancelada'];
  const { data, erro, carregando, recarregar } = useAsync(
    () => api<Conta[]>('/contas/', { query: { status } }),
    [filtro],
  );
  useRealtime(() => recarregar(true), 15000);
  const [nova, setNova] = useState(false);

  return (
    <div>
      <div className="pagina-topo">
        <h1>Caixa · contas</h1>
        <div className="acoes">
          <div className="segmentado">
            <button className={filtro === 'abertas' ? 'ativo' : ''} onClick={() => setFiltro('abertas')}>
              Em aberto
            </button>
            <button className={filtro === 'encerradas' ? 'ativo' : ''} onClick={() => setFiltro('encerradas')}>
              Encerradas
            </button>
          </div>
          {pode('atendente') && (
            <button className="btn btn-primario" onClick={() => setNova(true)}>
              + Conta balcão/retirada
            </button>
          )}
        </div>
      </div>
      {erro && <ErrorBox erro={erro} onRetry={() => recarregar()} />}
      {carregando && !data ? (
        <Loading />
      ) : data?.length === 0 ? (
        <Empty>Nenhuma conta {filtro === 'abertas' ? 'em aberto' : 'encerrada'}.</Empty>
      ) : (
        <div className="tabela-wrap">
          <table className="tabela">
            <thead>
              <tr>
                <th>Conta</th>
                <th>Atendimento</th>
                <th>Aberta em</th>
                <th>Status</th>
                <th className="num">Total</th>
                <th className="num">Pago</th>
                <th className="num">Saldo</th>
              </tr>
            </thead>
            <tbody>
              {data?.map((c) => (
                <tr key={c.id}>
                  <td>
                    <Link to={`/admin/contas/${c.id}`}>#{c.id}</Link>
                  </td>
                  <td>
                    {c.mesa_numero ? `Mesa ${c.mesa_numero}` : TIPO_LABEL[c.tipo]}
                    {c.cliente_nome && ` · ${c.cliente_nome}`}
                  </td>
                  <td>{dataHora(c.aberta_em)}</td>
                  <td>
                    <Badge status={c.status} />
                  </td>
                  <td className="num">{money(c.resumo.total)}</td>
                  <td className="num">{money(c.resumo.total_pago)}</td>
                  <td className={`num ${Number(c.resumo.saldo) > 0 ? 'texto-erro' : ''}`}>{money(c.resumo.saldo)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {nova && <ModalNovaConta onClose={() => setNova(false)} />}
    </div>
  );
}

function ModalNovaConta({ onClose }: { onClose: () => void }) {
  const navigate = useNavigate();
  const [tipo, setTipo] = useState<'balcao' | 'retirada'>('balcao');
  const [nome, setNome] = useState('');
  const [erro, setErro] = useState<string | null>(null);
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      const c = await api<Conta>('/contas/', { body: { tipo, cliente_nome: nome || null } });
      navigate(`/admin/contas/${c.id}`);
    } catch (err) {
      setErro((err as Error).message);
    }
  };
  return (
    <Modal titulo="Nova conta sem mesa" onClose={onClose}>
      <form className="form" onSubmit={submit}>
        <div className="segmentado">
          <button type="button" className={tipo === 'balcao' ? 'ativo' : ''} onClick={() => setTipo('balcao')}>
            Balcão
          </button>
          <button type="button" className={tipo === 'retirada' ? 'ativo' : ''} onClick={() => setTipo('retirada')}>
            Retirada
          </button>
        </div>
        <label>
          Nome do cliente (opcional)
          <input value={nome} onChange={(e) => setNome(e.target.value)} maxLength={80} />
        </label>
        {erro && <ErrorBox erro={erro} />}
        <div className="form-actions">
          <button className="btn btn-primario">Abrir conta</button>
        </div>
      </form>
    </Modal>
  );
}
