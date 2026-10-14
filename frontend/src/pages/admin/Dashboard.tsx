import {
  AlarmClock,
  Armchair,
  ArrowRight,
  CircleCheck,
  CircleDollarSign,
  Flame,
  HandCoins,
  LayoutDashboard,
  ReceiptText,
  TrendingUp,
  Wallet,
} from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../api/client';
import type { Mesa, Pedido, Relatorio } from '../../api/types';
import { useAuth } from '../../auth/AuthContext';
import { ModalPagamentoPedido } from '../../components/PagamentoPedido';
import { Badge, Empty, ErrorBox, Loading, PageHeader, Stat } from '../../components/ui';
import { useAsync } from '../../hooks/useAsync';
import { useRealtime } from '../../hooks/useRealtime';
import { atendimento, duracao, hojeISO, money } from '../../utils/format';

export default function Dashboard() {
  const { pode, user } = useAuth();
  const operacao = pode('atendente');
  const financeiro = pode('financeiro');
  const podeReceber = pode('atendente', 'financeiro');
  const [pagando, setPagando] = useState<Pedido | null>(null);

  const op = useAsync(async () => {
    if (!operacao) return null;
    const [pedidos, mesas, hoje] = await Promise.all([
      api<Pedido[]>('/pedidos/', { query: { ativos: true } }),
      api<Mesa[]>('/mesas/'),
      api<Pedido[]>('/pedidos/', { query: { status: ['pronto', 'entregue'], inicio: hojeISO(-1), fim: hojeISO() } }),
    ]);
    return { pedidos, mesas, aPagar: hoje.filter((p) => !p.pago) };
  }, [operacao]);
  const fin = useAsync(
    () => (financeiro ? api<Relatorio>('/relatorios/resumo', { query: { inicio: hojeISO(), fim: hojeISO() } }) : Promise.resolve(null)),
    [financeiro],
  );
  useRealtime(() => {
    op.recarregar(true);
    fin.recarregar(true);
  }, 20000);

  if ((op.carregando && !op.data) || (fin.carregando && !fin.data)) return <Loading />;

  const pedidos = op.data?.pedidos || [];
  const mesas = op.data?.mesas || [];
  const aPagar = op.data?.aPagar || [];
  const atrasados = pedidos.filter((p) => p.atrasado);
  const emPreparo = pedidos.filter((p) => p.status !== 'pronto');

  return (
    <div>
      <PageHeader
        icone={LayoutDashboard}
        titulo="Painel de hoje"
        subtitulo={`Olá, ${user?.nome}. ${new Date().toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' })}`}
      />
      {op.erro && <ErrorBox erro={op.erro} />}
      {fin.erro && <ErrorBox erro={fin.erro} />}

      <div className="stats">
        {operacao && (
          <>
            <Stat rotulo="Em preparo" valor={emPreparo.length} icone={Flame} destaque="aviso" />
            <Stat rotulo="Atrasados" valor={atrasados.length} icone={AlarmClock} destaque={atrasados.length ? 'erro' : undefined} />
            <Stat rotulo="Aguardando pagamento" valor={aPagar.length} icone={HandCoins} destaque={aPagar.length ? 'info' : undefined} />
            <Stat
              rotulo="Mesas ocupadas"
              valor={`${mesas.filter((m) => m.situacao !== 'livre').length}/${mesas.length}`}
              icone={Armchair}
            />
          </>
        )}
        {fin.data && (
          <>
            <Stat rotulo="Vendas hoje" valor={money(fin.data.total_vendas)} icone={TrendingUp} />
            <Stat rotulo="Recebido hoje" valor={money(fin.data.total_recebido)} icone={Wallet} destaque="ok" />
            <Stat rotulo="A receber" valor={money(fin.data.pendente_recebimento)} icone={CircleDollarSign} />
            <Stat rotulo="Ticket médio" valor={money(fin.data.ticket_medio)} icone={ReceiptText} />
          </>
        )}
      </div>

      {operacao && (
        <div className="grid-3-col">
          <section className="card">
            <h2 className="card-titulo">
              <HandCoins size={18} /> Prontos aguardando pagamento
            </h2>
            {aPagar.length === 0 ? (
              <Empty icone={CircleCheck}>Nenhum pedido pendente de pagamento.</Empty>
            ) : (
              <ul className="lista-acao">
                {aPagar.map((p) => (
                  <li key={p.id}>
                    <div>
                      <strong>#{p.id}</strong> · {atendimento(p)}
                      <div className="muted small">
                        <Badge status={p.status} /> {money(p.saldo)} a receber
                      </div>
                    </div>
                    {podeReceber && (
                      <button className="btn btn-sm btn-pagar" onClick={() => setPagando(p)}>
                        <CircleDollarSign size={14} /> Confirmar
                      </button>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </section>
          <section className="card">
            <h2 className="card-titulo">
              <AlarmClock size={18} /> Pedidos atrasados
            </h2>
            {atrasados.length === 0 ? (
              <Empty icone={CircleCheck}>Nenhum pedido atrasado.</Empty>
            ) : (
              <ul className="lista-acao">
                {atrasados.map((p) => (
                  <li key={p.id}>
                    <span>
                      <strong>#{p.id}</strong> · {atendimento(p)}
                    </span>
                    <span className="texto-erro">+{duracao(p.minutos_atraso)}</span>
                  </li>
                ))}
              </ul>
            )}
            <Link to="/admin/cozinha" className="link-seta">
              Abrir painel da cozinha <ArrowRight size={14} />
            </Link>
          </section>
          <section className="card">
            <h2 className="card-titulo">
              <Armchair size={18} /> Mesas aguardando pagamento
            </h2>
            {mesas.filter((m) => m.situacao === 'aguardando_pagamento').length === 0 ? (
              <Empty icone={CircleCheck}>Nenhuma mesa aguardando.</Empty>
            ) : (
              <ul className="lista-acao">
                {mesas
                  .filter((m) => m.situacao === 'aguardando_pagamento')
                  .map((m) => (
                    <li key={m.id}>
                      <Link to={`/admin/contas/${m.id_sessao}`}>Mesa {m.numero}</Link>
                      <strong>{money(m.total_consumido)}</strong>
                    </li>
                  ))}
              </ul>
            )}
            <Link to="/admin/mesas" className="link-seta">
              Ver todas as mesas <ArrowRight size={14} />
            </Link>
          </section>
        </div>
      )}
      {pagando && <ModalPagamentoPedido pedido={pagando} onClose={() => setPagando(null)} onPago={() => op.recarregar(true)} />}
    </div>
  );
}
