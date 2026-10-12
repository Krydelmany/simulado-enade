"""Recorta a figura/imagem de uma questão direto do PDF.

As figuras das provas são vetoriais (o INEP monta tudo no Corel), então
`pdfimages` não serve. A estratégia é renderizar a página em alta resolução e
cortar a faixa vertical que pertence à questão — com uma margem para não
cortar o enunciado nem a alternativa seguinte.
"""

import os
import re
import subprocess
import sys
import unicodedata

sys.path.insert(0, '/root/enade-simulado/banco')
import layout

SAIDA = '/tmp/opencode/extr/fig'
DPI = 200
PAG_INICIAL = 4    # antes disso é capa e instruções, não questões


def _cabeçalho(s):
    s = unicodedata.normalize('NFD', s)
    return re.sub(r'[^A-Za-z0-9]', '', s)


def achar_pagina(pdf, edicao, qid):
    """-> (n_pagina, y_inicio, y_fim) em pontos, pela posição do cabeçalho."""
    numero = int(re.search(r'(\d{2})$', qid).group(1))
    disc = '-D' in qid
    # posição vertical do cabeçalho da questão dentro da prova (ordem do doc)
    for i, (W, H, ls) in enumerate(layout.ler_stext(pdf), 1):
        if i < PAG_INICIAL:          # capa/instruções
            continue
        for l in ls:
            t = l[4].strip()
            if not re.fullmatch(r'QUEST[AÃ]O\s+(?:DISCURSIVA\s+)?\d{1,2}', t, re.I):
                continue
            m = re.search(r'(\d{1,2})', t)
            if not m or int(m.group(1)) != numero:
                continue
            if ('DISCURSIVA' in t.upper()) != disc:
                continue
            return (i, l[0], W, H, ls)   # 1ª ocorrência (o final traz
    return None                       # um quadro-resumo das respostas)


def limites(ls, y_ini, H, W):
    """Faixa vertical da questão: do cabeçalho até o próximo cabeçalho."""
    prox = None
    for l in ls:
        if l[0] > y_ini + 4 and re.fullmatch(
            r'QUEST[AÃ]O\s+(?:DISCURSIVA\s+)?\d{1,2}', l[4].strip(), re.I
        ):
            if prox is None or l[0] < prox:
                prox = l[0]
    if prox is None:
        prox = H - 40
    return y_ini, prox


def render(pdf, pag, dpi=DPI):
    os.makedirs(SAIDA, exist_ok=True)
    base = f'{SAIDA}/pag{pag}'
    subprocess.run(
        ['pdftoppm', '-r', str(dpi), '-f', str(pag), '-l', str(pag),
         '-png', '-singlefile', pdf, base],
        check=True, capture_output=True,
    )
    return base + '.png'


def cortar(png, x0, y0, x1, y1, destino, escala=1.0):
    from PIL import Image

    with Image.open(png) as im:
        W, H = im.size
        px = im.convert('RGB').crop(
            (int(x0 * escala), int(y0 * escala), int(x1 * escala), int(y1 * escala))
        )
        px.save(destino, optimize=True)
        return px.size


def figura(pdf, edicao, qid, destino, y_topo=None, y_base=None,
           x_esq=None, x_dir=None, escala=1.6):
    """Renderiza e recorta a faixa da questão.

    y_topo/y_base/x_esq/x_dir em PONTOS do PDF (opcional: corta a página toda).
    """
    achado = achar_pagina(pdf, edicao, qid)
    if achado is None:
        raise SystemExit(f'página de {qid} não encontrada')
    pag, y_ini, W, H, ls = achado
    a, b = limites(ls, y_ini, H, W)
    a = y_topo if y_topo is not None else a - 6
    b = y_base if y_base is not None else b - 4
    x0 = x_esq if x_esq is not None else 24
    x1 = x_dir if x_dir is not None else W - 24
    png = render(pdf, pag, DPI)
    tam = cortar(png, x0, a, x1, b, destino, escala=DPI / 72)
    os.remove(png)
    return pag, tam


if __name__ == '__main__':
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument('pdf')
    ap.add_argument('qid')
    ap.add_argument('destino')
    ap.add_argument('--ytopo', type=float)
    ap.add_argument('--ybase', type=float)
    ap.add_argument('--xesq', type=float)
    ap.add_argument('--xdir', type=float)
    a = ap.parse_args()
    pag, tam = figura(a.pdf, 0, a.qid, a.destino, a.ytopo, a.ybase, a.xesq, a.xdir)
    print(f'página {pag} -> {a.destino} {tam[0]}x{tam[1]}')