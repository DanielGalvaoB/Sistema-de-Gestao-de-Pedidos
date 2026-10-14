import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { api } from '../../api/client';
import type { CardapioPublico, ContaAcompanhamento } from '../../api/types';
import CardapioView, { lerUltimoPedido, salvarUltimoPedido } from '../../components/CardapioView';
import PublicoTopo from '../../components/PublicoTopo';
import { ErrorBox, Loading } from '../../components/ui';
import { useAsync } from '../../hooks/useAsync';

/** Cardapio aberto pelo QR Code (mesa ou geral). */
export default function Cardapio() {
  const { slug = '' } = useParams();
  const [sp] = useSearchParams();
  const mesaToken = sp.get('mesa');
  const navigate = useNavigate();

  const { data, erro, carregando, recarregar } = useAsync(async () => {
    const cardapio = await api<CardapioPublico>(`/public/${slug}`, { query: { mesa: mesaToken }, auth: false });
    // Se este aparelho ja tem um pedido com a conta aberta, os proximos
    // pedidos entram na mesma conta e a aba "Meus pedidos" fica disponivel.
    let conta: ContaAcompanhamento | null = null;
    const codigo = lerUltimoPedido(slug);
    if (codigo) {
      try {
        conta = await api<ContaAcompanhamento>(`/public/pedidos/${codigo}/conta`, { auth: false });
        const outraMesa = mesaToken && conta.mesa_numero !== cardapio.mesa_numero;
        if (!conta.conta_aberta || outraMesa) conta = null;
      } catch {
        conta = null;
      }
      if (!conta) salvarUltimoPedido(slug, null);
    }
    return { cardapio, conta, codigo: conta ? codigo : null };
  }, [slug, mesaToken]);

  if (carregando) return <Loading texto="Carregando cardápio..." />;
  if (erro || !data)
    return (
      <div className="publico">
        <ErrorBox erro={erro || 'Cardápio indisponível'} onRetry={() => recarregar()} />
      </div>
    );

  const { cardapio, conta, codigo } = data;
  return (
    <div className="publico">
      <PublicoTopo
        nomeLoja={cardapio.estabelecimento.nome_loja}
        mesaNumero={cardapio.mesa_numero}
        aba="cardapio"
        qtdPedidos={conta?.pedidos.length}
        onAba={codigo ? (aba) => aba === 'pedidos' && navigate(`/pedido/${codigo}`) : undefined}
      />
      <CardapioView
        slug={slug}
        cardapio={cardapio}
        mesaToken={mesaToken}
        codigoOrigem={codigo}
        onEnviado={(novo) => navigate(`/pedido/${novo}`)}
      />
    </div>
  );
}
