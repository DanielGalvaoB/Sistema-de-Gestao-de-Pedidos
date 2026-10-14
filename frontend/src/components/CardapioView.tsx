import { ChefHat, ImageOff, Info, Minus, Plus, Send, ShoppingCart, Trash2, X } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { api, imgUrl } from '../api/client';
import type { CardapioPublico, Produto } from '../api/types';
import { money } from '../utils/format';
import { ErrorBox } from './ui';

type ItemCarrinho = { produto: Produto; quantidade: number; observacao: string };

const CHAVE_ULTIMO = (slug: string) => `pdv:ultimo-pedido:${slug}`;

/** Codigo do ultimo pedido feito neste navegador para o estabelecimento. */
export function lerUltimoPedido(slug: string): string | null {
  try {
    return localStorage.getItem(CHAVE_ULTIMO(slug));
  } catch {
    return null;
  }
}

export function salvarUltimoPedido(slug: string, codigo: string | null) {
  try {
    if (codigo) localStorage.setItem(CHAVE_ULTIMO(slug), codigo);
    else localStorage.removeItem(CHAVE_ULTIMO(slug));
  } catch {
    /* armazenamento indisponivel */
  }
}

/**
 * Cardapio com carrinho. Com `codigoOrigem`, o pedido entra na mesma conta
 * do pedido anterior (mesma pessoa ou mesa).
 */
