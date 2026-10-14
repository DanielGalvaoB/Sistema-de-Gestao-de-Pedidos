import { KeyRound, Pencil, QrCode, Settings, Store, UserPlus, Users } from 'lucide-react';
import { useEffect, useState, type FormEvent } from 'react';
import { api } from '../../api/client';
import type { Estabelecimento, Perfil, Usuario } from '../../api/types';
import { useAuth } from '../../auth/AuthContext';
import { Badge, ErrorBox, Loading, Modal, useToast } from '../../components/ui';
import { useAsync } from '../../hooks/useAsync';
import { PERFIL_LABEL } from '../../utils/format';
import { ModalQr } from './Mesas';

export default function Configuracoes() {
  const { pode } = useAuth();
  return (
    <div>
      <div className="pagina-topo">
        <div className="pagina-titulo">
          <span className="pagina-icone">
            <Settings size={22} strokeWidth={1.75} />
          </span>
          <div>
            <h1>Configurações</h1>
            <p className="muted small">Dados da loja, operação, usuários e senha</p>
          </div>
        </div>
      </div>
      {pode() && <DadosLoja />}
      {pode() && <Usuarios />}
      <MinhaSenha />
    </div>
  );
}

function DadosLoja() {
  const toast = useToast();
  const { data, erro, carregando, recarregar } = useAsync(() => api<Estabelecimento>('/estabelecimentos/me'), []);
  const [f, setF] = useState<Partial<Estabelecimento>>({});
  const [qr, setQr] = useState<{ url: string; descricao: string } | null>(null);
  useEffect(() => {
    if (data) setF(data);
  }, [data]);

  if (carregando) return <Loading />;
  if (erro || !data) return <ErrorBox erro={erro || 'Erro'} onRetry={() => recarregar()} />;

  const salvar = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await api(`/estabelecimentos/${data.id}`, {
        method: 'PATCH',
        body: {
          nome_loja: f.nome_loja,
          nome_titular: f.nome_titular,
          chave_pix: f.chave_pix,
          cidade: f.cidade,
          email: f.email,
          taxa_servico_percentual: Number(f.taxa_servico_percentual).toFixed(2),
        },
      });
      toast('Configurações salvas');
      recarregar(true);
    } catch (err) {
      toast((err as Error).message, 'erro');
    }
  };

  const set = (k: keyof Estabelecimento) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value });

  return (
    <section className="card">
      <h2 className="card-titulo">
        <Store size={18} /> Estabelecimento
      </h2>
      <form className="form" onSubmit={salvar}>
        <div className="grid-2">
          <label>
            Nome
            <input value={f.nome_loja || ''} onChange={set('nome_loja')} required />
          </label>
          <label>
            Email
            <input type="email" value={f.email || ''} onChange={set('email')} required />
          </label>
          <label>
            Titular PIX
            <input value={f.nome_titular || ''} onChange={set('nome_titular')} required />
          </label>
          <label>
            Chave PIX
            <input value={f.chave_pix || ''} onChange={set('chave_pix')} required />
          </label>
          <label>
            Cidade
            <input value={f.cidade || ''} onChange={set('cidade')} required />
          </label>
          <label>
            Taxa de serviço (%)
            <input type="number" min={0} max={30} step="0.01" value={f.taxa_servico_percentual ?? ''} onChange={set('taxa_servico_percentual')} />
          </label>
        </div>
        <div className="form-actions">
          <button
            type="button"
            className="btn"
            onClick={async () => setQr(await api('/estabelecimentos/me/qrcode'))}
          >
            <QrCode size={16} /> QR Code do cardápio geral
          </button>
          <button className="btn btn-primario">Salvar</button>
        </div>
      </form>
      {qr && <ModalQr {...qr} onClose={() => setQr(null)} />}
    </section>
  );
}

