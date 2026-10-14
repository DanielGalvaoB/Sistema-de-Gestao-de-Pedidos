import { useState, type FormEvent } from 'react';
import { api } from '../../api/client';
import type { Categoria, Produto } from '../../api/types';
import { Badge, ConfirmModal, Empty, ErrorBox, Loading, Modal, useToast } from '../../components/ui';
import { useAsync } from '../../hooks/useAsync';
import { dataHora, money } from '../../utils/format';

export default function Produtos() {
  const toast = useToast();
  const [busca, setBusca] = useState('');
  const [catFiltro, setCatFiltro] = useState<number | ''>('');
  const [inativos, setInativos] = useState(false);
  const cats = useAsync(() => api<Categoria[]>('/categorias/'), []);
  const prods = useAsync(
    () =>
      api<Produto[]>('/menu/', {
        query: { busca, id_categoria: catFiltro === '' ? undefined : catFiltro, incluir_inativos: inativos },
      }),
    [busca, catFiltro, inativos],
  );
  const [editProd, setEditProd] = useState<Produto | 'novo' | null>(null);
  const [editCat, setEditCat] = useState<Categoria | 'nova' | null>(null);
  const [excluir, setExcluir] = useState<Produto | null>(null);
  const [historico, setHistorico] = useState<Produto | null>(null);

  const categorias = cats.data || [];
  const nomeCat = (id: number) => categorias.find((c) => c.id === id)?.nome || '-';

  const alternarDisp = async (p: Produto) => {
    try {
      await api(`/menu/${p.id}`, { method: 'PATCH', body: { is_disponivel: !p.is_disponivel } });
      prods.recarregar(true);
    } catch (e) {
      toast((e as Error).message, 'erro');
    }
  };

  return (
    <div>
      <div className="pagina-topo">
        <h1>Produtos e categorias</h1>
        <div className="acoes">
          <button className="btn" onClick={() => setEditCat('nova')}>
            + Categoria
          </button>
          <button className="btn btn-primario" onClick={() => setEditProd('novo')} disabled={!categorias.length}>
            + Produto
          </button>
        </div>
      </div>

      <section className="card">
        <h2>Categorias</h2>
        {cats.erro && <ErrorBox erro={cats.erro} />}
        {categorias.length === 0 && !cats.carregando && <Empty>Cadastre uma categoria para começar.</Empty>}
        <div className="chips">
          {categorias.map((c) => (
            <button key={c.id} className={`chip ${c.ativo ? '' : 'inativo'}`} onClick={() => setEditCat(c)}>
              {c.nome} {!c.ativo && '(oculta)'} ✎
            </button>
          ))}
        </div>
      </section>

      <div className="filtros">
        <input placeholder="Buscar por nome ou descrição" value={busca} onChange={(e) => setBusca(e.target.value)} />
        <select value={catFiltro} onChange={(e) => setCatFiltro(e.target.value ? Number(e.target.value) : '')}>
          <option value="">Todas as categorias</option>
          {categorias.map((c) => (
            <option key={c.id} value={c.id}>
              {c.nome}
            </option>
          ))}
        </select>
        <label className="toggle">
          <input type="checkbox" checked={inativos} onChange={(e) => setInativos(e.target.checked)} /> Incluir desativados
        </label>
      </div>

      {prods.erro && <ErrorBox erro={prods.erro} onRetry={() => prods.recarregar()} />}
      {prods.carregando && !prods.data ? (
        <Loading />
      ) : prods.data?.length === 0 ? (
        <Empty>Nenhum produto encontrado.</Empty>
      ) : (
        <div className="tabela-wrap">
          <table className="tabela">
            <thead>
              <tr>
                <th>Produto</th>
                <th>Categoria</th>
                <th className="num">Preço</th>
                <th>Disponível</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {prods.data?.map((p) => (
                <tr key={p.id} className={p.ativo ? '' : 'linha-inativa'}>
                  <td>
                    <strong>{p.nome}</strong>
                    {!p.ativo && <Badge status="cancelado">Desativado</Badge>}
                    {p.descricao && <div className="muted small">{p.descricao}</div>}
                  </td>
                  <td>{nomeCat(p.id_categoria)}</td>
                  <td className="num">{money(p.preco)}</td>
                  <td>
                    <label className="switch">
                      <input type="checkbox" checked={p.is_disponivel} onChange={() => alternarDisp(p)} disabled={!p.ativo} />
                      <span>{p.is_disponivel ? 'Sim' : 'Não'}</span>
                    </label>
                  </td>
                  <td className="acoes-linha">
                    <button className="btn btn-sm" onClick={() => setEditProd(p)}>
                      Editar
                    </button>
                    <button className="btn btn-sm" onClick={() => setHistorico(p)}>
                      Preços
                    </button>
                    {p.ativo && (
                      <button className="btn btn-sm btn-perigo-sutil" onClick={() => setExcluir(p)}>
                        Remover
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {editProd && (
        <ModalProduto
          produto={editProd === 'novo' ? null : editProd}
          categorias={categorias}
          onClose={() => setEditProd(null)}
          onSalvo={() => {
            setEditProd(null);
            prods.recarregar(true);
          }}
        />
      )}
      {editCat && (
        <ModalCategoria
          categoria={editCat === 'nova' ? null : editCat}
          onClose={() => setEditCat(null)}
          onSalvo={() => {
            setEditCat(null);
            cats.recarregar(true);
          }}
        />
      )}
      {excluir && (
        <ConfirmModal
          titulo={`Remover ${excluir.nome}`}
          mensagem="Produtos que já foram vendidos são apenas desativados, preservando o histórico dos pedidos."
          perigo
          textoConfirmar="Remover"
          onClose={() => setExcluir(null)}
          onConfirm={async () => {
            const res = await api<Response>(`/menu/${excluir.id}`, { method: 'DELETE', raw: true });
            toast(res.headers.get('X-Resultado') === 'desativado' ? 'Produto desativado' : 'Produto excluído');
            prods.recarregar(true);
          }}
        />
      )}
      {historico && <ModalHistorico produto={historico} onClose={() => setHistorico(null)} />}
    </div>
  );
}

function ModalProduto({
  produto,
  categorias,
  onClose,
  onSalvo,
}: {
  produto: Produto | null;
  categorias: Categoria[];
  onClose: () => void;
  onSalvo: () => void;
}) {
  const [f, setF] = useState({
    nome: produto?.nome || '',
    preco: produto?.preco || '',
    descricao: produto?.descricao || '',
    url_imagem: produto?.url_imagem || '',
    id_categoria: produto?.id_categoria || categorias[0]?.id || 0,
    tempo_preparo_min: produto?.tempo_preparo_min?.toString() || '',
    is_disponivel: produto?.is_disponivel ?? true,
    ativo: produto?.ativo ?? true,
  });
  const [erro, setErro] = useState<string | null>(null);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const preco = Number(String(f.preco).replace(',', '.'));
    if (!Number.isFinite(preco) || preco < 0) return setErro('Preço inválido');
    const body = {
      nome: f.nome,
      preco: preco.toFixed(2),
      descricao: f.descricao || null,
      url_imagem: f.url_imagem || null,
      id_categoria: Number(f.id_categoria),
      tempo_preparo_min: f.tempo_preparo_min ? Number(f.tempo_preparo_min) : null,
      is_disponivel: f.is_disponivel,
      ...(produto ? { ativo: f.ativo } : {}),
    };
    try {
      if (produto) await api(`/menu/${produto.id}`, { method: 'PATCH', body });
      else await api('/menu/', { body });
      onSalvo();
    } catch (err) {
      setErro((err as Error).message);
    }
  };

  return (
    <Modal titulo={produto ? 'Editar produto' : 'Novo produto'} onClose={onClose}>
      <form className="form" onSubmit={submit}>
        <label>
          Nome
          <input value={f.nome} onChange={(e) => setF({ ...f, nome: e.target.value })} required maxLength={120} />
        </label>
        <div className="grid-2">
          <label>
            Preço (R$)
            <input inputMode="decimal" value={f.preco} onChange={(e) => setF({ ...f, preco: e.target.value })} required />
          </label>
          <label>
            Categoria
            <select value={f.id_categoria} onChange={(e) => setF({ ...f, id_categoria: Number(e.target.value) })}>
              {categorias.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nome}
                </option>
              ))}
            </select>
          </label>
        </div>
        <label>
          Descrição
          <textarea value={f.descricao} onChange={(e) => setF({ ...f, descricao: e.target.value })} maxLength={500} />
        </label>
        <div className="grid-2">
          <label>
            URL da imagem
            <input type="url" value={f.url_imagem} onChange={(e) => setF({ ...f, url_imagem: e.target.value })} />
          </label>
          <label>
            Tempo de preparo (min)
            <input
              type="number"
              min={1}
              max={600}
              value={f.tempo_preparo_min}
              onChange={(e) => setF({ ...f, tempo_preparo_min: e.target.value })}
              placeholder="Padrão da loja"
            />
          </label>
        </div>
        <label className="toggle">
          <input type="checkbox" checked={f.is_disponivel} onChange={(e) => setF({ ...f, is_disponivel: e.target.checked })} />
          Disponível para pedidos
        </label>
        {produto && (
          <label className="toggle">
            <input type="checkbox" checked={f.ativo} onChange={(e) => setF({ ...f, ativo: e.target.checked })} />
            Produto ativo (aparece no cardápio)
          </label>
        )}
        {produto && <p className="muted small">Alterar o preço não muda o valor de pedidos já registrados.</p>}
        {erro && <ErrorBox erro={erro} />}
        <div className="form-actions">
          <button className="btn btn-primario">Salvar</button>
        </div>
      </form>
    </Modal>
  );
}

function ModalCategoria({
  categoria,
  onClose,
  onSalvo,
}: {
  categoria: Categoria | null;
  onClose: () => void;
  onSalvo: () => void;
}) {
  const [nome, setNome] = useState(categoria?.nome || '');
  const [ordem, setOrdem] = useState(categoria?.ordem ?? 0);
  const [ativo, setAtivo] = useState(categoria?.ativo ?? true);
  const [erro, setErro] = useState<string | null>(null);
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      if (categoria) await api(`/categorias/${categoria.id}`, { method: 'PUT', body: { nome, ordem, ativo } });
      else await api('/categorias/', { body: { nome, ordem } });
      onSalvo();
    } catch (err) {
      setErro((err as Error).message);
    }
  };
  return (
    <Modal titulo={categoria ? 'Editar categoria' : 'Nova categoria'} onClose={onClose}>
      <form className="form" onSubmit={submit}>
        <label>
          Nome
          <input value={nome} onChange={(e) => setNome(e.target.value)} required maxLength={80} autoFocus />
        </label>
        <label>
          Ordem de exibição
          <input type="number" value={ordem} onChange={(e) => setOrdem(Number(e.target.value))} />
        </label>
        {categoria && (
          <label className="toggle">
            <input type="checkbox" checked={ativo} onChange={(e) => setAtivo(e.target.checked)} /> Visível no cardápio
          </label>
        )}
        {erro && <ErrorBox erro={erro} />}
        <div className="form-actions">
          <button className="btn btn-primario">Salvar</button>
        </div>
      </form>
    </Modal>
  );
}

function ModalHistorico({ produto, onClose }: { produto: Produto; onClose: () => void }) {
  const { data, carregando } = useAsync(
    () => api<{ preco_anterior: string; preco_novo: string; alterado_em: string }[]>(`/menu/${produto.id}/historico-precos`),
    [produto.id],
  );
  return (
    <Modal titulo={`Histórico de preços · ${produto.nome}`} onClose={onClose}>
      {carregando ? (
        <Loading />
      ) : !data?.length ? (
        <Empty>Preço nunca alterado. Atual: {money(produto.preco)}</Empty>
      ) : (
        <table className="tabela">
          <thead>
            <tr>
              <th>Data</th>
              <th className="num">De</th>
              <th className="num">Para</th>
            </tr>
          </thead>
          <tbody>
            {data.map((h, i) => (
              <tr key={i}>
                <td>{dataHora(h.alterado_em)}</td>
                <td className="num">{money(h.preco_anterior)}</td>
                <td className="num">{money(h.preco_novo)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Modal>
  );
}
