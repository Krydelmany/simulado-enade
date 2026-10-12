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

sys.path.insert(0, '/root/enade-simulado/banco')

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
    """OCR de todas as páginas -> texto na ordem de leitura, COM as letras
    das alternativas corrigidas pela geometria do PDF."""
    import alternativas
    from PIL import Image

    os.makedirs(SAIDA, exist_ok=True)
    info = subprocess.run(['pdfinfo', pdf], capture_output=True).stdout.decode()
    m = re.search(r'Pages:\s+(\d+)', info)
    total = int(m.group(1)) if m else 0
    if paginas:
        total = max(paginas)

    seqs = alternativas.indice_por_pagina(os.path.basename(pdf))  # {pag: [grupos]}
    # O questionário de percepção da prova não pontua e tem o mesmo desenho
    # A..E; detectá-lo aqui evita gastar OCR com ele.
    percepcao = _paginas_do_questionario(pdf)
    partes = []
    for p in range(1, total + 1):
        if p in percepcao:
            partes.append('')
            continue
        png = render(pdf, p, dpi)
        with Image.open(png) as im:
            W, H = im.size
            partes.append(_pagina(png, im, W, H, dpi, seqs.get(p, []), pdf, p))
        os.remove(png)
        print(f'  {nome} p{p}/{total} ok ({len(partes[-1])} car.)', flush=True)
    return '\n'.join(partes)


def _recorte_alternativa(png, im, dpi, seq, k, x1=None, x_esq=None):
    """OCR de UMA alternativa, pela faixa entre a letra atual e a seguinte.

    A letra da alternativa é um glifo de 15.6 pt (o corpo do texto tem 12.3),
    e a caixa dela vem da geometria do PDF — que não depende de OCR. Cortando
    da base dessa caixa até a base da seguinte, cai exatamente na linha da
    alternativa: o tesseract lendo a página inteira erra a última (a bolinha
    pequena encosta no rodapé), mas lendo só a faixa acerta.
    """
    from PIL import Image

    letra, y0, y1, x0 = seq[k]
    n = len(seq)
    # A alternativa pode ocupar VÁRIAS linhas (a A da Q04 do 2014 tem 3),
    # então a faixa vai até o topo da letra seguinte. Se o passo for o
    # normal (uma linha por alternativa, ~16 pt), isso seria uma faixa
    # rasa demais — por isso o passo médio define a folga.
    if n > 1:
        passo = (seq[-1][1] - seq[0][1]) / (n - 1)
    else:
        passo = 16.0
    topo = y0 - 2
    base = seq[k + 1][1] - 3 if k + 1 < n else y0 + passo * 3.2

    escala = dpi / 72.0
    W, H = im.size
    # o x1 limita a COLUNA: em página de 2 colunas a alternativa da questão
    # vizinha está logo à direita e entrava no recorte.
    x_max = W if x1 is None else min(W, int(x1 * escala))
    esq = (x_esq if x_esq is not None else x0) - 8
    faixa = im.crop((
        max(0, int(esq * escala)),
        max(0, int(topo * escala)),
        max(int(x0 * escala) + 60, x_max),
        min(H, int(base * escala)),
    ))
    faixa = faixa.resize((faixa.width * 2, faixa.height * 2), Image.LANCZOS)
    tmp = f'{SAIDA}/_alt_{os.getpid()}_{k}.png'
    faixa.save(tmp)
    r = subprocess.run(
        ['tesseract', tmp, 'stdout', '-l', 'por', '--psm', '6'],
        capture_output=True,
    )
    os.remove(tmp)
    linhas = [l for l in r.stdout.decode('utf-8', 'replace').split('\n') if l.strip()]
    if not linhas:
        return ''
    return _tira_bolinha(max(linhas, key=lambda l: len(l.strip())))


def _paginas_do_questionario(pdf):
    import subprocess as _sp

    r = _sp.run(['pdfinfo', pdf], capture_output=True)
    m = re.search(r'Pages:\s+(\d+)', r.stdout.decode())
    total = int(m.group(1)) if m else 0
    achadas = set()
    for p in range(4, total + 1):
        t = _sp.run(
            ['pdftotext', '-f', str(p), '-l', str(p), pdf, '-'],
            capture_output=True,
        ).stdout.decode('utf-8', 'replace')
        if re.search(r'QUESTION[\u00c1\u00c3]RIO DE PERCEP[\u00c7\u00c3]\u00c3O', t, re.I):
            achadas.update(range(p, total + 1))
            break
    return achadas


