import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '../../api/client';
import type { ItemPedido, Pedido, StatusPedido } from '../../api/types';
import { Badge, ConfirmModal, ErrorBox, Loading, useToast } from '../../components/ui';
import { useAgora, useAsync } from '../../hooks/useAsync';
import { useRealtime } from '../../hooks/useRealtime';
import { atendimento, duracao, hojeISO, hora, minutosDesde } from '../../utils/format';

const COLUNAS: { status: StatusPedido; titulo: string }[] = [
  { status: 'recebido', titulo: 'Recebido' },
  { status: 'em_preparo', titulo: 'Em preparo' },
  { status: 'pronto', titulo: 'Pronto' },
  { status: 'entregue', titulo: 'Entregue' },
  { status: 'cancelado', titulo: 'Cancelado' },
];

const PROXIMO_ITEM: Partial<Record<StatusPedido, StatusPedido>> = {
  recebido: 'em_preparo',
  em_preparo: 'pronto',
  pronto: 'entregue',
};

function lerPref(chave: string, padrao: boolean) {
  try {
    const v = localStorage.getItem(chave);
    return v === null ? padrao : v === '1';
  } catch {
    return padrao;
  }
}

function beep(frequencias: number[]) {
  try {
    const Ctx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    const ctx = new Ctx();
    frequencias.forEach((f, i) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.frequency.value = f;
      osc.connect(gain);
      gain.connect(ctx.destination);
      const t = ctx.currentTime + i * 0.22;
      gain.gain.setValueAtTime(0.25, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.2);
      osc.start(t);
      osc.stop(t + 0.2);
    });
    setTimeout(() => ctx.close(), 1500);
  } catch {
    /* audio indisponivel */
  }
}

