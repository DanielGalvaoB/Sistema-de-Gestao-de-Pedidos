import { Banknote, CircleCheck, CreditCard, Landmark, QrCode, Wallet, type LucideIcon } from 'lucide-react';
import { useRef, useState, type FormEvent } from 'react';
import { api, novaChave } from '../api/client';
import type { Pedido } from '../api/types';
import { atendimento, money } from '../utils/format';
import { ErrorBox, Modal, useToast } from './ui';

export const METODOS: { valor: string; label: string; icone: LucideIcon }[] = [
  { valor: 'dinheiro', label: 'Dinheiro', icone: Banknote },
  { valor: 'cartao_credito', label: 'Crédito', icone: CreditCard },
  { valor: 'cartao_debito', label: 'Débito', icone: Landmark },
  { valor: 'pix', label: 'PIX', icone: QrCode },
  { valor: 'outro', label: 'Outro', icone: Wallet },
];

function numero(v: string): number {
  return Number(v.replace(',', '.'));
}

/** Confirmacao manual do pagamento de um pedido pronto/entregue. */
export function ModalPagamentoPedido({
  pedido,
  onClose,
  onPago,
}: {
  pedido: Pedido;
  onClose: () => void;
  onPago: (p: Pedido) => void;
}) {
  const toast = useToast();
  const saldo = Number(pedido.saldo);
  const [metodo, setMetodo] = useState<string | null>(null);
  const [valor, setValor] = useState(saldo.toFixed(2));
  const [recebido, setRecebido] = useState('');
  const [obs, setObs] = useState('');
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  // Mesma chave em reenvios: cliques repetidos nao duplicam o pagamento
  const chave = useRef(novaChave());

  const valorNum = numero(valor);
  const troco = metodo === 'dinheiro' && recebido ? numero(recebido) - valorNum : 0;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!metodo) return setErro('Selecione a forma de pagamento');
    if (!Number.isFinite(valorNum) || valorNum <= 0) return setErro('Valor inválido');
    if (metodo === 'dinheiro' && recebido && troco < 0) return setErro('Valor recebido menor que o valor a pagar');
    setEnviando(true);
    setErro(null);
    try {
      const atualizado = await api<Pedido>(`/pedidos/${pedido.id}/pagamentos`, {
        body: {
          metodo,
          valor: valorNum.toFixed(2),
          chave_idempotencia: chave.current,
          observacao: obs || undefined,
        },
      });
      toast(atualizado.pago ? `Pedido #${pedido.id} pago` : 'Pagamento parcial registrado');
      onPago(atualizado);
      onClose();
    } catch (err) {
      setErro((err as Error).message);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <Modal titulo={`Confirmar pagamento · pedido #${pedido.id}`} onClose={onClose}>
      <form className="form" onSubmit={submit}>
        <div className="resumo-pedido">
          <div className="resumo-pedido-topo">
            <span>{atendimento(pedido)}</span>
            <strong>{money(pedido.total)}</strong>
          </div>
          <ul>
            {pedido.itens
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
          {Number(pedido.total_pago) > 0 && (
            <div className="resumo-pedido-pago">
              Já pago: {money(pedido.total_pago)} · Restante: <strong>{money(pedido.saldo)}</strong>
            </div>
          )}
        </div>

        <fieldset className="metodos">
          <legend>Forma de pagamento</legend>
          <div className="metodos-grid">
            {METODOS.map(({ valor: v, label, icone: Icone }) => (
              <button
                type="button"
                key={v}
                className={`metodo ${metodo === v ? 'ativo' : ''}`}
                aria-pressed={metodo === v}
                onClick={() => setMetodo(v)}
              >
                <Icone size={22} strokeWidth={1.75} />
                <span>{label}</span>
              </button>
            ))}
          </div>
        </fieldset>

        <div className="grid-2">
          <label>
            Valor pago (R$)
            <input inputMode="decimal" value={valor} onChange={(e) => setValor(e.target.value)} required />
          </label>
          {metodo === 'dinheiro' && (
            <label>
              Valor recebido (R$)
              <input
                inputMode="decimal"
                value={recebido}
                onChange={(e) => setRecebido(e.target.value)}
                placeholder="Para calcular o troco"
              />
            </label>
          )}
        </div>
        {troco > 0 && (
          <div className="troco">
            Troco <strong>{money(troco)}</strong>
          </div>
        )}
        {valorNum > 0 && valorNum < saldo && (
          <p className="muted small">Pagamento parcial: restarão {money(saldo - valorNum)} neste pedido.</p>
        )}
        {metodo === 'pix' && (
          <div className="alert alert-aviso small">
            Confira o recebimento no app do banco antes de confirmar. Não há confirmação automática do PIX.
          </div>
        )}
        <label>
          Observação
          <input value={obs} onChange={(e) => setObs(e.target.value)} maxLength={300} placeholder="Opcional" />
        </label>
        {erro && <ErrorBox erro={erro} />}
        <div className="form-actions">
          <button type="button" className="btn" onClick={onClose}>
            Cancelar
          </button>
          <button className="btn btn-ok btn-lg" disabled={enviando || !metodo}>
            <CircleCheck size={18} />
            {enviando ? 'Confirmando...' : `Confirmar ${money(valorNum || 0)}`}
          </button>
        </div>
      </form>
    </Modal>
  );
}