def _pagina(png, im, W, H, dpi, grupos, pdf=None, pag=None):
    """Texto da página com as alternativas corrigidas.

    O OCR da página inteira acerta o texto do CORPO, mas erra a bolinha — lê
    "O" e às vezes nem a encontra. Duas saídas, combinadas:

    1. o corpo sai do OCR normal (rápido, bom);
    2. cada ALTERNATIVA sai de um recorte da faixa entre a letra atual e a
       seguinte. A letra vem da GEOMETRIA do PDF (que não depende de OCR) e
       o recorte é estreito o bastante para o tesseract não escorregar para a
       linha vizinha.

    Por que não casar por altura no texto inteiro: a ordem das colunas no
    texto e a ordem na geometria divergem, e o casamento erra a letra.
    """
    if not grupos:
        return montar(ocr(png), W, H, pdf, pag)

    texto = montar(ocr(png), W, H, pdf, pag)
    linhas = texto.split('\n')

    # na ordem em que o texto apresenta (de cima para baixo): para o corte
    # de um bloco não atrapalhar o do outro
    ordem = sorted(range(len(grupos)),
                   key=lambda i: grupos[i][0][1])
    for idx in reversed(ordem):
        seq = grupos[idx]
        novas = []
        # a coluna vai da margem do bloco até a margem do PRÓXIMO bloco
        x_esq = seq[0][3]
        if idx + 1 < len(grupos):
            x_dir = grupos[idx + 1][0][3] - 14
        else:
            x_dir = None
        if idx > 0:
            x_esq = max(0, seq[0][3] - 20)
        passo = (seq[-1][1] - seq[0][1]) / (len(seq) - 1) if len(seq) > 1 else 16.0
        # a ÚLTIMA alternativa pode ter várias linhas; o texto dela termina
        # onde começa a figura/questão seguinte. Sem limite, o recorte vaza
        # para o rodapé ("ENGENHARIA DE COMPUTAÇÃO").
        if idx + 1 < len(grupos):
            limite = min(seq[-1][2] + passo * 1.6, grupos[idx + 1][0][1] - 2)
        else:
            limite = seq[-1][2] + passo * 1.6
        for k, (letra, y0, y1, _x0) in enumerate(seq):
            topo = y0 - 2
            base = seq[k + 1][1] - 3 if k + 1 < len(seq) else limite
            alt = _tira_bolinha(
                _recorte(png, im, dpi, topo, base, x_esq, x_dir)
            )
            if alt:
                novas.append(f'[{letra}] {alt}')
        if not novas:
            continue
        i = _primeira_alternativa(linhas)
        j = _ultima_alternativa(linhas, i) if i >= 0 else 0
        linhas = (linhas[:i] if i >= 0 else linhas) + novas + linhas[j:]
    return '\n'.join(linhas)


def _recorte(png, im, dpi, y_topo, y_base, x_esq, x_dir):
    """OCR de uma faixa horizontal, entre duas coordenadas da imagem."""
    from PIL import Image

    escala = dpi / 72.0
    W, H = im.size
    px0 = max(0, int(x_esq * escala)) if x_esq is not None else 0
    px1 = min(W, int(x_dir * escala)) if x_dir else W
    py0 = max(0, int(y_topo * escala))
    py1 = min(H, int(y_base * escala))
    if px1 - px0 < 80 or py1 - py0 < 8:
        return ''
    faixa = im.crop((px0, py0, px1, py1))
    faixa = faixa.resize((faixa.width * 2, faixa.height * 2), Image.LANCZOS)
    tmp = f'{SAIDA}/_r_{os.getpid()}_{y_topo:.0f}.png'
    faixa.save(tmp)
    r = subprocess.run(
        ['tesseract', tmp, 'stdout', '-l', 'por', '--psm', '6'],
        capture_output=True,
    )
    os.remove(tmp)
    ls = [l for l in r.stdout.decode('utf-8', 'replace').split('\n') if l.strip()]
    # descarta o que for cabeçalho/rodapé do PDF (o recorte pode encostar
    # neles quando a alternativa é a última da página)
    ls = [l for l in ls if not LIXO_OCR.match(l)]
    return max(ls, key=lambda l: len(l.strip())) if ls else ''


def _y_por_linha_px(palavras, W, H, pdf, pag):
    """y (em PONTOS do PDF) de cada linha do texto, na mesma ordem que o
    `montar` emite — para casar a linha do OCR com a letra da geometria."""
    meio = W / 2
    tol = max(2, int(H * 0.004))

    def agrupa(lst):
        out = []
        for w in sorted(lst, key=lambda w: ((w[1] + w[3]) / 2, w[0])):
            y = (w[1] + w[3]) / 2
            if out and abs(out[-1][0] - y) <= tol:
                out[-1][1].append(w)
            else:
                out.append([y, [w]])
        return out

    if not palavras:
        return []

    duas = bool(pdf and pag) and _duas_colunas_por_questoes(pdf, pag)
    if duas:
        colunas = [
            agrupa([w for w in palavras if w[0] < meio]),
            agrupa([w for w in palavras if w[0] >= meio]),
        ]
    else:
        colunas = [agrupa(palavras)]

    # `y` saiu em pixels da IMAGEM; a geometria do PDF está em pontos.
    # dpi = 72 * H / altura_do_pdf_pontos. O poppler renderiza com
    # pdftoppm, entãodpi = H / altura_da_pagina_em_pontos.
    ys = [y for col in colunas for y, _ws in col]
    return ys


