"""Geracao de BR Code PIX estatico (padrao EMV do Banco Central).

O codigo gerado aqui e um "copia e cola" valido, que o cliente pode pagar
pelo app do banco. Ele NAO possui confirmacao automatica: sem um provedor
de pagamentos integrado, o recebimento precisa ser conferido e registrado
manualmente por um funcionario.
"""

import unicodedata
from decimal import Decimal


def _campo(id_: str, valor: str) -> str:
    return f'{id_}{len(valor):02d}{valor}'


def _limpar(texto: str, limite: int) -> str:
    norm = unicodedata.normalize('NFKD', texto)
    ascii_txt = norm.encode('ascii', 'ignore').decode().upper()
    return ascii_txt[:limite] or 'NA'


def crc16_ccitt(payload: str) -> str:
    crc = 0xFFFF
    for byte in payload.encode('utf-8'):
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return f'{crc:04X}'


def gerar_br_code(
    chave: str, nome: str, cidade: str, valor: Decimal, txid: str
) -> str:
    conta = _campo('00', 'br.gov.bcb.pix') + _campo('01', chave.strip())
    txid_limpo = ''.join(c for c in txid if c.isalnum())[:25] or '***'
    payload = (
        _campo('00', '01')
        + _campo('26', conta)
        + _campo('52', '0000')
        + _campo('53', '986')
        + _campo('54', f'{valor:.2f}')
        + _campo('58', 'BR')
        + _campo('59', _limpar(nome, 25))
        + _campo('60', _limpar(cidade, 15))
        + _campo('62', _campo('05', txid_limpo))
        + '6304'
    )
    return payload + crc16_ccitt(payload)
