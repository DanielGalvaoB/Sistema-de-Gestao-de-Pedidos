import {
  ChartColumn,
  ChefHat,
  ExternalLink,
  LayoutDashboard,
  LogOut,
  Menu as MenuIcon,
  ReceiptText,
  Settings,
  Store,
  UtensilsCrossed,
  Wallet,
  Armchair,
  CreditCard,
  X,
  type LucideIcon,
} from 'lucide-react';
import { useState } from 'react';
import { NavLink, Navigate, Outlet, useLocation } from 'react-router-dom';
import type { Perfil } from '../api/types';
import { useAuth } from '../auth/AuthContext';
import { PERFIL_LABEL } from '../utils/format';
import { Loading } from './ui';

export const NAV: { to: string; label: string; icone: LucideIcon; perfis: Perfil[]; grupo: string }[] = [
  { to: '/admin', label: 'Painel', icone: LayoutDashboard, perfis: ['atendente', 'financeiro'], grupo: 'Operação' },
  { to: '/admin/cozinha', label: 'Cozinha', icone: ChefHat, perfis: ['cozinha', 'atendente'], grupo: 'Operação' },
  { to: '/admin/pedidos', label: 'Pedidos', icone: ReceiptText, perfis: ['cozinha', 'atendente'], grupo: 'Operação' },
  { to: '/admin/mesas', label: 'Mesas', icone: Armchair, perfis: ['atendente'], grupo: 'Operação' },
  { to: '/admin/caixa', label: 'Caixa', icone: CreditCard, perfis: ['atendente', 'financeiro'], grupo: 'Operação' },
  { to: '/admin/produtos', label: 'Cardápio', icone: UtensilsCrossed, perfis: [], grupo: 'Gestão' },
  { to: '/admin/financeiro', label: 'Recebimentos', icone: Wallet, perfis: ['financeiro'], grupo: 'Gestão' },
  { to: '/admin/relatorios', label: 'Relatórios', icone: ChartColumn, perfis: ['financeiro'], grupo: 'Gestão' },
  { to: '/admin/configuracoes', label: 'Configurações', icone: Settings, perfis: [], grupo: 'Gestão' },
];

export function paginaInicial(perfil: Perfil): string {
  if (perfil === 'cozinha') return '/admin/cozinha';
  return '/admin';
}

function iniciais(nome: string) {
  return nome
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase())
    .join('');
}

export default function AdminLayout() {
  const { user, carregando, logout, pode } = useAuth();
  const [menuAberto, setMenuAberto] = useState(false);
  const loc = useLocation();

  if (carregando) return <Loading />;
  if (!user) return <Navigate to="/login" replace state={{ de: loc.pathname }} />;

  const itens = NAV.filter((n) => pode(...n.perfis));
  const grupos = [...new Set(itens.map((i) => i.grupo))];
  const telaCheia = loc.pathname === '/admin/cozinha';
  const atual = itens.find((n) => (n.to === '/admin' ? loc.pathname === '/admin' : loc.pathname.startsWith(n.to)));

  return (
    <div className={`admin ${telaCheia ? 'admin-tela-cheia' : ''}`}>
      <aside className={`sidebar ${menuAberto ? 'aberto' : ''}`}>
        <div className="sidebar-marca">
          <span className="marca-logo">
            <Store size={20} />
          </span>
          <div>
            <strong>{user.nome_loja}</strong>
            <span>Gestão de pedidos</span>
          </div>
          <button className="btn-icon sidebar-fechar" onClick={() => setMenuAberto(false)} aria-label="Fechar menu">
            <X size={20} />
          </button>
        </div>
        <nav onClick={() => setMenuAberto(false)}>
          {grupos.map((g) => (
            <div key={g} className="nav-grupo">
              <span className="nav-grupo-titulo">{g}</span>
              {itens
                .filter((i) => i.grupo === g)
                .map(({ to, label, icone: Icone }) => (
                  <NavLink key={to} to={to} end={to === '/admin'}>
                    <Icone size={18} strokeWidth={1.75} />
                    <span>{label}</span>
                  </NavLink>
                ))}
            </div>
          ))}
          <div className="nav-grupo">
            <a href={`/c/${user.slug}`} target="_blank" rel="noreferrer">
              <ExternalLink size={18} strokeWidth={1.75} />
              <span>Ver cardápio público</span>
            </a>
          </div>
        </nav>
        <div className="sidebar-usuario">
          <span className="avatar">{iniciais(user.nome)}</span>
          <div className="sidebar-usuario-info">
            <strong>{user.nome}</strong>
            <span>{PERFIL_LABEL[user.perfil]}</span>
          </div>
          <button className="btn-icon" onClick={logout} title="Sair" aria-label="Sair">
            <LogOut size={18} />
          </button>
        </div>
      </aside>
      {menuAberto && <div className="sidebar-overlay" onClick={() => setMenuAberto(false)} />}

      <div className="area">
        <header className="topbar-mobile">
          <button className="btn-icon" onClick={() => setMenuAberto(true)} aria-label="Abrir menu">
            <MenuIcon size={22} />
          </button>
          <strong>{atual?.label || user.nome_loja}</strong>
        </header>
        <main className="conteudo">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export function RequirePerfil({ perfis, children }: { perfis: Perfil[]; children: JSX.Element }) {
  const { user, pode } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (!pode(...perfis)) return <Navigate to={paginaInicial(user.perfil)} replace />;
  return children;
}