function Usuarios() {
  const { user } = useAuth();
  const { data, erro, recarregar } = useAsync(() => api<Usuario[]>('/usuarios/'), []);
  const [edit, setEdit] = useState<Usuario | 'novo' | null>(null);
  return (
    <section className="card">
      <div className="pagina-topo">
        <h2 className="card-titulo">
          <Users size={18} /> Usuários
        </h2>
        <button className="btn btn-primario" onClick={() => setEdit('novo')}>
          <UserPlus size={16} /> Usuário
        </button>
      </div>
      {erro && <ErrorBox erro={erro} />}
      <div className="tabela-wrap">
        <table className="tabela">
          <thead>
            <tr>
              <th>Nome</th>
              <th>Email</th>
              <th>Perfil</th>
              <th>Status</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {data?.map((u) => (
              <tr key={u.id}>
                <td>
                  {u.nome} {u.id === user?.id && <span className="muted">(você)</span>}
                </td>
                <td>{u.email}</td>
                <td>{PERFIL_LABEL[u.perfil]}</td>
                <td>{u.ativo ? <Badge status="ativa">Ativo</Badge> : <Badge status="cancelado">Inativo</Badge>}</td>
                <td>
                  <button className="btn btn-sm" onClick={() => setEdit(u)}>
                    <Pencil size={14} /> Editar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {edit && (
        <ModalUsuario
          usuario={edit === 'novo' ? null : edit}
          onClose={() => setEdit(null)}
          onSalvo={() => {
            setEdit(null);
            recarregar(true);
          }}
        />
      )}
    </section>
  );
}

function ModalUsuario({ usuario, onClose, onSalvo }: { usuario: Usuario | null; onClose: () => void; onSalvo: () => void }) {
  const [f, setF] = useState({
    nome: usuario?.nome || '',
    email: usuario?.email || '',
    perfil: (usuario?.perfil || 'atendente') as Perfil,
    password: '',
    ativo: usuario?.ativo ?? true,
  });
  const [erro, setErro] = useState<string | null>(null);
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      if (usuario) {
        await api(`/usuarios/${usuario.id}`, {
          method: 'PATCH',
          body: { nome: f.nome, email: f.email, perfil: f.perfil, ativo: f.ativo, password: f.password || undefined },
        });
      } else {
        await api('/usuarios/', { body: { nome: f.nome, email: f.email, perfil: f.perfil, password: f.password } });
      }
      onSalvo();
    } catch (err) {
      setErro((err as Error).message);
    }
  };
  return (
    <Modal titulo={usuario ? 'Editar usuário' : 'Novo usuário'} onClose={onClose}>
      <form className="form" onSubmit={submit}>
        <label>
          Nome
          <input value={f.nome} onChange={(e) => setF({ ...f, nome: e.target.value })} required />
        </label>
        <label>
          Email
          <input type="email" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} required />
        </label>
        <label>
          Perfil
          <select value={f.perfil} onChange={(e) => setF({ ...f, perfil: e.target.value as Perfil })}>
            {Object.entries(PERFIL_LABEL).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </select>
        </label>
        <label>
          {usuario ? 'Nova senha (deixe em branco para manter)' : 'Senha'}
          <input
            type="password"
            minLength={8}
            value={f.password}
            onChange={(e) => setF({ ...f, password: e.target.value })}
            required={!usuario}
          />
        </label>
        {usuario && (
          <label className="toggle">
            <input type="checkbox" checked={f.ativo} onChange={(e) => setF({ ...f, ativo: e.target.checked })} /> Ativo
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

function MinhaSenha() {
  const toast = useToast();
  const [atual, setAtual] = useState('');
  const [nova, setNova] = useState('');
  return (
    <section className="card">
      <h2 className="card-titulo">
        <KeyRound size={18} /> Alterar minha senha
      </h2>
      <form
        className="form grid-2"
        onSubmit={async (e) => {
          e.preventDefault();
          try {
            await api('/usuarios/me/senha', { method: 'PATCH', body: { senha_atual: atual, nova_senha: nova } });
            toast('Senha alterada');
            setAtual('');
            setNova('');
          } catch (err) {
            toast((err as Error).message, 'erro');
          }
        }}
      >
        <label>
          Senha atual
          <input type="password" value={atual} onChange={(e) => setAtual(e.target.value)} required />
        </label>
        <label>
          Nova senha
          <input type="password" minLength={8} value={nova} onChange={(e) => setNova(e.target.value)} required />
        </label>
        <div className="form-actions">
          <button className="btn btn-primario">Alterar senha</button>
        </div>
      </form>
    </section>
  );
}
