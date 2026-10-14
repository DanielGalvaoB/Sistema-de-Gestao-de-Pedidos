import { useCallback, useEffect, useRef, useState } from 'react';

/** Carrega dados de uma funcao assincrona, com recarga manual. */
export function useAsync<T>(fn: () => Promise<T>, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(true);
  const fnRef = useRef(fn);
  fnRef.current = fn;

  const recarregar = useCallback(async (silencioso = false) => {
    if (!silencioso) setCarregando(true);
    try {
      setData(await fnRef.current());
      setErro(null);
    } catch (e) {
      setErro((e as Error).message);
    } finally {
      setCarregando(false);
    }
  }, []);

  useEffect(() => {
    recarregar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, setData, erro, carregando, recarregar };
}

/** Executa `fn` periodicamente enquanto a pagina esta montada. */
export function useInterval(fn: () => void, ms: number | null) {
  const ref = useRef(fn);
  ref.current = fn;
  useEffect(() => {
    if (ms === null) return;
    const id = setInterval(() => ref.current(), ms);
    return () => clearInterval(id);
  }, [ms]);
}

/** Relogio que atualiza a cada `ms` (para contadores de tempo). */
export function useAgora(ms = 15000) {
  const [agora, setAgora] = useState(Date.now());
  useInterval(() => setAgora(Date.now()), ms);
  return agora;
}
