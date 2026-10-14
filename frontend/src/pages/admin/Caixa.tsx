import { Armchair, ChevronRight, CircleDollarSign, CreditCard, Plus, Search, ShoppingBag, Store } from 'lucide-react';
import { useMemo, useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../../api/client';
import type { Conta, Pedido } from '../../api/types';
import { useAuth } from '../../auth/AuthContext';
import { ModalPagamentoPedido } from '../../components/PagamentoPedido';
import { Badge, Empty, ErrorBox, Loading, Modal } from '../../components/ui';
import { useAsync } from '../../hooks/useAsync';
import { useRealtime } from '../../hooks/useRealtime';
import { dataHora, hora, money, TIPO_LABEL } from '../../utils/format';

function tituloConta(c: Conta) {
  if (c.mesa_numero) return `Mesa ${c.mesa_numero}`;
  return `${TIPO_LABEL[c.tipo]}${c.cliente_nome ? ` · ${c.cliente_nome}` : ''}`;
}

export default function Caixa() {
  const { pode } = useAuth();
  const [filtro, setFiltro] = useState<'abertas' | 'encerradas'>('abertas');
  const [busca, setBusca] = useState('');
  const status = filtro === 'abertas' ? ['aberta', 'aguardando_pagamento'] : ['encerrada', 'cancelada'];
  const { data, erro, carregando, recarregar } = useAsync(
    () => api<Conta[]>('/contas/', { query: { status, com_pedidos: true } }),
    [filtro],
  );
  // Contas novas (pedidos feitos no cardapio) aparecem sozinhas
  useRealtime(() => recarregar(true), 10000);
  const [nova, setNova] = useState(false);
  const [pagando, setPagando] = useState<Pedido | null>(null);

  const contas = useMemo(() => {
    const termo = busca.trim().toLowerCase();
    if (!termo) return data || [];
    return (data || []).filter(
      (c) =>
        tituloConta(c).toLowerCase().includes(termo) ||
        String(c.id) === termo.replace('#', '') ||
        c.pedidos?.some((p) => String(p.id) === termo.replace('#', '')),
    );
  }, [data, busca]);

  const saldoTotal = (data || []).reduce((s, c) => s + Math.max(Number(c.resumo.saldo), 0), 0);

  return (
    <div>
      <div className="pagina-topo">
        <div className="pagina-titulo">
          <span className="pagina-icone">
            <CreditCard size={22} strokeWidth={1.75} />
          </span>
          <div>
            <h1>Caixa</h1>
            <p className="muted small">
              Cada pedido abre sua conta automaticamente. Toque em uma conta para receber, ajustar ou encerrar.
            </p>
          </div>
        </div>
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
              <Plus size={16} /> Nova conta
            </button>
          )}
        </div>
      </div>

      <div className="filtros">
        <div className="input-icone">
          <Search size={16} />
          <input
            placeholder="Buscar por mesa, cliente, nº da conta ou do pedido"
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
          />
        </div>
        {filtro === 'abertas' && data && (
          <span className="muted small">
            {data.length} conta(s) em aberto · <strong className="texto-erro">{money(saldoTotal)}</strong> a receber
          </span>
        )}
      </div>

      {erro && <ErrorBox erro={erro} onRetry={() => recarregar()} />}
      {carregando && !data ? (
        <Loading />
      ) : contas.length === 0 ? (
        <Empty icone={CreditCard}>
          {busca ? 'Nenhuma conta encontrada.' : `Nenhuma conta ${filtro === 'abertas' ? 'em aberto' : 'encerrada'}.`}
        </Empty>
      ) : (
        <div className="contas-grid">
          {contas.map((c) => (
            <CartaoConta key={c.id} conta={c} onPagar={pode('atendente', 'financeiro') ? setPagando : undefined} />
          ))}
        </div>
      )}
      {nova && <ModalNovaConta onClose={() => setNova(false)} />}
      {pagando && <ModalPagamentoPedido pedido={pagando} onClose={() => setPagando(null)} onPago={() => recarregar(true)} />}
    </div>
  );
}

function CartaoConta({ conta: c, onPagar }: { conta: Conta; onPagar?: (p: Pedido) => void }) {
  const navigate = useNavigate();
  const saldo = Number(c.resumo.saldo);
  const aberta = c.status === 'aberta' || c.status === 'aguardando_pagamento';
  const Icone = c.mesa_numero ? Armchair : c.tipo === 'retirada' ? ShoppingBag : Store;
  const pedidos = (c.pedidos || []).filter((p) => p.status !== 'cancelado');
  const abrir = () => navigate(`/admin/contas/${c.id}`);

  return (
    <article
      className={`conta-card ${saldo > 0 && aberta ? 'com-saldo' : ''}`}
      role="link"
      tabIndex={0}
      onClick={abrir}
      onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && (e.preventDefault(), abrir())}
      aria-label={`Abrir conta ${c.id}`}
    >
      <header className="conta-card-topo">
        <span className="conta-icone">
          <Icone size={18} />
        </span>
        <div className="conta-card-titulo">
          <strong>{tituloConta(c)}</strong>
          <span className="muted small">
            Conta #{c.id} · aberta {hora(c.aberta_em)}
          </span>
        </div>
        <Badge status={c.status} />
      </header>

      <div className="conta-pedidos">
        {pedidos.length === 0 && <p className="muted small">Nenhum pedido ainda.</p>}
        {pedidos.map((p) => (
          <div key={p.id} className="conta-pedido">
            <div className="conta-pedido-topo">
              <span>
                Pedido #{p.id} · {hora(p.created_at)}
              </span>
              <Badge status={p.status} />
              <Badge status={p.pago ? 'paga' : 'pendente'}>{p.pago ? 'Pago' : 'A pagar'}</Badge>
            </div>
            <ul>
              {p.itens
                .filter((i) => i.status !== 'cancelado')
                .map((i) => (
                  <li key={i.id}>
                    <span>
                      {i.quantidade}x {i.nome_produto}
                    </span>
                    <span>{money(i.subtotal)}</span>
                  </li>
                ))}
            </ul>
            {onPagar && aberta && !p.pago && ['pronto', 'entregue'].includes(p.status) && (
              <button
                className="btn btn-sm btn-pagar"
                onClick={(e) => {
                  e.stopPropagation();
                  onPagar(p);
                }}
              >
                <CircleDollarSign size={14} /> Confirmar pagamento
              </button>
            )}
          </div>
        ))}
      </div>

      <footer className="conta-card-rodape">
        <div>
          <span className="muted small">Total {money(c.resumo.total)}</span>
          <strong className={saldo > 0 ? 'texto-erro' : 'texto-ok'}>
            {saldo > 0 ? `Saldo ${money(saldo)}` : 'Quitada'}
          </strong>
        </div>
        <Link to={`/admin/contas/${c.id}`} className="btn btn-sm" onClick={(e) => e.stopPropagation()}>
          Abrir conta <ChevronRight size={14} />
        </Link>
      </footer>
      {c.encerrada_em && <span className="muted small">Encerrada em {dataHora(c.encerrada_em)}</span>}
    </article>
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
        <p className="muted small">
          Use para lançar um pedido pelo caixa. Pedidos feitos pelo cardápio já abrem a conta sozinhos.
        </p>
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