export default function Cozinha() {
  const toast = useToast();
  const agora = useAgora(15000);
  const [somNovo, setSomNovo] = useState(() => lerPref('kds_som_novo', true));
  const [somPronto, setSomPronto] = useState(() => lerPref('kds_som_pronto', true));
  const [mostrarFinalizados, setMostrarFinalizados] = useState(() => lerPref('kds_finalizados', false));
  const [cancelando, setCancelando] = useState<Pedido | null>(null);
  const [atrasando, setAtrasando] = useState<Pedido | null>(null);
  const vistos = useRef<Map<number, StatusPedido> | null>(null);

  const carregar = useCallback(async () => {
    const ativos = await api<Pedido[]>('/pedidos/', { query: { ativos: true } });
    const finalizados = mostrarFinalizados
      ? await api<Pedido[]>('/pedidos/', {
          query: { status: ['entregue', 'cancelado'], inicio: hojeISO(), fim: hojeISO() },
        })
      : [];
    return [...ativos, ...finalizados.slice(0, 30)];
  }, [mostrarFinalizados]);

  const { data: pedidos, erro, carregando, recarregar } = useAsync(carregar, [carregar]);
  const conectado = useRealtime(() => recarregar(true), 10000);

  // Notificacoes de novos pedidos e pedidos prontos
  useEffect(() => {
    if (!pedidos) return;
    const atual = new Map(pedidos.map((p) => [p.id, p.status]));
    if (vistos.current) {
      const novos = pedidos.filter((p) => !vistos.current!.has(p.id) && p.status === 'recebido');
      const prontos = pedidos.filter((p) => p.status === 'pronto' && vistos.current!.get(p.id) !== 'pronto' && vistos.current!.has(p.id));
      if (novos.length) {
        if (somNovo) beep([880, 1175]);
        toast(`${novos.length} novo(s) pedido(s)`);
      }
      if (prontos.length && somPronto) beep([660, 660, 990]);
    }
    vistos.current = atual;
  }, [pedidos, somNovo, somPronto, toast]);

  const salvarPref = (chave: string, v: boolean, set: (v: boolean) => void) => {
    set(v);
    try {
      localStorage.setItem(chave, v ? '1' : '0');
    } catch {
      /* ignora */
    }
  };

  const acao = async (fn: () => Promise<unknown>) => {
    try {
      await fn();
      await recarregar(true);
    } catch (e) {
      toast((e as Error).message, 'erro');
    }
  };

  const mudarPedido = (p: Pedido, status: StatusPedido, motivo?: string) =>
    acao(() => api(`/pedidos/${p.id}/status`, { method: 'PATCH', body: { status, motivo } }));

  const mudarItem = (p: Pedido, item: ItemPedido, status: StatusPedido) =>
    acao(() => api(`/pedidos/${p.id}/itens/${item.id}/status`, { method: 'PATCH', body: { status } }));

  if (carregando && !pedidos) return <Loading />;

  const colunas = mostrarFinalizados ? COLUNAS : COLUNAS.slice(0, 3);

  return (
    <div className="kds">
      <div className="kds-barra">
        <h1>Cozinha</h1>
        <span className={`conexao ${conectado ? 'on' : 'off'}`}>
          {conectado ? '● Tempo real' : '● Atualização periódica'}
        </span>
        <label className="toggle">
          <input type="checkbox" checked={somNovo} onChange={(e) => salvarPref('kds_som_novo', e.target.checked, setSomNovo)} />
          Som novos
        </label>
        <label className="toggle">
          <input type="checkbox" checked={somPronto} onChange={(e) => salvarPref('kds_som_pronto', e.target.checked, setSomPronto)} />
          Som prontos
        </label>
        <label className="toggle">
          <input
            type="checkbox"
            checked={mostrarFinalizados}
            onChange={(e) => salvarPref('kds_finalizados', e.target.checked, setMostrarFinalizados)}
          />
          Entregues/cancelados
        </label>
        <button className="btn btn-sm" onClick={() => beep([880])}>
          Testar som
        </button>
      </div>
      {erro && <ErrorBox erro={erro} onRetry={() => recarregar()} />}

      <div className="kds-colunas" style={{ gridTemplateColumns: `repeat(${colunas.length}, minmax(230px, 1fr))` }}>
        {colunas.map((col) => {
          const lista = (pedidos || [])
            .filter((p) => p.status === col.status)
            .sort((a, b) => (col.status === 'entregue' || col.status === 'cancelado' ? b.id - a.id : a.id - b.id));
          return (
            <section key={col.status} className={`kds-coluna col-${col.status}`}>
              <h2>
                {col.titulo} <span className="contador">{lista.length}</span>
              </h2>
              {lista.map((p) => (
                <CartaoPedido
                  key={p.id}
                  p={p}
                  agora={agora}
                  onPedido={mudarPedido}
                  onItem={mudarItem}
                  onCancelar={() => setCancelando(p)}
                  onAtraso={() => setAtrasando(p)}
                />
              ))}
            </section>
          );
        })}
      </div>

      {cancelando && (
        <ConfirmModal
          titulo={`Cancelar pedido #${cancelando.id}`}
          mensagem="Todos os itens ainda não entregues serão cancelados."
          pedirMotivo
          perigo
          textoConfirmar="Cancelar pedido"
          onClose={() => setCancelando(null)}
          onConfirm={async (motivo) => {
            await api(`/pedidos/${cancelando.id}/status`, { method: 'PATCH', body: { status: 'cancelado', motivo } });
            await recarregar(true);
          }}
        />
      )}
      {atrasando && <ModalPrevisao pedido={atrasando} onClose={() => setAtrasando(null)} onSalvo={() => recarregar(true)} />}
    </div>
  );
}

