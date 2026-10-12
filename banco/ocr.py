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


def ocr(png, lang='por', psm='3'):  # noqa: ARG001
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


# "ÁREA LIVRE" é o rótulo do espaço de resposta da prova; o tesseract cola a
# bolinha da alternativa seguinte nele ("ÁREA LIVRE E somente L2 ficará…").
LIXO_OCR = re.compile(
    r'^(?:[ÁA]REA\s+LIVRE|ENGENHARIA\s+DE\s+COMPUTA[ÇC][ÃA]O|EXAME\s+NACIONAL.*|ENADE\s+\d{4}'
    r'|\*\s*R\d.*|[A-Z]{3,}\d{4}[A-Z0-9\s]*)$',
    re.I,
)


def _limpa_lixo(t):
    t = re.sub(r'\s*\b[ÁA]REA\s+LIVRE\b\s*', ' ', t, flags=re.I)
    t = re.sub(r'\s*\bENGENHARIA\s+DE\s+COMPUTA[ÇC][ÃA]O\s*\d*\s*', ' ', t, flags=re.I)
    t = re.sub(r'\s*\*\s*R[\d ]+\*?\s*', ' ', t)
    t = re.sub(r'\s*(?:VALIDINEP\d{4}|[A-Z]{3,}\d{4})[A-Z0-9\s]*$', '', t)
    return ' '.join(t.split())


def _agrupar(palavras, tol):
    """Palavras -> linhas por altura."""
    linhas = []
    for w in sorted(palavras, key=lambda w: ((w[1] + w[3]) / 2, w[0])):
        y = (w[1] + w[3]) / 2
        if linhas and abs(linhas[-1][0] - y) <= tol:
            linhas[-1][1].append(w)
            linhas[-1][2] = max(linhas[-1][2], w[2])
        else:
            linhas.append([y, [w], w[2]])
    for l in linhas:
        l[1].sort(key=lambda w: w[0])
    return linhas


_BBOX_CACHE = {}


def _blocos(pdf, pagina):
    """Caixas dos blocos de uma página, via pdftotext -bbox-layout.

    Funciona mesmo com a fonte quebrada (o poppler lê a geometria, não o
    texto), então serve para 2014/2017 também.
    """
    chave = (pdf, pagina)
    if chave in _BBOX_CACHE:
        return _BBOX_CACHE[chave]
    r = subprocess.run(
        ['pdftotext', '-bbox-layout', '-f', str(pagina), '-l', str(pagina), pdf, '-'],
        capture_output=True,
    )
    s = r.stdout.decode('utf-8', 'replace')
    W = float(re.search(r'<page width="([\d.]+)"', s).group(1)) if re.search(r'<page width="([\d.]+)"', s) else 0
    bs = [
        tuple(float(v) for v in b)
        for b in re.findall(
            r'<block xMin="([\d.-]+)" yMin="([\d.-]+)" xMax="([\d.-]+)" yMax="([\d.-]+)">', s
        )
    ]
    _BBOX_CACHE[chave] = (W, bs)
    return _BBOX_CACHE[chave]


def _cabecalhos(pdf, pagina):
    """-> [(x0, y0, x1, y1)] das caixas 'QUESTÃO' numa página."""
    W, _ = _blocos(pdf, pagina)
    r = subprocess.run(
        ['pdftotext', '-bbox', '-f', str(pagina), '-l', str(pagina), pdf, '-'],
        capture_output=True,
    )
    s = r.stdout.decode('utf-8', 'replace')
    achados = []
    palavras = re.finditer(
        r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(QUEST[^<]*)</word>',
        s,
    )
    for m in palavras:
        achados.append(tuple(float(m.group(i)) for i in (1, 2, 3, 4)))
    return W, achados


def _duas_colunas_por_questoes(pdf, pagina):
    W, cabs = _cabecalhos(pdf, pagina)
    if not W or len(cabs) < 2:
        return False
    por_linha = {}
    for x0, y0, x1, y1 in cabs:
        chave = round(y0 / (H_TOL := 6))
        por_linha.setdefault(chave, []).append(x0)
    # 2+ cabeçalhos na mesma altura -> colunas
    return any(len(v) >= 2 for v in por_linha.values())


