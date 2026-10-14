import { AlarmClock, BookOpen, CircleCheck, Clock, Flame, HandPlatter, Inbox, PartyPopper, XCircle, type LucideIcon } from 'lucide-react';
import { useEffect } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { api } from '../../api/client';
import type { CardapioPublico, ContaAcompanhamento, PedidoAcompanhamento } from '../../api/types';
import CardapioView, { salvarUltimoPedido } from '../../components/CardapioView';
import PublicoTopo, { type AbaPublica } from '../../components/PublicoTopo';
import { ErrorBox, Loading, useToast } from '../../components/ui';
import { useAsync, useInterval } from '../../hooks/useAsync';
import { hora, money, STATUS_LABEL } from '../../utils/format';

const ETAPAS: { status: string; campo: 'created_at' | 'iniciado_em' | 'pronto_em' | 'entregue_em'; label: string; icone: LucideIcon }[] = [
  { status: 'recebido', campo: 'created_at', label: 'Recebido', icone: Inbox },
  { status: 'em_preparo', campo: 'iniciado_em', label: 'Em preparo', icone: Flame },
  { status: 'pronto', campo: 'pronto_em', label: 'Pronto', icone: CircleCheck },
  { status: 'entregue', campo: 'entregue_em', label: 'Entregue', icone: HandPlatter },
];

const MENSAGEM: Record<string, string> = {
  recebido: 'Recebemos seu pedido e ele já está na fila da cozinha.',
  em_preparo: 'Seu pedido está sendo preparado.',
  pronto: 'Seu pedido está pronto!',
  entregue: 'Pedido entregue. Bom apetite!',
  cancelado: 'Este pedido foi cancelado.',
};

export default function Acompanhamento() {
  const { codigo = '' } = useParams();
  const [sp, setSp] = useSearchParams();
  const aba: AbaPublica = sp.get('aba') === 'cardapio' ? 'cardapio' : 'pedidos';
  const navigate = useNavigate();
  const toast = useToast();

  const { data: conta, erro, carregando, recarregar } = useAsync(
    () => api<ContaAcompanhamento>(`/public/pedidos/${codigo}/conta`, { auth: false }),
    [codigo],
  );
  const atual = useAsync(() => api<PedidoAcompanhamento>(`/public/pedidos/${codigo}`, { auth: false }), [codigo]);
  const slug = conta?.slug;
  const cardapio = useAsync(
    () => (slug && aba === 'cardapio' ? api<CardapioPublico>(`/public/${slug}`, { auth: false }) : Promise.resolve(null)),
    [slug, aba],
  );

  // Lembra o pedido neste aparelho para o cardapio do QR Code
  useEffect(() => {
    if (slug && conta?.conta_aberta) salvarUltimoPedido(slug, codigo);
  }, [slug, codigo, conta?.conta_aberta]);

  const emAndamento = conta?.pedidos.some((p) => !['entregue', 'cancelado'].includes(p.status));
  useInterval(() => {
    recarregar(true);
    atual.recarregar(true);
  }, aba === 'pedidos' && emAndamento !== false ? 8000 : null);

  const trocarAba = (nova: AbaPublica) => {
    setSp(nova === 'cardapio' ? { aba: 'cardapio' } : {}, { replace: true });
    window.scrollTo({ top: 0 });
  };

  if (carregando) return <Loading />;
  if (erro || !conta)
    return (
      <div className="publico">
        <ErrorBox erro={erro || 'Pedido não encontrado'} onRetry={() => recarregar()} />
      </div>
    );

  const numeroAtual = atual.data?.numero;

  return (
    <div className="publico">
      <PublicoTopo
        nomeLoja={conta.nome_loja}
        mesaNumero={conta.mesa_numero}
        aba={aba}
        qtdPedidos={conta.pedidos.length}
        onAba={trocarAba}
      />

      {aba === 'cardapio' ? (
        cardapio.carregando && !cardapio.data ? (
          <Loading texto="Carregando cardápio..." />
        ) : cardapio.erro || !cardapio.data ? (
          <ErrorBox erro={cardapio.erro || 'Cardápio indisponível'} onRetry={() => cardapio.recarregar()} />
        ) : (
          <CardapioView
            slug={conta.slug}
            cardapio={cardapio.data}
            codigoOrigem={codigo}
            onEnviado={(novo, numero) => {
              toast(`Pedido nº ${numero} enviado para a cozinha`);
              navigate(`/pedido/${novo}`, { replace: true });
            }}
          />
        )
      ) : (
        <>
          <div className="conta-publica-resumo">
            <div>
              <span className="muted small">{conta.conta_aberta ? 'Sua conta' : 'Conta encerrada'}</span>
              <strong>{money(conta.total)}</strong>
            </div>
            <button className="btn btn-primario" onClick={() => trocarAba('cardapio')}>
              <BookOpen size={16} /> Pedir mais
            </button>
          </div>

          {conta.pedidos.map((p) => (
            <CartaoAcompanhamento key={p.numero} p={p} destaque={p.numero === numeroAtual} />
          ))}
          <p className="muted small centro">Esta página atualiza automaticamente.</p>
        </>
      )}
    </div>
  );
}

function CartaoAcompanhamento({ p, destaque }: { p: PedidoAcompanhamento; destaque: boolean }) {
  const idxAtual = ETAPAS.findIndex((e) => e.status === p.status);
  const IconeStatus =
    p.status === 'cancelado' ? XCircle : p.status === 'pronto' ? PartyPopper : ETAPAS[idxAtual]?.icone || Clock;

  return (
    <div className={`card acompanhamento ${destaque ? 'acompanhamento-atual' : ''}`}>
      <div className="acompanhamento-cabecalho">
        <span className="muted small">
          Pedido nº {p.numero} · {hora(p.created_at)}
        </span>
        {destaque && <span className="badge badge-info">Último pedido</span>}
      </div>
      <div className={`acompanhamento-status status-${p.status}`}>
        <span className="acompanhamento-icone">
          <IconeStatus size={32} strokeWidth={1.75} />
        </span>
        <strong>{STATUS_LABEL[p.status]}</strong>
        <p>{MENSAGEM[p.status]}</p>
      </div>

      {p.status !== 'cancelado' && (
        <ol className="linha-tempo">
          {ETAPAS.map(({ status, campo, label, icone: Icone }, i) => (
            <li key={status} className={i <= idxAtual ? 'feito' : ''}>
              <span className="ponto">
                <Icone size={16} />
              </span>
              <span>{label}</span>
              <span className="muted small">{hora(p[campo])}</span>
            </li>
          ))}
        </ol>
      )}

      {p.previsao_pronto && ['recebido', 'em_preparo'].includes(p.status) && (
        <div className={`alert ${p.atrasado ? 'alert-aviso' : 'alert-info'}`}>
          {p.atrasado ? <AlarmClock size={18} /> : <Clock size={18} />}
          <div>
            Tivemos um imprevisto. Nova previsão: <strong>{hora(p.previsao_pronto)}</strong>
            {p.atrasado && ' · estamos finalizando, já já fica pronto.'}
            {p.motivo_atraso && <div className="small">Motivo: {p.motivo_atraso}</div>}
          </div>
        </div>
      )}

      <ul className="lista-itens">
        {p.itens.map((i, k) => (
          <li key={k}>
            <span>
              {i.quantidade}x {i.nome_produto}
            </span>
            <span className={`badge badge-${i.status}`}>{STATUS_LABEL[i.status]}</span>
          </li>
        ))}
      </ul>
      <div className="carrinho-total">
        <span>Total do pedido</span>
        <strong>{money(p.total)}</strong>
      </div>
    </div>
  );
}
