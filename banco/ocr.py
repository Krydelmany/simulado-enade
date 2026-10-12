"""OCR das provas com fonte quebrada (2014 e 2017).

O PDF traz fonte embutida sem ToUnicode, então o pdftotext devolve glifos
trocados ("ĚĞ" no lugar de "da"). Aqui a página é renderizada e o tesseract
devolve as palavras COM COORDENADA — o mesmo esquema que o layout.py usa —
o que permite remontar as colunas na ordem de leitura.
"""

import json
import os
import re
import subprocess
import sys

SAIDA = '/tmp/opencode/extr/ocr'


def render(pdf, pag, dpi=300):
    base = f'{SAIDA}/p{pag}'
    subprocess.run(
        ['pdftoppm', '-r', str(dpi), '-f', str(pag), '-l', str(pag), '-gray',
         '-png', '-singlefile', pdf, base],
        check=True,
        capture_output=True,
    )
    return base + '.png'


def ocr(png, lang='por', psm='3'):
    """-> [(x0,y0,x1,y1,palavra,conf)] via saida TSV."""
    r = subprocess.run(
        ['tesseract', png, 'stdout', '-l', lang, '--psm', psm, 'tsv'],
        capture_output=True,
    )
    txt = r.stdout.decode('utf-8', 'replace')
    out = []
    for ln in txt.split('\n'):
        c = ln.split('\t')
        if len(c) < 12:
            continue
        if c[0] != '5':          # so level word
            continue
        try:
            x, y, w, h, conf = int(c[6]), int(c[7]), int(c[8]), int(c[9]), float(c[10])
        except ValueError:
            continue
        pal = c[11].strip()
        if not pal or conf < 40:
            continue
        out.append((x, y, x + w, y + h, _corrige(pal), conf))
    return out


# O tesseract lê a bolinha da alternativa ("A)" / "(A") como "O" — o desenho é
# idêntico ao glifo da letra O maiúscula. Aqui a bolinha vira a letra.
def _corrige(pal):
    # bolinha da alternativa ("(A)" vira "(O") -> marcador
    if pal in ('(O', 'O)', 'O)'):
        return '[LETRA]'
    return pal


def montar(palavras, W, H):
    """-> texto na ordem de leitura, respeitando 1 ou 2 colunas.

    O tesseract devolve a página em Z (topo,baixo,topo,baixo...) e mistura as
    colunas quando as linhas caem na mesma altura. Aqui as linhas são
    montadas por y e a página é partida em colunas ANTES de concatenar.
    """
    if not palavras:
        return ''
    meio = W / 2

    # 1) monta as linhas (tolerance proportional à altura da página)
    tol = max(2, int(H * 0.004))
    ordenadas = sorted(palavras, key=lambda w: ((w[1] + w[3]) / 2, w[0]))
    linhas = []          # [y, x0, x1, [palavras]]
    for w in ordenadas:
        y = (w[1] + w[3]) / 2
        if linhas and abs(linhas[-1][0] - y) <= tol:
            linhas[-1][3].append(w)
            linhas[-1][2] = max(linhas[-1][2], w[2])
            linhas[-1][0] = (linhas[-1][0] * (len(linhas[-1][3]) - 1) + y) / len(linhas[-1][3])
        else:
            linhas.append([y, w[0], w[2], [w]])
    for l in linhas:
        l[3].sort(key=lambda w: w[0])

    # 2) 2 colunas? nenhuma palavra cruzando o meio
    cruza = any(l[1] < meio * 0.85 and l[2] > meio * 1.15 for l in linhas)
    tem_esq = any(l[1] < meio * 0.8 for l in linhas)
    tem_dir = any(l[1] >= meio * 0.9 for l in linhas)
    duas = (not cruza) and tem_esq and tem_dir

    def linha_txt(l):
        return ' '.join(w[4] for w in l[3])

    if duas:
        partes_txt = []
        for pred in (lambda x: x < meio, lambda x: x >= meio):
            partes_txt.append([linha_txt(l) for l in linhas if pred(l[1])])
    else:
        partes_txt = [[linha_txt(l) for l in linhas]]

    return '\n'.join('\n'.join(_marca_bolinhas(p)) for p in partes_txt)


BOLINHA = '[LETRA]'

# OCR da bolinha varies conforme a fonte: A) -> "O", B) -> "4"/"B", C) -> "OQ".
# Normalizamos para o mesmo marcador.
BOLINHA_VARIANTES = re.compile(
    r'^(?:\(|\[)?(?:O|OQ|QO|0|4|8|9|1|2|3|5|6|7)(?:\)|\])?(?=\s|$)'
)


def _marca_bolinhas(linhas_txt):
    """Troca a bolinha inicial (lida como 'O') pelo marcador da alternativa.

    O tesseract não distingue a bolinha da letra O — mesmo desenho. A
    assinatura é o CONJUNTO: alternativas sempre vêm em 4 ou 5 linhas
    consecutivas que começam com 'O'. Uma frase normal ("O gestor de um
    hotel...") vem sozinha e é deixada intacta.
    """
    cand = [i for i, t in enumerate(linhas_txt) if _comeca_bolinha(t)]
    if len(cand) < 4:
        return linhas_txt

    marcados = set()
    for i in range(len(cand) - 3):
        grupo = cand[i:i + 4]
        if grupo[-1] - grupo[0] <= 8:          # 4 bolinhas coladas
            marcados.update(grupo)
        if i + 4 < len(cand) and cand[i + 4] - grupo[0] <= 12:
            marcados.update(cand[i:i + 5])     # 5 bolinhas (com 1 linha entre)

    for i in marcados:
        linhas_txt[i] = BOLINHA + BOLINHA_VARIANTES.sub('', linhas_txt[i], count=1)
    return linhas_txt


def _comeca_bolinha(t):
    return bool(BOLINHA_VARIANTES.match(t.strip()))


def processar(pdf, nome, paginas=None, dpi=300):
    os.makedirs(SAIDA, exist_ok=True)
    info = subprocess.run(['pdfinfo', pdf], capture_output=True).stdout.decode()
    m = re.search(r'Pages:\s+(\d+)', info)
    total = int(m.group(1)) if m else 0
    if paginas:
        total = max(paginas)
    partes = []
    for p in range(1, total + 1):
        png = render(pdf, p, dpi)
        palavras = ocr(png)
        from PIL import Image  # noqa
        with Image.open(png) as im:
            W, H = im.size
        txt = montar(palavras, W, H)
        partes.append(txt)
        os.remove(png)
        print(f'  {nome} p{p}/{total} ok ({len(txt)} car.)', flush=True)
    return '\n'.join(partes)


if __name__ == '__main__':
    base = '/root/enade-simulado/fontes/'
    for nome, arq in (('2014', '2014-e1_prova.pdf'), ('2017', '2017-e1_prova.pdf')):
        print(f'== OCR {nome} ==', flush=True)
        t = processar(base + arq, nome)
        with open(f'{SAIDA}/{nome}-ocr.txt', 'w', encoding='utf-8') as fh:
            fh.write(t)
        print(f'== {nome} pronto ==', flush=True)