function CartaoPedido({
  p,
  agora,
  onPedido,
  onItem,
  onCancelar,
  onAtraso,
}: {
  p: Pedido;
  agora: number;
  onPedido: (p: Pedido, s: StatusPedido) => void;
  onItem: (p: Pedido, i: ItemPedido, s: StatusPedido) => void;
  onCancelar: () => void;
  onAtraso: () => void;
}) {
  const decorrido = minutosDesde(p.created_at, agora);
  const ativo = ['recebido', 'em_preparo', 'pronto'].includes(p.status);
  const classe = p.atrasado ? 'atrasado' : p.alerta_prazo ? 'alerta' : '';

  return (
    <article className={`kds-card ${classe}`}>
      <header>
        <strong className="kds-numero">#{p.id}</strong>
        <span className="kds-local">{atendimento(p)}</span>
        <span className="kds-tempo" title={`Entrada ${hora(p.created_at)}`}>
          ⏱ {duracao(decorrido)}
        </span>
      </header>
      <div className="kds-meta">
        Entrada {hora(p.created_at)}
        {p.previsao_pronto && ativo && <> · Previsão {hora(p.previsao_pronto)}</>}
        {p.iniciado_em && <> · Início {hora(p.iniciado_em)}</>}
        {p.pronto_em && <> · Pronto {hora(p.pronto_em)}</>}
      </div>
      {p.atrasado && (
        <div className="kds-atraso">
          Atrasado {duracao(p.minutos_atraso)}
          {p.motivo_atraso && ` · ${p.motivo_atraso}`}
        </div>
      )}
      {!p.atrasado && p.alerta_prazo && <div className="kds-alerta">Perto do prazo</div>}
      {p.observacao && <div className="kds-obs">📝 {p.observacao}</div>}
      {p.motivo_cancelamento && <div className="kds-obs">Motivo: {p.motivo_cancelamento}</div>}

      <ul className="kds-itens">
        {p.itens.map((i) => {
          const prox = PROXIMO_ITEM[i.status];
          return (
            <li key={i.id} className={`item-${i.status} ${i.atrasado ? 'item-atrasado' : ''}`}>
              <button
                className="kds-item-btn"
                disabled={!prox || !ativo || (prox === 'entregue' && p.status !== 'pronto')}
                onClick={() => prox && onItem(p, i, prox)}
                title={prox ? `Marcar como ${prox.replace('_', ' ')}` : ''}
              >
                <span className="kds-qtd">{i.quantidade}×</span>
                <span className="kds-nome">
                  {i.nome_produto}
                  {i.observacao && <em>{i.observacao}</em>}
                </span>
                <Badge status={i.status} />
              </button>
            </li>
          );
        })}
      </ul>

      {ativo && (
        <div className="kds-acoes">
          {p.status === 'recebido' && (
            <button className="btn btn-primario btn-grande" onClick={() => onPedido(p, 'em_preparo')}>
              Iniciar preparo
            </button>
          )}
          {(p.status === 'recebido' || p.status === 'em_preparo') && (
            <button className="btn btn-ok btn-grande" onClick={() => onPedido(p, 'pronto')}>
              Tudo pronto
            </button>
          )}
          {p.status === 'pronto' && (
            <button className="btn btn-ok btn-grande" onClick={() => onPedido(p, 'entregue')}>
              Entregue
            </button>
          )}
          <div className="kds-acoes-sec">
            {p.status !== 'pronto' && (
              <button className="btn btn-sm" onClick={onAtraso}>
                Previsão
              </button>
            )}
            <button className="btn btn-sm btn-perigo-sutil" onClick={onCancelar}>
              Cancelar
            </button>
          </div>
        </div>
      )}
    </article>
  );
}

function ModalPrevisao({ pedido, onClose, onSalvo }: { pedido: Pedido; onClose: () => void; onSalvo: () => void }) {
  const [minutos, setMinutos] = useState(10);
  const [motivo, setMotivo] = useState(pedido.motivo_atraso || '');
  return (
    <ConfirmModal
      titulo={`Nova previsão · pedido #${pedido.id}`}
      mensagem={
        <div className="form">
          <p className="muted">Previsão atual: {hora(pedido.previsao_pronto)}. O cliente verá a nova previsão.</p>
          <div className="chips">
            {[5, 10, 15, 20, 30].map((m) => (
              <button type="button" key={m} className={`chip ${minutos === m ? 'ativo' : ''}`} onClick={() => setMinutos(m)}>
                +{m} min
              </button>
            ))}
          </div>
          <label>
            Motivo do atraso (opcional)
            <input value={motivo} onChange={(e) => setMotivo(e.target.value)} maxLength={300} />
          </label>
        </div>
      }
      textoConfirmar={`Adiar ${minutos} min`}
      onClose={onClose}
      onConfirm={async () => {
        await api(`/pedidos/${pedido.id}/previsao`, {
          method: 'PATCH',
          body: { minutos_adicionais: minutos, motivo_atraso: motivo || undefined },
        });
        onSalvo();
      }}
    />
  );
}
