import { QRCodeSVG } from 'qrcode.react';
import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../api/client';
import type { Mesa } from '../../api/types';
import { useAuth } from '../../auth/AuthContext';
import { Badge, ConfirmModal, Empty, ErrorBox, Loading, Modal, useToast } from '../../components/ui';
import { useAgora, useAsync } from '../../hooks/useAsync';
import { useRealtime } from '../../hooks/useRealtime';
import { duracao, minutosDesde, money } from '../../utils/format';

export default function Mesas() {
  const { pode } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();
  const agora = useAgora(30000);
  const [incluirInativas, setIncluirInativas] = useState(false);
  const { data: mesas, erro, carregando, recarregar } = useAsync(
    () => api<Mesa[]>('/mesas/', { query: { incluir_inativas: incluirInativas } }),
    [incluirInativas],
  );
  useRealtime(() => recarregar(true), 15000);
  const [editando, setEditando] = useState<Mesa | 'nova' | null>(null);
  const [qr, setQr] = useState<{ url: string; descricao: string } | null>(null);
  const [regenerar, setRegenerar] = useState<Mesa | null>(null);

  const abrirConta = async (m: Mesa) => {
    if (m.id_sessao) return navigate(`/admin/contas/${m.id_sessao}`);
    try {
      const conta = await api<{ id: number }>('/contas/', { body: { id_mesa: m.id, tipo: 'mesa' } });
      navigate(`/admin/contas/${conta.id}`);
    } catch (e) {
      toast((e as Error).message, 'erro');
    }
  };

  const verQr = async (m: Mesa) => {
    try {
      setQr(await api(`/mesas/${m.id}/qrcode`));
    } catch (e) {
      toast((e as Error).message, 'erro');
    }
  };

  if (carregando && !mesas) return <Loading />;

  return (
    <div>
      <div className="pagina-topo">
        <h1>Mesas e contas</h1>
        <div className="acoes">
          <label className="toggle">
            <input type="checkbox" checked={incluirInativas} onChange={(e) => setIncluirInativas(e.target.checked)} />
            Mostrar desativadas
          </label>
          {pode() && (
            <button className="btn btn-primario" onClick={() => setEditando('nova')}>
              + Nova mesa
            </button>
          )}
        </div>
      </div>
      {erro && <ErrorBox erro={erro} onRetry={() => recarregar()} />}
      {mesas?.length === 0 && <Empty>Nenhuma mesa cadastrada.</Empty>}

      <div className="legenda">
        <Badge status="livre" /> <Badge status="ocupada" /> <Badge status="aguardando_pagamento" />
      </div>

      <div className="mesas-grid">
        {mesas?.map((m) => (
          <div key={m.id} className={`mesa-card mesa-${m.ativo ? m.situacao : 'inativa'}`}>
            <button className="mesa-principal" onClick={() => m.ativo && abrirConta(m)} disabled={!m.ativo}>
              <span className="mesa-numero">Mesa {m.numero}</span>
              {m.ativo ? <Badge status={m.situacao} /> : <Badge status="cancelado">Desativada</Badge>}
              {m.id_sessao && (
                <span className="mesa-info">
                  {money(m.total_consumido)} · {duracao(minutosDesde(m.aberta_em, agora))}
                </span>
              )}
              {!m.id_sessao && m.ativo && <span className="mesa-info muted">Toque para abrir conta</span>}
            </button>
            <div className="mesa-acoes">
              <button className="btn btn-sm" onClick={() => verQr(m)}>
                QR Code
              </button>
              {pode() && (
                <button className="btn btn-sm" onClick={() => setEditando(m)}>
                  Editar
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {editando && (
        <ModalMesa
          mesa={editando === 'nova' ? null : editando}
          onClose={() => setEditando(null)}
          onRegenerar={(m) => {
            setEditando(null);
            setRegenerar(m);
          }}
          onSalvo={() => {
            setEditando(null);
            recarregar(true);
          }}
        />
      )}
      {qr && <ModalQr {...qr} onClose={() => setQr(null)} />}
      {regenerar && (
        <ConfirmModal
          titulo={`Gerar novo QR Code · mesa ${regenerar.numero}`}
          mensagem="O QR Code impresso atual deixará de funcionar. Imprima o novo em seguida."
          perigo
          onClose={() => setRegenerar(null)}
          onConfirm={async () => {
            await api(`/mesas/${regenerar.id}/regenerar-token`, { method: 'POST' });
            toast('Novo QR Code gerado');
            recarregar(true);
          }}
        />
      )}
    </div>
  );
}

function ModalMesa({
  mesa,
  onClose,
  onSalvo,
  onRegenerar,
}: {
  mesa: Mesa | null;
  onClose: () => void;
  onSalvo: () => void;
  onRegenerar: (m: Mesa) => void;
}) {
  const toast = useToast();
  const [numero, setNumero] = useState(mesa?.numero || '');
  const [capacidade, setCapacidade] = useState(mesa?.capacidade?.toString() || '');
  const [ativo, setAtivo] = useState(mesa?.ativo ?? true);
  const [erro, setErro] = useState<string | null>(null);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const body = { numero, capacidade: capacidade ? Number(capacidade) : null, ...(mesa ? { ativo } : {}) };
    try {
      if (mesa) await api(`/mesas/${mesa.id}`, { method: 'PATCH', body });
      else await api('/mesas/', { body });
      toast('Mesa salva');
      onSalvo();
    } catch (err) {
      setErro((err as Error).message);
    }
  };

  return (
    <Modal titulo={mesa ? `Editar mesa ${mesa.numero}` : 'Nova mesa'} onClose={onClose}>
      <form className="form" onSubmit={submit}>
        <label>
          Número / identificação
          <input value={numero} onChange={(e) => setNumero(e.target.value)} required maxLength={20} autoFocus />
        </label>
        <label>
          Capacidade (pessoas)
          <input type="number" min={1} max={100} value={capacidade} onChange={(e) => setCapacidade(e.target.value)} />
        </label>
        {mesa && (
          <label className="toggle">
            <input type="checkbox" checked={ativo} onChange={(e) => setAtivo(e.target.checked)} /> Mesa ativa
          </label>
        )}
        {erro && <ErrorBox erro={erro} />}
        <div className="form-actions">
          {mesa && (
            <button type="button" className="btn btn-perigo-sutil" onClick={() => onRegenerar(mesa)}>
              Gerar novo QR
            </button>
          )}
          <button className="btn btn-primario">Salvar</button>
        </div>
      </form>
    </Modal>
  );
}

export function ModalQr({ url, descricao, onClose }: { url: string; descricao: string; onClose: () => void }) {
  return (
    <Modal titulo={`QR Code do cardápio · ${descricao}`} onClose={onClose}>
      <div className="qr-box imprimivel">
        <QRCodeSVG value={url} size={240} includeMargin />
        <strong>{descricao}</strong>
        <span className="small">Aponte a câmera para ver o cardápio e fazer o pedido</span>
        <code className="small quebra">{url}</code>
      </div>
      <div className="form-actions">
        <button className="btn" onClick={() => navigator.clipboard?.writeText(url)}>
          Copiar link
        </button>
        <button className="btn btn-primario" onClick={() => window.print()}>
          Imprimir
        </button>
      </div>
    </Modal>
  );
}