def _ultima_alternativa(linhas, i):
    """Fim do bloco de alternativas que começa em i (última linha `[E]`)."""
    ultimo = i
    for k in range(i, len(linhas)):
        if re.match(r'^\s*\[[A-E]\]', linhas[k]):
            ultimo = k
        elif ultimo > i and linhas[k].strip():
            # texto de continuação da alternativa anterior
            continue
    return ultimo + 1


def _primeira_alternativa(linhas):
    """Índice da 1ª linha que já é alternativa (a do OCR de página toda)."""
    for i, ln in enumerate(linhas):
        if re.match(r'^\s*\[?LETRA\]?|^\s*O\s+\S|^\s*OQ\s+', ln):
            return i
    return -1


# cabeçalho/rodapé que o recorte pode pegar. O OCR erra o próprio rodapé
# ("DE"->"NE"), então o padrão é tolerante.
LIXO_OCR = re.compile(
    r'^\s*(?:'
    r'[ÁA]REA\s+LIVRE'
    r'|EXAME\s+NACIONAL'
    r'|ENADE\s+\d{4}'
    r'|EN\w*HARIA\s+N[DE]\s*COMPUTA'
    r'|COMPONENTE\s+ESPEC'
    r'|FORMA[ÇC][ÃA]O\s+GERAL'
    r'|\*\s*R\d'
    r'|CADERNOS?\s+DE'
    r').*',
    re.I,
)

BOLINHA_OU = re.compile(r'^\s*(?:[(\[]?\s*)?(?:O|OQ|QO|0|4|8|9|1|2|3|5|6|7|BA|OW|lell|ll)\s*\)?\s*')


def _tira_bolinha(txt):
    """Remove a bolinha lida como letra do começo do texto da alternativa."""
    return BOLINHA_OU.sub('', txt, count=1).strip()


def _pagina_com_letras(palavras, W, H, escala, seq, pdf, pag):
    k = 0
    """Monta o texto da página e troca a bolinha (lida como 'O') pela letra
    verdadeira, vinda da geometria.

    A bolinha da alternativa fica na MESMA altura da letra real (glifo de
    15.6 pt), então casamos por proximidade vertical — sem isso, quando o
    tesseract perde a 5ª bolinha, as letras A..E saem deslocadas e a questão
    fica com alternativas trocadas.
    """
    texto = montar(palavras, W, H, pdf, pag)
    if not seq:
        return texto
    linhas = texto.split('\n')
    # y (pt) de cada linha, na ordem em que saíram
    alturas = []
    tol = max(2, int(H * 0.004))
    agrupadas = []
    for w in sorted(palavras, key=lambda w: ((w[1] + w[3]) / 2, w[0])):
        y = (w[1] + w[3]) / 2
        if agrupadas and abs(agrupadas[-1][0] - y) <= tol:
            agrupadas[-1][1].append(w)
        else:
            agrupadas.append([y, [w]])

    # Casa cada linha do OCR com a letra pela ALTURA (a bolinha e a letra
    # real estão na mesma linha). Quando o tesseract perde a bolinha, sobra
    # uma linha vazia entre duas — a geometria ainda sabe que letra é a
    # próxima, então preenche.
    letras_y = [(a[0], (a[1] + a[2]) / 2) for a in seq]

    def letra_da_linha(y_pt):
        melhor, dist = None, 1e9
        for letra, cy in letras_y:
            d = abs(cy - y_pt)
            if d < dist:
                melhor, dist = letra, d
        return melhor if dist <= 12 else None

    saida = []
    ult_letra = ''
    for ln in linhas:
        s = ln.strip()
        m = re.match(r'^\[?LETRA\]?\s*|^O\s+|^OQ\s+|^\d\s+|^(?:BA|OW)\s+', s)
        if m:
            if k < len(agrupadas):
                letra = letra_da_linha(agrupadas[k][0] * escala)
            else:
                letra = None
            k += 1
            if letra:
                cauda = s[m.end():].strip()
                saida.append(f'[{letra}] ' + cauda)
                ult_letra = letra
                continue
        saida.append(ln)
    return '\n'.join(saida)


def _letra_mais_proxima(y_pt, seq):
    melhor, dist = None, 1e9
    for letra, y0, y1, _x0 in seq:
        centro = (y0 + y1) / 2
        d = abs(centro - y_pt)
        if d < dist:
            melhor, dist = letra, d
    return melhor if dist <= 12 else None


if __name__ == '__main__':
    base = '/root/enade-simulado/fontes/'
    for nome, arq in (('2014', '2014-e1_prova.pdf'), ('2017', '2017-e1_prova.pdf')):
        print(f'== OCR {nome} ==', flush=True)
        t = processar(base + arq, nome)
        with open(f'{SAIDA}/{nome}-ocr.txt', 'w', encoding='utf-8') as fh:
            fh.write(t)
        print(f'== {nome} pronto ==', flush=True)