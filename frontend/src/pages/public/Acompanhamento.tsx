import { useParams } from 'react-router-dom';
import { api } from '../../api/client';
import type { PedidoAcompanhamento } from '../../api/types';
import { Badge, ErrorBox, Loading } from '../../components/ui';
import { useAsync, useInterval } from '../../hooks/useAsync';
import { atendimento, hora, money, STATUS_LABEL } from '../../utils/format';

const ETAPAS = [
  { status: 'recebido', campo: 'created_at', label: 'Recebido' },
  { status: 'em_preparo', campo: 'iniciado_em', label: 'Em preparo' },
  { status: 'pronto', campo: 'pronto_em', label: 'Pronto' },
  { status: 'entregue', campo: 'entregue_em', label: 'Entregue' },
] as const;

export default function Acompanhamento() {
  const { codigo = '' } = useParams();
  const { data, erro, carregando, recarregar } = useAsync(
    () => api<PedidoAcompanhamento>(`/public/pedidos/${codigo}`, { auth: false }),
    [codigo],
  );
  const finalizado = data && ['entregue', 'cancelado'].includes(data.status);
  useInterval(() => recarregar(true), finalizado ? null : 8000);

  if (carregando) return <Loading />;
  if (erro || !data)
    return (
      <div className="publico">
        <ErrorBox erro={erro || 'Pedido não encontrado'} onRetry={() => recarregar()} />
      </div>
    );

  const idxAtual = ETAPAS.findIndex((e) => e.status === data.status);

  return (
    <div className="publico">
      <header className="publico-header">
        <h1>{data.nome_loja}</h1>
        <p>
          Pedido nº {data.numero} · {atendimento(data)}
        </p>
      </header>

      <div className="card acompanhamento">
        <div className="acompanhamento-status">
          <Badge status={data.status} />
          {data.status === 'pronto' && <p className="destaque">Seu pedido está pronto! 🎉</p>}
          {data.status === 'cancelado' && <p className="destaque erro">Pedido cancelado.</p>}
        </div>

        {data.status !== 'cancelado' && (
          <ol className="linha-tempo">
            {ETAPAS.map((e, i) => (
              <li key={e.status} className={i <= idxAtual ? 'feito' : ''}>
                <span className="ponto" />
                <span>{e.label}</span>
                <span className="muted">{hora(data[e.campo])}</span>
              </li>
            ))}
          </ol>
        )}

        {data.previsao_pronto && ['recebido', 'em_preparo'].includes(data.status) && (
          <div className={`alert ${data.atrasado ? 'alert-aviso' : 'alert-info'}`}>
            Previsão: {hora(data.previsao_pronto)}
            {data.atrasado && ' — estamos um pouco atrasados, já já fica pronto.'}
            {data.motivo_atraso && <div className="small">Motivo: {data.motivo_atraso}</div>}
          </div>
        )}

        <ul className="lista-itens">
          {data.itens.map((i, k) => (
            <li key={k}>
              <span>
                {i.quantidade}× {i.nome_produto}
              </span>
              <span className="muted small">{STATUS_LABEL[i.status]}</span>
            </li>
          ))}
        </ul>
        <div className="carrinho-total">
          <span>Total</span>
          <strong>{money(data.total)}</strong>
        </div>
        <p className="muted small">Esta página atualiza automaticamente.</p>
      </div>
    </div>
  );
}