def _duas_colunas_por_blocos(pdf, pagina, min_largura_frac=0.30):
    """-> bool: a página tem 2 colunas de TEXTO (não é tabela)."""
    W, bs = _blocos(pdf, pagina)
    if not W:
        return False
    # Assinatura de página em 2 colunas: existem blocos COMEÇANDO na margem
    # esquerda (x ~ 8% da largura) E blocos começando na margem da segunda
    # coluna (x ~ 51%). Numa página de 1 coluna (mesmo com tabela), todo
    # bloco nasce na margem esquerda.
    MARGEM_E, MARGEM_D = W * 0.08, W * 0.47
    tol = W * 0.04
    esq = [b for b in bs if abs(b[0] - MARGEM_E) < tol]
    dir_ = [b for b in bs if abs(b[0] - MARGEM_D) < tol]
    return len(esq) >= 2 and len(dir_) >= 2


def montar(palavras, W, H, pdf=None, pagina=None):
    """-> texto na ordem de leitura, respeitando 1 ou 2 colunas.

    O tesseract devolve a página em Z (topo,baixo,topo,baixo...). Duas
    colunas com linhas na MESMA altura viram uma linha só se forem agrupadas
    antes de separar — por isso a coluna é decidida ANTES do agrupamento.
    """
    if not palavras:
        return ''
    meio = W / 2
    tol = max(2, int(H * 0.004))

    # 1) decide a coluna pelo centroid de x, olhando o corpo da página
    ys = sorted(((w[1] + w[3]) / 2 for w in palavras))
    y0, y1 = ys[0], ys[-1]
    altura = y1 - y0 or 1.0
    corpo = [
        w for w in palavras
        if y0 + 0.06 * altura <= (w[1] + w[3]) / 2 <= y1 - 0.06 * altura
    ] or palavras
    # Uma TABELA (com 2 colunas de dados) também tem palavras dos dois lados
    # do meio, mas NÃO é página de 2 colunas. A diferença: na página de 2
    # colunas existe uma FAIXA VERTICAL vazia no meio (gap de ~1 caractere ou
    # mais em TODA a altura do corpo). Numa tabela, as palavras se encostam.
    # A geometria do PDF decide, não a densidade do OCR. O sinal é simples e
    # não ambíguo: o pdftotext -bbox funciona mesmo com a fonte quebrada (ele
    # lê a caixa, não o texto) e devolve uma caixa "QUESTÃO" SEPARADA para
    # cada questão. Duas caixas na MESMA altura = página de 2 colunas; uma
    # caixa só (mesmo com tabelas e figuras ao lado) = página de 1 coluna.
    if any(w[0] < meio * 0.85 and w[2] > meio * 1.15 for w in corpo):
        duas = False
    elif pdf and pagina:
        duas = _duas_colunas_por_questoes(pdf, pagina)
    else:
        duas = False

    if not duas:
        partes = [_agrupar(palavras, tol)]
    else:
        partes = [
            _agrupar([w for w in palavras if w[0] < meio], tol),
            _agrupar([w for w in palavras if w[0] >= meio], tol),
        ]

    textos = []
    for linhas in partes:
        cru = [' '.join(w[4] for w in l[1]) for l in linhas]
        limpo = [t for t in (_limpa_lixo(t) for t in cru) if t]
        textos.append(_marca_bolinhas(limpo))
    return '\n'.join('\n'.join(t) for t in textos)


BOLINHA = '[LETRA]'

# OCR da bolinha varies conforme a fonte: A) -> "O", B) -> "4"/"B", C) -> "OQ".
# Normalizamos para o mesmo marcador.
# A bolinha da alternativa é lida de formas varieadas conforme a fonte e o
# ruído: "A)"->"O", "B)"->"4", "C)"->"OQ"/"Q", "D)"->"lell", "E)"->"|".
# O tesseract também pode devolver a bolinha SOZINHA numa linha.
BOLINHA_VARIANTES = re.compile(
    r'^(?:\(|\[)?(?:O|OQ|QO|Q0|QQ|BA|OW|OU|O[A-Z]|0|4|8|9|1|2|3|5|6|7|lell|lelll|ll)(?:\)|\])?(?=\s|$)'
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
        txt = montar(palavras, W, H, pdf, p)
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