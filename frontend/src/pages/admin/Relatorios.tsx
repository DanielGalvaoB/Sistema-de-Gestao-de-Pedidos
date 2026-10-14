import {
  ChartColumn,
  CircleDollarSign,
  FileDown,
  FileSpreadsheet,
  HandCoins,
  ReceiptText,
  ShoppingCart,
  TrendingUp,
  Wallet,
} from 'lucide-react';
import { useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { api, baixarArquivo } from '../../api/client';
import type { Relatorio } from '../../api/types';
import { ErrorBox, Loading, Stat, useToast } from '../../components/ui';
import { useAsync } from '../../hooks/useAsync';
import { hojeISO, METODO_LABEL, money } from '../../utils/format';

const CORES = { vendas: '#6366f1', recebido: '#10b981' };

export default function Relatorios() {
  const toast = useToast();
  const [inicio, setInicio] = useState(hojeISO(-6));
  const [fim, setFim] = useState(hojeISO());
  const [metodo, setMetodo] = useState('');
  const { data: r, erro, carregando, recarregar } = useAsync(
    () => api<Relatorio>('/relatorios/resumo', { query: { inicio, fim, metodo } }),
    [inicio, fim, metodo],
  );

  const exportar = async (formato: 'csv' | 'pdf') => {
    try {
      await baixarArquivo(`/relatorios/extrato.${formato}`, { inicio, fim, metodo }, `extrato_${inicio}_${fim}.${formato}`);
    } catch (e) {
      toast((e as Error).message, 'erro');
    }
  };

  const atalho = (dias: number) => {
    setInicio(hojeISO(-dias));
    setFim(hojeISO());
  };

  const serie = (r?.vendas_por_dia || []).map((d) => ({
    dia: d.dia.slice(8, 10) + '/' + d.dia.slice(5, 7),
    vendas: Number(d.vendas),
    recebido: Number(d.recebido),
  }));

  return (
    <div>
      <div className="pagina-topo">
        <div className="pagina-titulo">
          <span className="pagina-icone">
            <ChartColumn size={22} strokeWidth={1.75} />
          </span>
          <div>
            <h1>Relatórios</h1>
            <p className="muted small">Vendas, recebimentos e extratos do que entrou</p>
          </div>
        </div>
        <div className="acoes">
          <button className="btn" onClick={() => exportar('csv')}>
            <FileSpreadsheet size={16} /> Exportar CSV
          </button>
          <button className="btn" onClick={() => exportar('pdf')}>
            <FileDown size={16} /> Exportar PDF
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
        <div className="chips">
          <button className="chip" onClick={() => atalho(0)}>
            Hoje
          </button>
          <button className="chip" onClick={() => atalho(6)}>
            7 dias
          </button>
          <button className="chip" onClick={() => atalho(29)}>
            30 dias
          </button>
        </div>
        <select value={metodo} onChange={(e) => setMetodo(e.target.value)}>
          <option value="">Todas as formas de pagamento</option>
          {Object.entries(METODO_LABEL).map(([k, v]) => (
            <option key={k} value={k}>
              {v}
            </option>
          ))}
        </select>
      </div>

      {erro && <ErrorBox erro={erro} onRetry={() => recarregar()} />}
      {carregando && !r ? (
        <Loading />
      ) : (
        r && (
          <>
            <div className="stats">
              <Stat rotulo="Vendas" valor={money(r.total_vendas)} icone={TrendingUp} destaque="info" />
              <Stat rotulo="Recebido" valor={money(r.total_recebido)} destaque="ok" icone={Wallet} />
              <Stat rotulo="Outras entradas" valor={money(r.outras_entradas)} icone={HandCoins} />
              <Stat rotulo="Total que entrou" valor={money(r.total_entradas)} destaque="ok" icone={Wallet} />
              <Stat rotulo="A receber" valor={money(r.pendente_recebimento)} icone={CircleDollarSign} destaque="aviso" />
              <Stat rotulo="Pedidos" valor={r.quantidade_pedidos} icone={ShoppingCart} />
              <Stat rotulo="Ticket médio" valor={money(r.ticket_medio)} icone={ReceiptText} />
            </div>

            <section className="card">
              <h2>Por dia</h2>
              <div style={{ width: '100%', height: 280 }}>
                <ResponsiveContainer>
                  <BarChart data={serie}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="dia" />
                    <YAxis width={70} tickFormatter={(v) => money(v).replace(',00', '')} />
                    <Tooltip formatter={(v: number) => money(v)} />
                    <Legend />
                    <Bar dataKey="vendas" name="Vendas" fill={CORES.vendas} />
                    <Bar dataKey="recebido" name="Recebido" fill={CORES.recebido} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </section>

            <div className="grid-2-col">
              <Ranking titulo="Produtos mais vendidos" itens={r.produtos_mais_vendidos} mostrarQtd />
              <Ranking
                titulo="Recebido por método"
                itens={r.recebido_por_metodo.map((x) => ({ ...x, rotulo: METODO_LABEL[x.rotulo] || x.rotulo }))}
              />
            </div>

            <details className="card">
              <summary>Critérios dos relatórios</summary>
              <ul className="small">
                {Object.entries(r.criterios).map(([k, v]) => (
                  <li key={k}>
                    <strong>{k}</strong>: {v}
                  </li>
                ))}
              </ul>
            </details>
          </>
        )
      )}
    </div>
  );
}

function Ranking({
  titulo,
  itens,
  mostrarQtd,
}: {
  titulo: string;
  itens: { rotulo: string; valor: string; quantidade: number }[];
  mostrarQtd?: boolean;
}) {
  const max = Math.max(...itens.map((i) => Number(i.valor)), 1);
  return (
    <section className="card">
      <h2>{titulo}</h2>
      {itens.length === 0 && <p className="muted">Sem dados no período.</p>}
      <ul className="ranking">
        {itens.map((i) => (
          <li key={i.rotulo}>
            <div className="ranking-linha">
              <span>{i.rotulo}</span>
              <span>
                {mostrarQtd && <span className="muted">{i.quantidade} un · </span>}
                {money(i.valor)}
              </span>
            </div>
            <div className="ranking-barra" style={{ width: `${(Number(i.valor) / max) * 100}%` }} />
          </li>
        ))}
      </ul>
    </section>
  );
}
