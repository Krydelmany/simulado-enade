"""Extração de texto do PDF com coluna, fonte e recuo preservados.

Usa `mutool draw -F stext`, que entrega cada caractere com posição E com a
fonte usada. Isso resolve três coisas que o pdftotext estraga:

1. **colunas** — as provas têm corpo em 1 ou 2 colunas; o texto tem de sair na
   ordem de leitura, senão o enunciado de uma questão se mistura com o da
   vizinha;
2. **código** — fonte monoespaçada (Courier/Consolas) vira bloco indentado, e
   em código a indentação é sintaxe, não formatação;
3. **fonte quebrada** — 2014 e 2017 embutem fonte sem ToUnicode; aí o stext
   também não salva e o caminho é OCR (ocr.py), que entrega o mesmo esquema.
"""

import html
import re
import subprocess
import unicodedata

PAGE_RE = re.compile(r'<page id="[^"]*" width="([\d.]+)" height="([\d.]+)">')
BLOCK_RE = re.compile(r'<block bbox="([\d.\s-]+)">(.*?)</block>', re.S)
LINE_RE = re.compile(r'<line bbox="([\d.\s-]+)"[^>]*>(.*?)</line>', re.S)
FONT_RE = re.compile(r'<font name="([^"]+)" size="([\d.]+)"[^>]*>(.*?)</font>', re.S)
# c="..." pode conter &quot; etc.? não, mas sim caracteres escapados; o
# atributo é o ÚLTIMO da tag, então casamos até o fechamento.
CHAR_RE = re.compile(r'<char\s+quad="([^"]+)"[^>]*?\bc="((?:[^"])*)"', re.S)

MONO = re.compile(r'courier|consolas|mono|menlo|couriernew', re.I)


def _num(s):
    try:
        return float(s)
    except ValueError:
        return 0.0


def _desentidade(c):
    """stext escapa como &#xe7; (hex minúsculo) ou &#231; — normaliza."""
    if c.startswith('&#'):
        corpo = c.lstrip('#&').rstrip(';')
        if corpo[:1] in ('x', 'X'):
            corpo = corpo[1:]
        try:
            return chr(int(corpo, 16))
        except ValueError:
            return c
    return html.unescape(c)


def ler_stext(pdf):
    """-> [(W, H, [[linha, ...], ...])] por página.

    linha = (y, x0, x1, [(x, texto, mono), ...])  — texto já com espaços
    deduzidos a partir das coordenadas.
    """
    xml = subprocess.run(
        ['mutool', 'draw', '-F', 'stext', '-o', '-', pdf],
        capture_output=True,
    ).stdout.decode('utf-8', 'replace')

    partes = [(m.start(), m.end(), _num(m.group(1)), _num(m.group(2)))
              for m in PAGE_RE.finditer(xml)]

    paginas = []
    for i, (ini, fim, W, H) in enumerate(partes):
        fim_txt = partes[i + 1][0] if i + 1 < len(partes) else len(xml)
        trecho = xml[fim:fim_txt]
        brutos = []
        for bi, bm in enumerate(BLOCK_RE.finditer(trecho)):
            bx = [_num(v) for v in bm.group(1).split()]
            for lm in LINE_RE.finditer(bm.group(2)):
                ly = [_num(v) for v in lm.group(1).split()]
                y = (ly[1] + ly[3]) / 2 if len(ly) > 3 else ly[1]
                chars = []
                for fm in FONT_RE.finditer(lm.group(2)):
                    mono = bool(MONO.search(fm.group(1)))
                    for cm in CHAR_RE.finditer(fm.group(3)):
                        q = [_num(v) for v in cm.group(1).split()]
                        chars.append((q[0], _desentidade(cm.group(2)), mono))
                if chars:
                    # bx0 do bloco é a coluna; sem isso, duas colunas com a
                    # mesma altura viram uma linha só (o stext une as duas).
                    brutos.append((y, min(c[0] for c in chars), chars,
                                   bx[0] if bx else 0.0))

        # o PDF quebra UMA linha visual em vários <line> (recuo vira outro
        # <line>) -> junta por y DENTRO DA MESMA COLUNA
        grupos = []
        brutos.sort(key=lambda b: (b[3], b[0], b[1]))
        for y, x0, chars, col in brutos:
            if grupos and abs(grupos[-1][0] - y) <= 3.0 and abs(grupos[-1][4] - col) < 5.0:
                grupos[-1][1].extend(chars)
                grupos[-1][3] = min(grupos[-1][3], y)
            else:
                grupos.append([y, list(chars), x0, y, col])

        # margem de referência p/ o recuo do código: a coluna mais à esquerda
        # entre as linhas monoespaçadas da página (o corpo do texto pode ser
        # mais recuado que o código e zeraria a conta)
        x_mono = [
            min(c[0] for c in chars if c[1].strip())
            for _y, chars, _x, _y2, _col in grupos
            if chars and any(c[2] for c in chars) and any(c[1].strip() for c in chars)
        ]
        margem = min(x_mono) if x_mono else 0.0

        linhas = []
        for y, chars, _x0, _y2, _col in grupos:
            chars.sort(key=lambda c: c[0])
            texto, mono = _monta_texto(chars, margem)
            xmin = min(c[0] for c in chars)
            xmax = max(c[0] for c in chars)
            linhas.append((y, xmin, xmax, chars, texto, mono))

        linhas.sort(key=lambda l: (l[0], l[1]))
        paginas.append((W, H, linhas))
    return paginas


