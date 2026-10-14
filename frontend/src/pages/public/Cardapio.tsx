import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { api } from '../../api/client';
import type { CardapioPublico, Produto } from '../../api/types';
import { ErrorBox, Loading } from '../../components/ui';
import { useAsync } from '../../hooks/useAsync';
import { money } from '../../utils/format';

type ItemCarrinho = { produto: Produto; quantidade: number; observacao: string };

export default function Cardapio() {
  const { slug = '' } = useParams();
  const [sp] = useSearchParams();
  const mesaToken = sp.get('mesa');
  const navigate = useNavigate();
  const chaveCarrinho = `carrinho:${slug}:${mesaToken || 'geral'}`;

  const { data, erro, carregando, recarregar } = useAsync(
    () => api<CardapioPublico>(`/public/${slug}`, { query: { mesa: mesaToken }, auth: false }),
    [slug, mesaToken],
  );

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

  useEffect(() => {
    try {
      sessionStorage.setItem(chaveCarrinho, JSON.stringify(carrinho));
    } catch {
      /* ignora */
    }
  }, [carrinho, chaveCarrinho]);

  const total = useMemo(
    () => carrinho.reduce((s, i) => s + Number(i.produto.preco) * i.quantidade, 0),
    [carrinho],
  );
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
          tipo: mesaToken ? 'mesa' : tipo,
          cliente_nome: nome || undefined,
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
      navigate(`/pedido/${res.codigo_acompanhamento}`);
    } catch (e) {
      setErroEnvio((e as Error).message);
      recarregar(true);
    } finally {
      setEnviando(false);
    }
  };

  if (carregando) return <Loading texto="Carregando cardápio..." />;
  if (erro || !data)
    return (
      <div className="publico">
        <ErrorBox erro={erro || 'Cardápio indisponível'} onRetry={() => recarregar()} />
      </div>
    );

  return (
    <div className="publico">
      <header className="publico-header">
        <h1>{data.estabelecimento.nome_loja}</h1>
        <p>{data.mesa_numero ? `Mesa ${data.mesa_numero}` : 'Pedido no balcão / retirada'}</p>
      </header>

      <nav className="chips" aria-label="Categorias">
        {data.categorias.map((c) => (
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

      {data.categorias.length === 0 && <p className="empty">Nenhum produto disponível no momento.</p>}

      {data.categorias.map((c) => (
        <section key={c.id} id={`cat-${c.id}`} className="cardapio-secao">
          <h2>{c.nome}</h2>
          <div className="produtos-grid">
            {c.produtos.map((p) => {
              const noCarrinho = carrinho.find((i) => i.produto.id === p.id)?.quantidade || 0;
              return (
                <article key={p.id} className={`produto-card ${p.is_disponivel ? '' : 'indisponivel'}`}>
                  {p.url_imagem && <img src={p.url_imagem} alt={p.nome} loading="lazy" />}
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
                            −
                          </button>
                          <span>{noCarrinho}</span>
                          <button onClick={() => alterarQtd(p, 1)} aria-label="Aumentar">
                            +
                          </button>
                        </div>
                      ) : (
                        <button className="btn btn-primario btn-sm" onClick={() => alterarQtd(p, 1)}>
                          Adicionar
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
          <span>
            🛒 {qtdItens} {qtdItens === 1 ? 'item' : 'itens'}
          </span>
          <strong>Ver carrinho · {money(total)}</strong>
        </button>
      )}

      {verCarrinho && (
        <div className="carrinho-painel" role="dialog" aria-label="Carrinho">
          <div className="carrinho-topo">
            <h2>Seu pedido</h2>
            <button className="btn-icon" onClick={() => setVerCarrinho(false)} aria-label="Fechar">
              ✕
            </button>
          </div>
          {carrinho.length === 0 && <p className="empty">Carrinho vazio.</p>}
          {carrinho.map((i) => (
            <div key={i.produto.id} className="carrinho-item">
              <div className="carrinho-linha">
                <div>
                  <strong>{i.produto.nome}</strong>
                  <div className="muted">
                    {money(i.produto.preco)} × {i.quantidade} = {money(Number(i.produto.preco) * i.quantidade)}
                  </div>
                </div>
                <div className="qtd">
                  <button onClick={() => alterarQtd(i.produto, -1)} aria-label="Diminuir">
                    −
                  </button>
                  <span>{i.quantidade}</span>
                  <button onClick={() => alterarQtd(i.produto, 1)} aria-label="Aumentar">
                    +
                  </button>
                </div>
              </div>
              <input
                placeholder="Observação (ex.: sem cebola)"
                value={i.observacao}
                maxLength={300}
                onChange={(e) =>
                  setCarrinho((c) =>
                    c.map((x) => (x.produto.id === i.produto.id ? { ...x, observacao: e.target.value } : x)),
                  )
                }
              />
              <button
                className="link-perigo"
                onClick={() => setCarrinho((c) => c.filter((x) => x.produto.id !== i.produto.id))}
              >
                Remover
              </button>
            </div>
          ))}

          {carrinho.length > 0 && (
            <div className="form">
              {!mesaToken && (
                <div className="segmentado">
                  <button className={tipo === 'balcao' ? 'ativo' : ''} onClick={() => setTipo('balcao')}>
                    Consumir no local
                  </button>
                  <button className={tipo === 'retirada' ? 'ativo' : ''} onClick={() => setTipo('retirada')}>
                    Retirada
                  </button>
                </div>
              )}
              {!mesaToken && (
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
                {enviando ? 'Enviando...' : 'Enviar pedido para a cozinha'}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
