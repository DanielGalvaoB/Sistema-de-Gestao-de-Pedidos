import { AlertCircle, CheckCircle2, Inbox, Loader2, RotateCw, X, type LucideIcon } from 'lucide-react';
import { createContext, useCallback, useContext, useState, type FormEvent, type ReactNode } from 'react';
import { STATUS_LABEL } from '../utils/format';

/* ---------- Toasts ---------- */
type Toast = { id: number; texto: string; tipo: 'ok' | 'erro' };
const ToastCtx = createContext<(texto: string, tipo?: 'ok' | 'erro') => void>(() => {});

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const mostrar = useCallback((texto: string, tipo: 'ok' | 'erro' = 'ok') => {
    const id = Date.now() + Math.random();
    setToasts((t) => [...t, { id, texto, tipo }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), tipo === 'erro' ? 6000 : 3000);
  }, []);
  return (
    <ToastCtx.Provider value={mostrar}>
      {children}
      <div className="toasts" role="status" aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id} className={`toast toast-${t.tipo}`}>
            {t.tipo === 'ok' ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
            <span>{t.texto}</span>
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}

export const useToast = () => useContext(ToastCtx);

/* ---------- Estados ---------- */
export function Loading({ texto = 'Carregando...' }: { texto?: string }) {
  return (
    <div className="loading">
      <Loader2 className="girar" size={20} /> {texto}
    </div>
  );
}

export function ErrorBox({ erro, onRetry }: { erro: string; onRetry?: () => void }) {
  return (
    <div className="alert alert-erro">
      <AlertCircle size={18} className="alert-icone" />
      <span className="alert-texto">{erro}</span>
      {onRetry && (
        <button className="btn btn-sm" onClick={onRetry}>
          <RotateCw size={14} /> Tentar novamente
        </button>
      )}
    </div>
  );
}

export function Empty({ children, icone: Icone = Inbox }: { children: ReactNode; icone?: LucideIcon }) {
  return (
    <div className="empty">
      <Icone size={32} strokeWidth={1.5} />
      <div>{children}</div>
    </div>
  );
}

export function Badge({ status, children }: { status: string; children?: ReactNode }) {
  return <span className={`badge badge-${status}`}>{children ?? STATUS_LABEL[status] ?? status}</span>;
}

/* ---------- Modal ---------- */
export function Modal({
  titulo,
  onClose,
  children,
  largo,
}: {
  titulo: string;
  onClose: () => void;
  children: ReactNode;
  largo?: boolean;
}) {
  return (
    <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className={`modal ${largo ? 'modal-largo' : ''}`} role="dialog" aria-modal aria-label={titulo}>
        <div className="modal-header">
          <h2>{titulo}</h2>
          <button className="btn-icon" onClick={onClose} aria-label="Fechar">
            <X size={20} />
          </button>
        </div>
        <div className="modal-body">{children}</div>
      </div>
    </div>
  );
}

/** Confirmacao para operacoes criticas, opcionalmente pedindo um motivo. */
export function ConfirmModal({
  titulo,
  mensagem,
  pedirMotivo,
  textoConfirmar = 'Confirmar',
  perigo,
  onConfirm,
  onClose,
}: {
  titulo: string;
  mensagem: ReactNode;
  pedirMotivo?: boolean;
  textoConfirmar?: string;
  perigo?: boolean;
  onConfirm: (motivo: string) => Promise<void> | void;
  onClose: () => void;
}) {
  const [motivo, setMotivo] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setEnviando(true);
    setErro(null);
    try {
      await onConfirm(motivo.trim());
      onClose();
    } catch (err) {
      setErro((err as Error).message);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <Modal titulo={titulo} onClose={onClose}>
      <form onSubmit={submit} className="form">
        <div>{mensagem}</div>
        {pedirMotivo && (
          <label>
            Motivo
            <input value={motivo} onChange={(e) => setMotivo(e.target.value)} required minLength={3} autoFocus />
          </label>
        )}
        {erro && <ErrorBox erro={erro} />}
        <div className="form-actions">
          <button type="button" className="btn" onClick={onClose}>
            Voltar
          </button>
          <button className={`btn ${perigo ? 'btn-perigo' : 'btn-primario'}`} disabled={enviando}>
            {enviando ? 'Enviando...' : textoConfirmar}
          </button>
        </div>
      </form>
    </Modal>
  );
}

export function Stat({
  rotulo,
  valor,
  destaque,
  icone: Icone,
}: {
  rotulo: string;
  valor: ReactNode;
  destaque?: 'ok' | 'erro' | 'info' | 'aviso';
  icone?: LucideIcon;
}) {
  return (
    <div className={`stat ${destaque ? `stat-${destaque}` : ''}`}>
      {Icone && (
        <span className="stat-icone">
          <Icone size={20} strokeWidth={1.75} />
        </span>
      )}
      <div className="stat-corpo">
        <span className="stat-rotulo">{rotulo}</span>
        <span className="stat-valor">{valor}</span>
      </div>
    </div>
  );
}

export function PageHeader({
  titulo,
  subtitulo,
  icone: Icone,
  children,
}: {
  titulo: ReactNode;
  subtitulo?: ReactNode;
  icone?: LucideIcon;
  children?: ReactNode;
}) {
  return (
    <div className="pagina-topo">
      <div className="pagina-titulo">
        {Icone && (
          <span className="pagina-icone">
            <Icone size={22} strokeWidth={1.75} />
          </span>
        )}
        <div>
          <h1>{titulo}</h1>
          {subtitulo && <p className="muted small">{subtitulo}</p>}
        </div>
      </div>
      {children && <div className="acoes">{children}</div>}
    </div>
  );
}
