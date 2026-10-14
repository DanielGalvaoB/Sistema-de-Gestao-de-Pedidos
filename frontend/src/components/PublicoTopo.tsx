import { Armchair, BookOpen, ReceiptText, ShoppingBag, Store } from 'lucide-react';

export type AbaPublica = 'cardapio' | 'pedidos';

/** Cabecalho das paginas publicas com as abas Cardapio / Meus pedidos. */
export default function PublicoTopo({
  nomeLoja,
  mesaNumero,
  subtitulo,
  aba,
  qtdPedidos,
  onAba,
}: {
  nomeLoja: string;
  mesaNumero?: string | null;
  subtitulo?: string;
  aba: AbaPublica;
  qtdPedidos?: number;
  onAba?: (aba: AbaPublica) => void;
}) {
  return (
    <>
      <header className="publico-header publico-hero">
        <span className="marca-logo grande">
          <Store size={26} />
        </span>
        <div>
          <h1>{nomeLoja}</h1>
          <p className="com-icone">
            {mesaNumero ? <Armchair size={16} /> : <ShoppingBag size={16} />}
            {subtitulo || (mesaNumero ? `Mesa ${mesaNumero}` : 'Pedido no balcão ou para retirada')}
          </p>
        </div>
      </header>
      {onAba && (
        <div className="abas-publicas" role="tablist">
          <button role="tab" aria-selected={aba === 'cardapio'} className={aba === 'cardapio' ? 'ativo' : ''} onClick={() => onAba('cardapio')}>
            <BookOpen size={18} /> Cardápio
          </button>
          <button role="tab" aria-selected={aba === 'pedidos'} className={aba === 'pedidos' ? 'ativo' : ''} onClick={() => onAba('pedidos')}>
            <ReceiptText size={18} /> Meus pedidos
            {!!qtdPedidos && <span className="abas-contador">{qtdPedidos}</span>}
          </button>
        </div>
      )}
    </>
  );
}
