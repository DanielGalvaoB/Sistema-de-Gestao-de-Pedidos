import { useEffect, useRef, useState } from 'react';
import { getToken, wsUrl } from '../api/client';
import { useInterval } from './useAsync';

/**
 * Chama `onChange` quando o servidor avisa que os pedidos mudaram (WebSocket).
 * Se o WebSocket cair, usa atualizacao periodica (polling) como reserva.
 */
export function useRealtime(onChange: () => void, pollingMs = 10000) {
  const cb = useRef(onChange);
  cb.current = onChange;
  const [conectado, setConectado] = useState(false);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let fechado = false;
    let tentativa: ReturnType<typeof setTimeout> | undefined;

    const conectar = () => {
      const token = getToken();
      if (!token || fechado) return;
      ws = new WebSocket(wsUrl(`/ws/pedidos?token=${encodeURIComponent(token)}`));
      ws.onopen = () => setConectado(true);
      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data);
          if (msg.evento === 'atualizar') cb.current();
        } catch {
          /* ignora */
        }
      };
      ws.onclose = () => {
        setConectado(false);
        if (!fechado) tentativa = setTimeout(conectar, 5000);
      };
      ws.onerror = () => ws?.close();
    };
    conectar();
    return () => {
      fechado = true;
      clearTimeout(tentativa);
      ws?.close();
    };
  }, []);

  // Polling de seguranca: mais lento quando o WebSocket esta conectado
  useInterval(() => cb.current(), conectado ? pollingMs * 3 : pollingMs);
  return conectado;
}
