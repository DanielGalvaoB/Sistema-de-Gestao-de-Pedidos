"""Armazenamento local das imagens dos produtos.

O arquivo enviado e aberto com Pillow (o que rejeita qualquer coisa que nao
seja imagem), tem a orientacao corrigida, e reduzido e regravado como WebP.
Assim nunca servimos o arquivo original enviado pelo usuario.
"""

import io
import mimetypes
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from app.config import settings
from app.core.errors import BusinessRuleError
from app.core.utils import novo_token

# O registro do Windows nem sempre conhece .webp; sem isso o arquivo seria
# servido como text/plain
mimetypes.add_type('image/webp', '.webp')

PREFIXO_URL = '/uploads'
TAMANHO_MAXIMO_PX = 1200
FORMATOS_ACEITOS = {'JPEG', 'PNG', 'WEBP', 'GIF'}


def pasta_uploads() -> Path:
    pasta = Path(settings.UPLOAD_DIR)
    (pasta / 'produtos').mkdir(parents=True, exist_ok=True)
    return pasta


def salvar_imagem_produto(conteudo: bytes, id_estab: int, id_menu: int) -> str:
    limite = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(conteudo) > limite:
        raise BusinessRuleError(
            f'Imagem maior que {settings.MAX_UPLOAD_MB} MB'
        )
    try:
        with Image.open(io.BytesIO(conteudo)) as teste:
            formato = teste.format
            teste.verify()
        if formato not in FORMATOS_ACEITOS:
            raise BusinessRuleError(
                'Formato nao suportado (use JPG, PNG ou WebP)'
            )
        img = Image.open(io.BytesIO(conteudo))
        img = ImageOps.exif_transpose(img)
        img.thumbnail((TAMANHO_MAXIMO_PX, TAMANHO_MAXIMO_PX))
        if img.mode not in {'RGB', 'RGBA'}:
            img = img.convert('RGBA' if 'A' in img.getbands() else 'RGB')
    except (
        UnidentifiedImageError,
        OSError,
        Image.DecompressionBombError,
    ) as exc:
        raise BusinessRuleError(
            'Arquivo enviado nao e uma imagem valida'
        ) from exc

    nome = f'{id_estab}_{id_menu}_{novo_token(8)}.webp'
    destino = pasta_uploads() / 'produtos' / nome
    img.save(destino, 'WEBP', quality=82, method=4)
    return f'{PREFIXO_URL}/produtos/{nome}'


def remover_imagem_local(url: str | None) -> None:
    """Apaga o arquivo se a URL apontar para um upload local."""
    if not url or not url.startswith(f'{PREFIXO_URL}/produtos/'):
        return
    nome = Path(url).name
    caminho = pasta_uploads() / 'produtos' / nome
    if caminho.is_file():
        caminho.unlink()
