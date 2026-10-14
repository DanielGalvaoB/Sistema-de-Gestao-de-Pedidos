import { lazy, Suspense } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import AdminLayout, { RequirePerfil } from './components/AdminLayout';
import { Loading, ToastProvider } from './components/ui';
import { Cadastro, Login } from './pages/Login';
import Acompanhamento from './pages/public/Acompanhamento';
import Cardapio from './pages/public/Cardapio';

// Paginas administrativas carregadas sob demanda (cardapio publico fica leve)
const Caixa = lazy(() => import('./pages/admin/Caixa'));
const Configuracoes = lazy(() => import('./pages/admin/Configuracoes'));
const Conta = lazy(() => import('./pages/admin/Conta'));
const Cozinha = lazy(() => import('./pages/admin/Cozinha'));
const Dashboard = lazy(() => import('./pages/admin/Dashboard'));
const Financeiro = lazy(() => import('./pages/admin/Financeiro'));
const Mesas = lazy(() => import('./pages/admin/Mesas'));
const Pedidos = lazy(() => import('./pages/admin/Pedidos'));
const Produtos = lazy(() => import('./pages/admin/Produtos'));
const Relatorios = lazy(() => import('./pages/admin/Relatorios'));

export default function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <BrowserRouter>
          <Suspense fallback={<Loading />}>
          <Routes>
            <Route path="/" element={<Navigate to="/login" replace />} />
            <Route path="/login" element={<Login />} />
            <Route path="/cadastro" element={<Cadastro />} />
            {/* Publico: cardapio (QR Code) e acompanhamento do pedido */}
            <Route path="/c/:slug" element={<Cardapio />} />
            <Route path="/pedido/:codigo" element={<Acompanhamento />} />

            <Route path="/admin" element={<AdminLayout />}>
              <Route index element={<RequirePerfil perfis={['atendente', 'financeiro']}><Dashboard /></RequirePerfil>} />
              <Route path="cozinha" element={<RequirePerfil perfis={['cozinha', 'atendente']}><Cozinha /></RequirePerfil>} />
              <Route path="pedidos" element={<RequirePerfil perfis={['cozinha', 'atendente']}><Pedidos /></RequirePerfil>} />
              <Route path="mesas" element={<RequirePerfil perfis={['atendente']}><Mesas /></RequirePerfil>} />
              <Route path="caixa" element={<RequirePerfil perfis={['atendente', 'financeiro']}><Caixa /></RequirePerfil>} />
              <Route path="contas/:id" element={<RequirePerfil perfis={['atendente', 'financeiro']}><Conta /></RequirePerfil>} />
              <Route path="produtos" element={<RequirePerfil perfis={[]}><Produtos /></RequirePerfil>} />
              <Route path="financeiro" element={<RequirePerfil perfis={['financeiro']}><Financeiro /></RequirePerfil>} />
              <Route path="relatorios" element={<RequirePerfil perfis={['financeiro']}><Relatorios /></RequirePerfil>} />
              <Route path="configuracoes" element={<Configuracoes />} />
            </Route>
            <Route path="*" element={<div className="empty">Página não encontrada.</div>} />
          </Routes>
          </Suspense>
        </BrowserRouter>
      </AuthProvider>
    </ToastProvider>
  );
}