export default function CardapioView({
  slug,
  cardapio,
  mesaToken,
  codigoOrigem,
  onEnviado,
}: {
  slug: string;
  cardapio: CardapioPublico;
  mesaToken?: string | null;
  codigoOrigem?: string | null;
  onEnviado: (codigo: string, numero: number) => void;
}) {
  const chaveCarrinho = `carrinho:${slug}:${mesaToken || codigoOrigem || 'geral'}`;
  const [carrinho, setCarrinho] = useState<ItemCarrinho[]>(() => {
    try {
      return JSON.parse(sessionStorage.getItem(chaveCarrinho) || '[]');
    } catch {
      return [];
    }
  });
  const [verCarrinho, setVerCarrinho] = useState(false);
  const [categoriaAtiva, setCategoriaAtiva] = useState<number | null>(null);
  const [tipo, setTipo] = useState<'balcao' | 'retirada'>('balcao');
  const [nome, setNome] = useState('');
  const [observacao, setObservacao] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [erroEnvio, setErroEnvio] = useState<string | null>(null);
  const mesmaConta = !!codigoOrigem;
  const pedirDados = !mesaToken && !mesmaConta;

  useEffect(() => {
    try {
      sessionStorage.setItem(chaveCarrinho, JSON.stringify(carrinho));
    } catch {
      /* ignora */
    }
  }, [carrinho, chaveCarrinho]);

  const total = useMemo(() => carrinho.reduce((s, i) => s + Number(i.produto.preco) * i.quantidade, 0), [carrinho]);
  const qtdItens = carrinho.reduce((s, i) => s + i.quantidade, 0);

  const alterarQtd = (produto: Produto, delta: number) => {
    setCarrinho((c) => {
      const existe = c.find((i) => i.produto.id === produto.id);
      if (!existe) return delta > 0 ? [...c, { produto, quantidade: 1, observacao: '' }] : c;
      return c
        .map((i) => (i.produto.id === produto.id ? { ...i, quantidade: i.quantidade + delta } : i))
        .filter((i) => i.quantidade > 0);
    });
  };

  const enviar = async () => {
    setEnviando(true);
    setErroEnvio(null);
    try {
      const res = await api<{ numero: number; codigo_acompanhamento: string }>(`/public/${slug}/pedidos`, {
        auth: false,
        body: {
          mesa_token: mesaToken || undefined,
          codigo_origem: codigoOrigem || undefined,
          tipo: mesaToken ? 'mesa' : tipo,
          cliente_nome: pedirDados ? nome || undefined : undefined,
          observacao: observacao || undefined,
          // Apenas produto, quantidade e observacao: o preco vem do servidor
          itens: carrinho.map((i) => ({
            id_menu: i.produto.id,
            quantidade: i.quantidade,
            observacao: i.observacao || undefined,
          })),
        },
      });
      setCarrinho([]);
      setVerCarrinho(false);
      setObservacao('');
      salvarUltimoPedido(slug, res.codigo_acompanhamento);
      onEnviado(res.codigo_acompanhamento, res.numero);
    } catch (e) {
      setErroEnvio((e as Error).message);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <>
      {mesmaConta && (
        <div className="alert alert-info">
          <Info size={18} />
          <span>Os itens que você pedir agora entram na mesma conta dos seus pedidos anteriores.</span>
        </div>
      )}

      <nav className="chips" aria-label="Categorias">
        {cardapio.categorias.map((c) => (
          <a
            key={c.id}
            href={`#cat-${c.id}`}
            className={`chip ${categoriaAtiva === c.id ? 'ativo' : ''}`}
            onClick={() => setCategoriaAtiva(c.id)}
          >
            {c.nome}
          </a>
        ))}
      </nav>

      {cardapio.categorias.length === 0 && <p className="empty">Nenhum produto disponível no momento.</p>}

      {cardapio.categorias.map((c) => (
        <section key={c.id} id={`cat-${c.id}`} className="cardapio-secao">
          <h2>{c.nome}</h2>
          <div className="produtos-grid">
            {c.produtos.map((p) => {
              const noCarrinho = carrinho.find((i) => i.produto.id === p.id)?.quantidade || 0;
              return (
                <article key={p.id} className={`produto-card ${p.is_disponivel ? '' : 'indisponivel'}`}>
                  {p.url_imagem ? (
                    <img src={imgUrl(p.url_imagem) || ''} alt={p.nome} loading="lazy" />
                  ) : (
                    <div className="produto-sem-imagem" aria-hidden>
                      {p.is_disponivel ? <ChefHat size={28} strokeWidth={1.5} /> : <ImageOff size={28} strokeWidth={1.5} />}
                    </div>
                  )}
                  <div className="produto-info">
                    <h3>{p.nome}</h3>
                    {p.descricao && <p>{p.descricao}</p>}
                    <div className="produto-rodape">
                      <strong>{money(p.preco)}</strong>
                      {!p.is_disponivel ? (
                        <span className="badge badge-cancelado">Indisponível</span>
                      ) : noCarrinho ? (
                        <div className="qtd">
                          <button onClick={() => alterarQtd(p, -1)} aria-label="Diminuir">
                            <Minus size={16} />
                          </button>
                          <span>{noCarrinho}</span>
                          <button onClick={() => alterarQtd(p, 1)} aria-label="Aumentar">
                            <Plus size={16} />
                          </button>
                        </div>
                      ) : (
                        <button className="btn btn-primario btn-sm" onClick={() => alterarQtd(p, 1)}>
                          <Plus size={14} /> Adicionar
                        </button>
                      )}
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        </section>
      ))}

      {qtdItens > 0 && !verCarrinho && (
        <button className="carrinho-barra" onClick={() => setVerCarrinho(true)}>
          <span className="com-icone">
            <ShoppingCart size={18} /> {qtdItens} {qtdItens === 1 ? 'item' : 'itens'}
          </span>
          <strong>Ver carrinho · {money(total)}</strong>
        </button>
      )}

      {verCarrinho && (
        <div className="carrinho-painel" role="dialog" aria-label="Carrinho">
          <div className="carrinho-topo">
            <h2 className="com-icone">
              <ShoppingCart size={20} /> {mesmaConta ? 'Novo pedido' : 'Seu pedido'}
            </h2>
            <button className="btn-icon" onClick={() => setVerCarrinho(false)} aria-label="Fechar">
              <X size={22} />
            </button>
          </div>
          {carrinho.length === 0 && <p className="empty">Carrinho vazio.</p>}
          {carrinho.map((i) => (
            <div key={i.produto.id} className="carrinho-item">
              <div className="carrinho-linha">
                <div>
                  <strong>{i.produto.nome}</strong>
                  <div className="muted">
                    {money(i.produto.preco)} x {i.quantidade} = {money(Number(i.produto.preco) * i.quantidade)}
                  </div>
                </div>
                <div className="qtd">
                  <button onClick={() => alterarQtd(i.produto, -1)} aria-label="Diminuir">
                    <Minus size={16} />
                  </button>
                  <span>{i.quantidade}</span>
                  <button onClick={() => alterarQtd(i.produto, 1)} aria-label="Aumentar">
                    <Plus size={16} />
                  </button>
                </div>
              </div>
              <input
                placeholder="Observação (ex.: sem cebola)"
                value={i.observacao}
                maxLength={300}
                onChange={(e) =>
                  setCarrinho((c) => c.map((x) => (x.produto.id === i.produto.id ? { ...x, observacao: e.target.value } : x)))
                }
              />
              <button
                className="link-perigo com-icone"
                onClick={() => setCarrinho((c) => c.filter((x) => x.produto.id !== i.produto.id))}
              >
                <Trash2 size={14} /> Remover
              </button>
            </div>
          ))}

          {carrinho.length > 0 && (
            <div className="form">
              {pedirDados && (
                <div className="segmentado">
                  <button className={tipo === 'balcao' ? 'ativo' : ''} onClick={() => setTipo('balcao')}>
                    Consumir no local
                  </button>
                  <button className={tipo === 'retirada' ? 'ativo' : ''} onClick={() => setTipo('retirada')}>
                    Retirada
                  </button>
                </div>
              )}
              {pedirDados && (
                <label>
                  Seu nome (para chamarmos você)
                  <input value={nome} onChange={(e) => setNome(e.target.value)} maxLength={80} />
                </label>
              )}
              <label>
                Observações do pedido
                <textarea value={observacao} onChange={(e) => setObservacao(e.target.value)} maxLength={500} />
              </label>
              <div className="carrinho-total">
                <span>Total estimado</span>
                <strong>{money(total)}</strong>
              </div>
              <p className="muted small">O valor final é confirmado pelo estabelecimento.</p>
              {erroEnvio && <ErrorBox erro={erroEnvio} />}
              <button className="btn btn-primario btn-grande" disabled={enviando} onClick={enviar}>
                <Send size={18} /> {enviando ? 'Enviando...' : 'Enviar pedido para a cozinha'}
              </button>
            </div>
          )}
        </div>
      )}
    </>
  );
}
