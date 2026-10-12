"""Extração de texto do PDF com coluna e recuo preservados.

A camada de texto é lida com `pdftotext -bbox-layout`: o poppler entrega cada
PALAVRA com a sua caixa E o texto já decodificado certo. Isso resolve duas
coisas que o `pdftotext` puro estraga:

1. **colunas** — as provas têm corpo em 1 ou 2 colunas; no modo comum o texto
   sai na ordem visual e o enunciado de uma questão se mistura com o da
   vizinha;
2. **código** — a fonte monoespaçada é reconhecida pelo advance uniforme dos
   caracteres, e o recuo (que o PDF emite só pela metade) é reconstruído a
   partir do vão horizontal.

O `mutool draw -F stext` também entrega posição, mas erra caracteres com
frequência nesse acervo ("Criptografai", "of-fthe-shelf", "sofwtare") e esses
erros iam parar no enunciado das questões.

2014 e 2017 embutem fonte sem ToUnicode — aí nem o poppler salva e o caminho
é OCR (ver ocr.py), que entrega o mesmo esquema.
"""

import html
import re
import subprocess
import unicodedata

# Saída do `pdftotext -bbox-layout` (XHTML do poppler).
PAGE_RE = re.compile(r'<page width="([\d.]+)" height="([\d.]+)"')
BLOCK_RE = re.compile(
    r'<block xMin="([-.\d]+)" yMin="([-.\d]+)" xMax="([-.\d]+)" yMax="([-.\d]+)">'
    r'(.*?)</block>',
    re.S,
)
LINE_RE = re.compile(
    r'<line xMin="([-.\d]+)" yMin="([-.\d]+)" xMax="([-.\d]+)" yMax="([-.\d]+)">'
    r'(.*?)</line>',
    re.S,
)
# <word xMin=.. yMin=.. xMax=.. yMax=..>TEXTO</word>
WORD_RE = re.compile(
    r'<word xMin="([-.\d]+)" yMin="([-.\d]+)" xMax="([-.\d]+)" yMax="([-.\d]+)">'
    r'([^<]*)</word>'
)


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

    A FONTE DO TEXTO é o `pdftotext -bbox-layout`, não o `mutool`. Os dois
    entregam palavra com posição, mas o mutool erra caracteres com
    frequência nesse acervo: devolve "Criptografai", "of-fthe-shelf",
    "inflitração", "sofwtare" — erros que vão parar no enunciado das
    questões. O poppler lê a camada de texto corretamente (os PDFs de 2019 e
    2023 saem 100% corretos), então o miolho de fazer a leitura de coluna aqui
    em cima é do poppler.

    linha = (y, x0, x1, [(x, texto, mono), ...])
    """
    xml = subprocess.run(
        ['pdftotext', '-bbox-layout', pdf, '-'],
        capture_output=True,
    ).stdout.decode('utf-8', 'replace')

    partes = [
        (m.start(), m.end(), _num(m.group(1)), _num(m.group(2)))
        for m in PAGE_RE.finditer(xml)
    ]

    paginas = []
    for i, (ini, fim, W, H) in enumerate(partes):
        fim_txt = partes[i + 1][0] if i + 1 < len(partes) else len(xml)
        trecho = xml[fim:fim_txt]
        brutos = []
        for bi, bm in enumerate(BLOCK_RE.finditer(trecho)):
            bx = [_num(v) for v in bm.group(1).split()]
            for lm in LINE_RE.finditer(bm.group(5)):
                ly = [_num(v) for v in lm.group(1, 2, 3, 4)]
                y = (ly[1] + ly[3]) / 2 if len(ly) > 3 else ly[1]
                palavras = WORD_RE.findall(lm.group(5))
                if not palavras:
                    continue
                chars = [
                    (
                        _num(w[0]),
                        _num(w[1]),        # yMin, só para ordenar depois
                        _num(w[2]),
                        _num(w[3]),
                        html.unescape(w[4]).strip(),
                    )
                    for w in palavras
                ]
                chars = [c for c in chars if c[4]]
                if chars:
                    # bx0 do bloco é a coluna; sem isso, duas colunas com a
                    # mesma altura viram uma linha só.
                    brutos.append((y, min(c[0] for c in chars), chars,
                                   bx[0] if bx else 0.0))

        # o PDF quebra UMA linha visual em vários <line> (o recuo da
        # monoespaçada vira outro <line>) -> junta por y DENTRO DA COLUNA
        grupos = []
        brutos.sort(key=lambda b: (b[3], b[0], b[1]))
        for y, x0, chars, col in brutos:
            if grupos and abs(grupos[-1][0] - y) <= 3.0 and abs(grupos[-1][4] - col) < 5.0:
                grupos[-1][1].extend(chars)
                grupos[-1][3] = min(grupos[-1][3], y)
            else:
                grupos.append([y, list(chars), x0, y, col])

        # margem de referência p/ o recuo do código: a coluna mais à esquerda
        # entre as linhas monoespaçadas da página
        x_mono = [
            min(c[0] for c in chars if c[4])
            for _y, chars, _x, _y2, _col in grupos
            if chars and c_monospace(chars)
        ]
        margem = min(x_mono) if x_mono else 0.0

        linhas = []
        for y, chars, _x0, _y2, _col in grupos:
            # O poppler JÁ entrega as palavras na ordem de leitura dentro do
            # <line>; reordenar por x ou por y embaralha: a bolinha da
            # alternativa (glifo circular maior) tem y levemente diferente e
            # sai para o fim. A posição no <line> é a única ordem confiável.
            chars = _ordena_por_x(chars)
            mono = c_monospace(chars)
            _ = margem
            texto = _junta_palavras(chars)
            xmin = min(c[0] for c in chars)
            xmax = max(c[2] for c in chars)
            linhas.append((y, xmin, xmax, chars, texto, mono))
        linhas.sort(key=lambda l: (l[0], l[1]))
        paginas.append((W, H, linhas))
    return paginas


def c_monospace(chars):
    """O poppler -bbox não diz a fonte; linhas de código são as que, com a
    mesma altura, têm passos horizontais uniformes."""
    passos = [
        chars[i + 1][0] - chars[i][0]
        for i in range(len(chars) - 1)
        if chars[i][4] != ' ' and chars[i + 1][4] != ' '
    ]
    if len(passos) < 6:
        return False
    ordenados = sorted(passos)
    mediana = ordenados[len(ordenados) // 2]
    if mediana <= 0:
        return False
    return (ordenados[-1] - ordenados[0]) / mediana < 0.35


def _ordena_por_x(chars):
    """Ordena da esquerda para a direita, com tolerância para o caso de a
    bolinha vir ANTES da palavra mas com x ligeiramente menor."""
    return sorted(chars, key=lambda c: c[0])


def _para_triplas(chars):
    """(x, texto, mono) de (x, y, x1, y1, texto) do poppler."""
    return [(c[0], c[4], False) for c in chars]


def _dedup_espaco(chars):
    """Remove espaços que não são espaço.

    O poppler às vezes emite o espaço de recuo na MESMA coordenada x do
    caractere seguinte (o glifo tem deslocamento). Espaço de verdade anda
    alguns pontos; x igual é artefato.
    """
    saida = []
    for i, c in enumerate(chars):
        if c[1] == ' ':
            prox = chars[i + 1] if i + 1 < len(chars) else None
            if prox and abs(prox[0] - c[0]) < 0.5:
                continue
        saida.append(c)

    # ligadura: a Calibri liga "fi" num glyph só, e o mutool emite o glyph
    # partido em DOIS caracteres na MESMA posição (delta 0). O espaço do
    # mutool entre os dois é o que produz "af irma".
    corrigido = []
    for c in saida:
        if corrigido and abs(c[0] - corrigido[-1][0]) < 0.5 and c[1] != ' ':
            anterior = corrigido.pop()
            # junta as letras; se entre elas havia espaço, ele era artefato
            if len(corrigido) and corrigido[-1][1] == ' ':
                # espaço real antes da ligadura? (ex.: "o fi") -> mantém
                corrigido.pop()
            corrigido.append((anterior[0], anterior[1] + c[1], anterior[2]))
            continue
        corrigido.append(c)
    return corrigido


def _junta_palavras(palavras):
    """palavras (x0,y0,x1,y1,texto) -> texto com espaços.

    O poppler devolve cada palavra com a caixa, sem os espaços entre elas —
    então o espaço é deduzido do vão: se a próxima palavra começa bem depois
    do fim da anterior, é uma palavra nova; se encosta, é a mesma.
    """
    out = ''
    fim = None
    for x0, _y0, x1, _y1, txt in palavras:
        if fim is None:
            out = txt
        else:
            vao = x0 - fim
            alt = _y1 - _y0 or 1.0
            # O poppler não marca os espaços, mas ele ENTREGA cada palavra
            # separada. O vão entre duas palavras é ~0.2-0.3 da altura da
            # linha; entre dígitos soltos ("QUESTÃO" + "01") é o mesmo, então
            # usamos a altura: um espaço de verdade é ~1/4 da altura do texto.
            if vao > 0.10 * alt and not out.endswith(' '):
                out += ' '
            out += txt
        fim = x1
    return out


def _monta_texto(chars, margem=None):
    """Concatena na ordem x. Em fonte monoespaçada, um vão na horizontal
    significa espaço perdido na extração — e em código recuo é sintaxe, então
    o vão é reconstruído (o PDF emite parte dos espaços e "some" com o resto).
    """
    chars = _dedup_espaco(sorted(chars, key=lambda c: c[0]))
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


def _colunas(W, linhas, pdf=None, pagina=None):
    """-> [(x0, x1)] — 1 ou 2 faixas.

    O sinal mais firme não é a densidade de tinta: são os CABEÇALHOS das
    questões. Duas caixas "QUESTÃO" na mesma altura = página de 2 colunas; uma
    caixa só (mesmo com tabela e figura ao lado) = 1 coluna. Quando dá para
    consultar o PDF, é o que a gente usa.
    """
    if not linhas:
        return [(0, W)]

    if pdf and pagina and _duas_colunas_por_questoes(pdf, pagina):
        return [(0, W / 2), (W / 2, W)]

    meio = W / 2
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
            return [(0, W)]
    esq = [l for l in corpo if l[1] < meio * 0.92]
    dir_ = [l for l in corpo if l[1] >= meio * 0.92]
    if not esq or not dir_:
        return [(0, W)]
    return [(0, meio), (meio, W)]


def _duas_colunas_por_questoes(pdf, pagina):
    """-> bool: a página tem 2 questões lado a lado (mesma altura, x distintos)."""
    r = subprocess.run(
        ['pdftotext', '-bbox', '-f', str(pagina), '-l', str(pagina), pdf, '-'],
        capture_output=True,
    )
    s = r.stdout.decode('utf-8', 'replace')
    achados = [
        (float(m.group(2)), float(m.group(1)))
        for m in re.finditer(
            r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="[\d.]+" yMax="[\d.]+">'
            r'QUEST[^<]*</word>',
            s,
        )
    ]
    if len(achados) < 2:
        return False
    alturas = {}
    for y, x in achados:
        alturas.setdefault(round(y / 6), []).append(x)
    return any(len(v) >= 2 for v in alturas.values())


def texto(pdf, pular=None):
    """-> texto com marcação de código: linhas mono vêm prefixadas por \x00."""
    paginas = ler_stext(pdf)
    out = []
    for idx, (W, H, linhas) in enumerate(paginas, 1):
        if pular and idx in pular:
            continue
        cols = _colunas(W, linhas, pdf, idx)
        if len(cols) == 1:
            grupos = [linhas]
        else:
            # Separa por x0 ANTES: uma linha pode ter palavras dos dois lados
            # (a que se estende do enunciado ate as alternativas), e ai não é
            # a coluna que manda — é a linha inteira.
            # Separa por PALAVRA, não por linha: uma linha justificada pode
            # atravessar o meio (o enunciado de uma questão estourando a
            # margem), e aí a linha inteira pertence à coluna esquerda —
            # mas a alternativa que começa logo à direita do meio é da
            # questão vizinha e tem de ir com ela.
            meio = W / 2
            por_palavra = [{}, {}]
            for l in linhas:
                for c in l[3]:
                    d = por_palavra[0 if c[0] < meio else 1]
                    chave = id(l)
                    d.setdefault(chave, [l, []])
                    d[chave][1].append(c)
            grupos = []
            for d in por_palavra:
                if not d:
                    grupos.append([])
                    continue
                reconst = []
                for linha, palavras in d.values():
                    palavras = sorted(palavras, key=lambda c: c[0])
                    xmin = min(c[0] for c in palavras)
                    xmax = max(c[2] for c in palavras)
                    reconst.append((linha[0], xmin, xmax, palavras,
                                    _junta_palavras(palavras), False))
                reconst.sort(key=lambda l: l[0])
                grupos.append(reconst)
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
    # carimbo do arquivo impresso: "VALIDINEP2023VALIDINEP2023..." (a marca d'
    # água sai colada na última linha da página)
    re.compile(r'^\s*(?:VALIDINEP\d{4}|\[MARCA\'D.?[ÁA]GUA\]|[A-Z]{3,}\d{4})[A-Z0-9\s]*$', re.I),
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


def _arruma_questao(txt):
    """O poppler junta "QUESTÃO" + "01" sem espaço quando eles são uma
    palavra só na caixa dele: "QUESTÃO01"."""
    return re.sub(r'QUEST(?:Ã|A)O(?=\d)', 'QUESTÃO ', txt)


def normaliza(txt):
    """NFC + colapsa espaço RUNNING, preservando o recuo de código.

    Cuidado: o recuo reconstruído em código são espaços iniciais;
    colapsar tudo vira 1 espaço e o Java/Python perde a estrutura.
    """
    txt = unicodedata.normalize('NFC', txt)
    txt = _arruma_questao(txt)
    saida = []
    for ln in txt.split('\n'):
        if ln.startswith('\x00'):
            saida.append('\x00' + re.sub(r'[ \t]+', ' ', ln[1:]).rstrip())
        else:
            saida.append(re.sub(r'[ \t]+', ' ', ln).rstrip())
    return '\n'.join(saida)


def tem_codigo(txt):
    return '\x00' in txt