def _largura_mono(chars):
    """Largura de um caractere na fonte monoespaçada (mediana dos passos)."""
    passos = [chars[i + 1][0] - chars[i][0]
              for i in range(len(chars) - 1)
              if chars[i][1] != ' ' and chars[i + 1][1] != ' ']
    if not passos:
        return 0.0
    passos.sort()
    return passos[len(passos) // 2]


def _monta_texto(chars, margem=None):
    """Concatena na ordem x. Em fonte monoespaçada, um vão na horizontal
    significa espaço perdido na extração — e em código recuo é sintaxe, então
    o vão é reconstruído (o PDF emite parte dos espaços e "some" com o resto).
    """
    chars = sorted(chars, key=lambda c: c[0])
    texto = ''.join(c[1] for c in chars)
    mono_tudo = all(m for _x, _c, m in chars if _c.strip())

    if mono_tudo and len(chars) > 3:
        larg = _largura_mono(chars)
        if larg > 0.5:
            # recuo = quantas colunas o primeiro caractereNAL ocupa
            primeiro = next((c for c in chars if c[1].strip()), None)
            if primeiro and margem:
                col = round((primeiro[0] - margem) / larg)
                if col > 0:
                    texto = ' ' * col + texto.lstrip()
    return texto, mono_tudo


def _colunas(W, linhas):
    """-> [(x0, x1)] — 1 ou 2 faixas.

    Decide pelo corpo da página, não pelo cabeçalho/rodapé: o "*R09201917*"
    fica no alto à direita e atravessa o meio, mas não significa que a página
    seja de uma coluna só.
    """
    if not linhas:
        return [(0, W)]
    meio = W / 2
    # descarta cabeçalho e rodapé (10% de cima e de baixo)
    ys = sorted(l[0] for l in linhas)
    if len(ys) < 6:
        return [(0, W)]
    y0, y1 = ys[0], ys[-1]
    altura = y1 - y0 or 1.0
    corpo = [l for l in linhas if y0 + 0.06 * altura <= l[0] <= y1 - 0.06 * altura]
    if len(corpo) < 4:
        corpo = linhas

    for l in corpo:
        if l[1] < meio * 0.88 and l[2] > meio * 1.12:
            return [(0, W)]          # algo atravessa -> página de 1 coluna
    esq = [l for l in corpo if l[1] < meio * 0.92]
    dir_ = [l for l in corpo if l[1] >= meio * 0.92]
    if not esq or not dir_:
        return [(0, W)]
    return [(0, meio), (meio, W)]


def texto(pdf, pular=None):
    """-> texto com marcação de código: linhas mono vêm prefixadas por \x00."""
    paginas = ler_stext(pdf)
    out = []
    for idx, (W, H, linhas) in enumerate(paginas, 1):
        if pular and idx in pular:
            continue
        cols = _colunas(W, linhas)
        grupos = [linhas] if len(cols) == 1 else [
            [l for l in linhas if cols[0][0] <= l[1] < cols[0][1]],
            [l for l in linhas if l[1] >= cols[1][0]],
        ]
        for g in grupos:
            for l in g:
                marca = '\x00' if l[5] else ''
                out.append(marca + (l[4].rstrip() if marca else l[4].strip()))
            out.append('')
    return '\n'.join(out)


# --- limpeza de artefatos --------------------------------------------------

LIXO = [
    # cabeçalho/rodapé: *R09201917*, "16 ENGENHARIA DE COMPUTAÇÃO",
    # "ENGENHARIA DE COMPUTAÇÃO 29" (o nº da página cola no texto),
    # "Área livre", número de página solto
    re.compile(r'^\*?\s*R\d{4}\s*\d+\s*\*?$'),
    re.compile(r'^\s*\d{0,3}\s*ENGENHARIA\s+DE\s+COMPUTA[ÇC][ÃA]O\s*\d{0,3}\s*$', re.I),
    re.compile(r'^\s*[ÁA]rea\s+livre\s*$', re.I),
    re.compile(r'^\s*\d{1,3}\s*$'),
    re.compile(r'^\s*(?:Novembro\s*\|\s*)?\d{4}\s*$'),
    re.compile(r'^\s*de\s+Computational\b.*$', re.I),
]


def limpar(txt):
    linhas = []
    for ln in txt.split('\n'):
        s = ln.rstrip()
        if any(rx.match(s) for rx in LIXO):
            s = ''
        if s:
            linhas.append(s)
    txt = '\n'.join(linhas)
    # URL quebrada no meio (".../noticia/" + "2019/03/15/...")
    conserta = re.compile(r'(https?://[^\s]*/)\n([^\s]+)')
    for _ in range(4):
        novo = conserta.sub(lambda m: m.group(1) + m.group(2), txt)
        if novo == txt:
            break
        txt = novo
    return txt


def normaliza(txt):
    """NFC + colapsa espaço RUNNING, preservando o recuo de código.

    Cuidado: o recuo reconstruído em código são espaços iniciais;
    colapsar tudo vira 1 espaço e o Java/Python perde a estrutura.
    """
    txt = unicodedata.normalize('NFC', txt)
    saida = []
    for ln in txt.split('\n'):
        if ln.startswith('\x00'):
            saida.append('\x00' + re.sub(r'[ \t]+', ' ', ln[1:]).rstrip())
        else:
            saida.append(re.sub(r'[ \t]+', ' ', ln).rstrip())
    return '\n'.join(saida)


def tem_codigo(txt):
    return '\x00' in txt