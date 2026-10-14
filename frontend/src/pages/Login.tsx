import { useState, type FormEvent } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import { paginaInicial } from '../components/AdminLayout';
import { ErrorBox } from '../components/ui';

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
    <div className="auth-pagina">
      <form className="card form auth-card" onSubmit={submit}>
        <h1>Entrar</h1>
        <label>
          Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoFocus />
        </label>
        <label>
          Senha
          <input type="password" value={senha} onChange={(e) => setSenha(e.target.value)} required />
        </label>
        {erro && <ErrorBox erro={erro} />}
        <button className="btn btn-primario btn-grande" disabled={enviando}>
          {enviando ? 'Entrando...' : 'Entrar'}
        </button>
        <p className="muted small">
          Ainda não tem cadastro? <Link to="/cadastro">Cadastrar estabelecimento</Link>
        </p>
      </form>
    </div>
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
    <div className="auth-pagina">
      <form className="card form auth-card" onSubmit={submit}>
        <h1>Cadastrar estabelecimento</h1>
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
          <input type="email" value={f.email} onChange={set('email')} required />
        </label>
        <label>
          Senha (mínimo 8 caracteres)
          <input type="password" value={f.password} onChange={set('password')} required minLength={8} />
        </label>
        {erro && <ErrorBox erro={erro} />}
        <button className="btn btn-primario btn-grande" disabled={enviando}>
          {enviando ? 'Cadastrando...' : 'Cadastrar'}
        </button>
        <p className="muted small">
          Já tem conta? <Link to="/login">Entrar</Link>
        </p>
      </form>
    </div>
  );
}
