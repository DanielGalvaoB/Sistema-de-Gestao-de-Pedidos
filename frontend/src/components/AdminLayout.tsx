import { useState } from 'react';
import { NavLink, Navigate, Outlet, useLocation } from 'react-router-dom';
import type { Perfil } from '../api/types';
import { useAuth } from '../auth/AuthContext';
import { PERFIL_LABEL } from '../utils/format';
import { Loading } from './ui';

export const NAV: { to: string; label: string; icone: string; perfis: Perfil[] }[] = [
  { to: '/admin', label: 'Painel', icone: '📊', perfis: ['atendente', 'financeiro'] },
  { to: '/admin/cozinha', label: 'Cozinha', icone: '🍳', perfis: ['cozinha', 'atendente'] },
  { to: '/admin/pedidos', label: 'Pedidos', icone: '🧾', perfis: ['cozinha', 'atendente'] },
  { to: '/admin/mesas', label: 'Mesas e contas', icone: '🪑', perfis: ['atendente'] },
  { to: '/admin/caixa', label: 'Caixa', icone: '💳', perfis: ['atendente', 'financeiro'] },
  { to: '/admin/produtos', label: 'Produtos', icone: '🍔', perfis: [] },
  { to: '/admin/financeiro', label: 'Financeiro', icone: '💰', perfis: ['financeiro'] },
  { to: '/admin/relatorios', label: 'Relatórios', icone: '📈', perfis: ['financeiro'] },
  { to: '/admin/configuracoes', label: 'Configurações', icone: '⚙️', perfis: [] },
];

export function paginaInicial(perfil: Perfil): string {
  if (perfil === 'cozinha') return '/admin/cozinha';
  return '/admin';
}

export default function AdminLayout() {
  const { user, carregando, logout, pode } = useAuth();
  const [menuAberto, setMenuAberto] = useState(false);
  const loc = useLocation();

  if (carregando) return <Loading />;
  if (!user) return <Navigate to="/login" replace state={{ de: loc.pathname }} />;

  const itens = NAV.filter((n) => pode(...n.perfis));
  const telaCheia = loc.pathname === '/admin/cozinha';

  return (
    <div className={`admin ${telaCheia ? 'admin-tela-cheia' : ''}`}>
      <header className="topbar">
        <button className="btn-icon menu-toggle" onClick={() => setMenuAberto((v) => !v)} aria-label="Menu">
          ☰
        </button>
        <strong className="topbar-loja">{user.nome_loja}</strong>
        <span className="topbar-user">
          {user.nome} · {PERFIL_LABEL[user.perfil]}
        </span>
        <button className="btn btn-sm" onClick={logout}>
          Sair
        </button>
      </header>
      <nav className={`sidebar ${menuAberto ? 'aberto' : ''}`} onClick={() => setMenuAberto(false)}>
        {itens.map((n) => (
          <NavLink key={n.to} to={n.to} end={n.to === '/admin'}>
            <span aria-hidden>{n.icone}</span> {n.label}
          </NavLink>
        ))}
        <a href={`/c/${user.slug}`} target="_blank" rel="noreferrer">
          <span aria-hidden>📱</span> Ver cardápio
        </a>
      </nav>
      <main className="conteudo">
        <Outlet />
      </main>
    </div>
  );
}

export function RequirePerfil({ perfis, children }: { perfis: Perfil[]; children: JSX.Element }) {
  const { user, pode } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (!pode(...perfis)) return <Navigate to={paginaInicial(user.perfil)} replace />;
  return children;
}
