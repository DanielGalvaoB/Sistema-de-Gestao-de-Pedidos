import { Link } from 'react-router-dom';
import { api } from '../../api/client';
import type { Mesa, Pedido, Relatorio } from '../../api/types';
import { useAuth } from '../../auth/AuthContext';
import { Badge, ErrorBox, Loading, Stat } from '../../components/ui';
import { useAsync } from '../../hooks/useAsync';
import { useRealtime } from '../../hooks/useRealtime';
import { atendimento, duracao, hojeISO, money } from '../../utils/format';

export default function Dashboard() {
  const { pode } = useAuth();
  const operacao = pode('atendente');
  const financeiro = pode('financeiro');

  const op = useAsync(async () => {
    if (!operacao) return null;
    const [pedidos, mesas] = await Promise.all([
      api<Pedido[]>('/pedidos/', { query: { ativos: true } }),
      api<Mesa[]>('/mesas/'),
    ]);
    return { pedidos, mesas };
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
  const atrasados = pedidos.filter((p) => p.atrasado);

  return (
    <div>
      <div className="pagina-topo">
        <h1>Painel de hoje</h1>
      </div>
      {op.erro && <ErrorBox erro={op.erro} />}
      {fin.erro && <ErrorBox erro={fin.erro} />}

      <div className="stats">
        {operacao && (
          <>
            <Stat rotulo="Pedidos em andamento" valor={pedidos.length} />
            <Stat rotulo="Atrasados" valor={atrasados.length} destaque={atrasados.length ? 'erro' : undefined} />
            <Stat rotulo="Mesas ocupadas" valor={`${mesas.filter((m) => m.situacao !== 'livre').length}/${mesas.length}`} />
          </>
        )}
        {fin.data && (
          <>
            <Stat rotulo="Vendas hoje" valor={money(fin.data.total_vendas)} />
            <Stat rotulo="Recebido hoje" valor={money(fin.data.total_recebido)} destaque="ok" />
            <Stat rotulo="A receber" valor={money(fin.data.pendente_recebimento)} />
            <Stat rotulo="Ticket médio" valor={money(fin.data.ticket_medio)} />
          </>
        )}
      </div>

      {operacao && (
        <div className="grid-2-col">
          <section className="card">
            <h2>Pedidos atrasados</h2>
            {atrasados.length === 0 ? (
              <p className="muted">Nenhum pedido atrasado. 👍</p>
            ) : (
              <ul className="lista-itens">
                {atrasados.map((p) => (
                  <li key={p.id}>
                    <span>
                      #{p.id} · {atendimento(p)}
                    </span>
                    <span className="texto-erro">+{duracao(p.minutos_atraso)}</span>
                  </li>
                ))}
              </ul>
            )}
            <Link to="/admin/cozinha">Abrir painel da cozinha →</Link>
          </section>
          <section className="card">
            <h2>Mesas aguardando pagamento</h2>
            {mesas.filter((m) => m.situacao === 'aguardando_pagamento').length === 0 ? (
              <p className="muted">Nenhuma.</p>
            ) : (
              <ul className="lista-itens">
                {mesas
                  .filter((m) => m.situacao === 'aguardando_pagamento')
                  .map((m) => (
                    <li key={m.id}>
                      <Link to={`/admin/contas/${m.id_sessao}`}>Mesa {m.numero}</Link>
                      <span>
                        <Badge status={m.situacao} /> {money(m.total_consumido)}
                      </span>
                    </li>
                  ))}
              </ul>
            )}
            <Link to="/admin/mesas">Ver todas as mesas →</Link>
          </section>
        </div>
      )}
    </div>
  );
}
