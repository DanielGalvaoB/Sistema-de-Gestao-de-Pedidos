import { ChartColumn, ChefHat, LogIn, QrCode, Store, UserPlus, Wallet, type LucideIcon } from 'lucide-react';
import { useState, type FormEvent, type ReactNode } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import { paginaInicial } from '../components/AdminLayout';
import { ErrorBox } from '../components/ui';

const DESTAQUES: { icone: LucideIcon; texto: string }[] = [
  { icone: QrCode, texto: 'Cardápio digital por QR Code em cada mesa' },
  { icone: ChefHat, texto: 'Painel da cozinha em tempo real' },
  { icone: Wallet, texto: 'Contas, pagamentos e PIX' },
  { icone: ChartColumn, texto: 'Financeiro e relatórios por período' },
];

function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="auth-pagina">
      <aside className="auth-lateral">
        <div className="auth-marca">
          <span className="marca-logo grande">
            <Store size={26} />
          </span>
          <strong>Gestão de Pedidos</strong>
        </div>
        <h2>Do pedido ao caixa, tudo em um só lugar.</h2>
        <ul>
          {DESTAQUES.map(({ icone: Icone, texto }) => (
            <li key={texto}>
              <span>
                <Icone size={18} />
              </span>
              {texto}
            </li>
          ))}
        </ul>
      </aside>
      <main className="auth-conteudo">{children}</main>
    </div>
  );
}

export function Login() {
  const { login, user } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  if (user) return <Navigate to={paginaInicial(user.perfil)} replace />;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setEnviando(true);
    setErro(null);
    try {
      await login(email, senha);
      navigate('/admin');
    } catch (err) {
      setErro((err as Error).message);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <AuthLayout>
      <form className="form auth-card" onSubmit={submit}>
        <div>
          <h1>Entrar</h1>
          <p className="muted">Acesse o painel do seu estabelecimento.</p>
        </div>
        <label>
          Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoFocus autoComplete="username" />
        </label>
        <label>
          Senha
          <input type="password" value={senha} onChange={(e) => setSenha(e.target.value)} required autoComplete="current-password" />
        </label>
        {erro && <ErrorBox erro={erro} />}
        <button className="btn btn-primario btn-grande" disabled={enviando}>
          <LogIn size={18} /> {enviando ? 'Entrando...' : 'Entrar'}
        </button>
        <p className="muted small centro">
          Ainda não tem cadastro? <Link to="/cadastro">Cadastrar estabelecimento</Link>
        </p>
      </form>
    </AuthLayout>
  );
}

export function Cadastro() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [f, setF] = useState({
    nome_loja: '',
    nome_titular: '',
    chave_pix: '',
    cidade: '',
    email: '',
    password: '',
  });
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const set = (k: keyof typeof f) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value });

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setEnviando(true);
    setErro(null);
    try {
      await api('/estabelecimentos/', { body: { ...f, cidade: f.cidade || 'SAO PAULO' }, auth: false });
      await login(f.email, f.password);
      navigate('/admin/produtos');
    } catch (err) {
      setErro((err as Error).message);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <AuthLayout>
      <form className="form auth-card" onSubmit={submit}>
        <div>
          <h1>Cadastrar estabelecimento</h1>
          <p className="muted">O email e a senha informados serão do administrador.</p>
        </div>
        <label>
          Nome do estabelecimento
          <input value={f.nome_loja} onChange={set('nome_loja')} required />
        </label>
        <label>
          Nome do titular (recebedor PIX)
          <input value={f.nome_titular} onChange={set('nome_titular')} required />
        </label>
        <div className="grid-2">
          <label>
            Chave PIX
            <input value={f.chave_pix} onChange={set('chave_pix')} required />
          </label>
          <label>
            Cidade
            <input value={f.cidade} onChange={set('cidade')} placeholder="SAO PAULO" />
          </label>
        </div>
        <label>
          Email do administrador
          <input type="email" value={f.email} onChange={set('email')} required autoComplete="username" />
        </label>
        <label>
          Senha (mínimo 8 caracteres)
          <input type="password" value={f.password} onChange={set('password')} required minLength={8} autoComplete="new-password" />
        </label>
        {erro && <ErrorBox erro={erro} />}
        <button className="btn btn-primario btn-grande" disabled={enviando}>
          <UserPlus size={18} /> {enviando ? 'Cadastrando...' : 'Cadastrar'}
        </button>
        <p className="muted small centro">
          Já tem conta? <Link to="/login">Entrar</Link>
        </p>
      </form>
    </AuthLayout>
  );
}
