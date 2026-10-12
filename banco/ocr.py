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

import layout

SAIDA = '/tmp/opencode/extr/ocr'


def render(pdf, pag, dpi=300):
    """Renderiza UMA página em PNG cinza.

    Usa o MUTOOL, não o pdftoppm: nestas duas edições a fonte é embutida sem
    ToUnicode, e cada renderizador substitui por uma fonte diferente. A
    substituição do poppler sai com glifos que o tesseract lê errado de forma
    sistemática (toda letra maiúscula vira minúscula: "I, III e IV." vira
    "l, lll e lv."), e o problema se agrava no recorte estreito da
    alternativa. O do mutool sai limpo — medido lado a lado na página 6 do
    2014, o mesmo bloco sai "lelv" no poppler e "le lV." no mutool.
    """
    base = f'{SAIDA}/p{pag}'
    subprocess.run(
        ['mutool', 'draw', '-r', str(dpi), '-F', 'png', '-c', 'gray',
         '-o', f'{base}.png', pdf, str(pag)],
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


# altura do glifo da letra-da-alternativa contra o corpo do texto: 15.6 pt
# contra 12.3. A letra vem da fonte dos símbolos, que tem ToUnicode — então
# continua legível mesmo com o resto do texto quebrado.
H_LETRA = (13.5, 17.5)


def _duas_colunas_por_letras(pdf, pagina):
    """-> bool: a página tem alternativas em duas margens (portanto 2 colunas).

    Complementa a detecção pelos cabeçalhos "QUESTÃO". Em 2017 só a questão
    da PRIMEIRA coluna tem cabeçalho — a da segunda começa no meio da
    página, sem título. As letras da alternativa, ao contrário, aparecem
    nas duas margens, e são o sinal mais firme que existe.
    """
    if pagina in _BBOX_CACHE:
        xml = _BBOX_CACHE[pdf][pagina]
    else:
        r = subprocess.run(
            ['pdftotext', '-bbox-layout', '-f', str(pagina), '-l',
             str(pagina), pdf, '-'],
            capture_output=True,
        )
        xml = r.stdout.decode('utf-8', 'replace')
        _BBOX_CACHE[(pdf, pagina)] = xml
    xs = []
    for m in layout.WORD_RE.finditer(xml):
        w = m.group(5)
        if len(w) != 1 or w not in 'ABCDE':
            continue
        y0, y1 = float(m.group(2)), float(m.group(4))
        if not (H_LETRA[0] <= y1 - y0 <= H_LETRA[1]):
            continue
        xs.append(float(m.group(1)))
    if len(xs) < 6:
        return False
    x0 = min(xs)
    return any(x - x0 > 60 for x in xs)


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
    # A geometria do PDF decide, não a densidade do OCR. O sinal é simples e
    # não ambíguo: o pdftotext -bbox funciona mesmo com a fonte quebrada (ele
    # lê a caixa, não o texto) e devolve uma caixa "QUESTÃO" SEPARADA para
    # cada questão. Duas caixas na MESMA altura = página de 2 colunas; uma
    # caixa só (mesmo com tabelas e figuras ao lado) = página de 1 coluna.
    #
    # O PDF tem prioridade: o teste do OCR (nenhuma palavra cruzando o meio)
    # erra justamente quando a página tem um cabeçalho ou uma tabela de
    # largura total — e aí as duas questões do meio de página saem
    # embaralhadas, com o enunciado de uma colado no da outra.
    if pdf and pagina:
        duas = (
            _duas_colunas_por_questoes(pdf, pagina)
            or _duas_colunas_por_letras(pdf, pagina)
        )
    else:
        duas = not any(
            w[0] < meio * 0.85 and w[2] > meio * 1.15 for w in corpo
        )

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
        textos.append(_marca_bolinhas(_sem_rodape(limpo)))
    return '\n'.join('\n'.join(t) for t in textos)


# O OCR da bolinha varia conforme a fonte e o ruído: "A)" -> "O", "B)" -> "4",
# "C)" -> "OQ", "E)" -> "E". O tesseract também devolve a bolinha SOZINHA na
# linha. Tudo isso vira o mesmo marcador.
BOLINHA = '[LETRA]'

BOLINHA_VARIANTES = re.compile(
    r'^(?:'
    # bolinha lida como "O", "(O", "O)" etc. — o token vai sozinho
    r'[(\[]?\s*(?:O|OQ|QO|Q0|QQ|BA|OW|OU|O[A-Z]|0|4|8|9|1|2|3|5|6|7'
    r'|lell|lelll|ll|Q)\s*[)\]]?(?=\s|$)'
    # ou lida como a PRÓPRIA LETRA, mas só com parêntese/colchete depois:
    # sem isso "A respeito dessas asserções…" — que é a frase que antecede as
    # alternativas — entra como se fosse a alternativa A
    r'|[A-E]\s*[):]'
    r')'
)

# Cabeçalho e rodapé que o OCR traz colados ao texto. Sem tirar, a última
# alternativa da página acaba com "2017 enade Exame Nacional de Desempenho dos
# Estudantes" grudado — e entra no banco errada. O corte vai do marcador até o
# fim da linha, porque o OCR junta o rodapé com a alternativa na MESMA linha.
RODAPE = re.compile(
    r'\b(?:'
    r'\d{4}\s+enade'
    r'|EN[A-Z]{0,3}DE\s+\d{4}'                # ENADE 2014
    r'|enade\s+Exame\s+Nacional'
    r'|Exame\s+Nacional(?:\s+de\s+Desempenho)?(?:\s+dos\s+Estudantes)?'
    r'|EN\w*HARIA\s+(?:DE|N[DE])(?:\s+COMPUTA[\wÇÃ]*)?'
    r'|COMPONENTE\s+ESPEC'
    r'|CADERNOS?\s+DE\s+PROVA'
    r'|FORMA[ÇC][ÃA]O\s+GERAL'
    r').*$',
    re.I,
)


# Linhas INTEIRAS de rodapé. O OCR quebra o rodapé em várias linhas curtas
# ("2017", "enade", "dos Estudantes") e o `separar_alternativas` emenda as
# linhas depois da última bolinha na última alternativa — sem tirar aqui, a
# alternativa E do banco vira "..., apenas. 2017 enade dos Estudantes".
SO_RODAPE = re.compile(
    r'^\s*(?:'
    r'\d{4}'                                      # 2017
    r'|enade'
    r'|(?:dos|de)\s+Estudantes'
    r'|Exame\s+Nacional.*'
    r'|EN\w*HARIA\s+(?:DE|N[DE])(?:\s+COMPUTA[\wÇÃ]*)?'   # "ENGENHARIA DE"
    r'|COMPUTA[ÇC][ÃA]O'
    r'|\*[^.]{4,}\*?'                              # "*R42014 4*" virado pelo OCR
    r'|COMPONENTE\s+ESPEC.*'
    r'|\d{1,3}\s+enade'
    r')$',
    re.I,
)

# número de página sozinho, só no fim da coluna (gráficos têm "160", mas
# nunca no fim do texto corrido)
SO_PAGINA = re.compile(r'^\s*\d{1,3}\s*$')


def _sem_rodape(linhas):
    saida = [t for t in linhas if t and not SO_RODAPE.match(t)]
    while saida and SO_PAGINA.match(saida[-1]):
        saida.pop()
    return saida


def _limpa_lixo(t):
    """Tira cabeçalho, rodapé e o rótulo "ÁREA LIVRE" de uma linha do OCR."""
    t = RODAPE.sub('', t)
    t = re.sub(r'\s*\b[ÁA]REA\s+LIVRE\b\s*', ' ', t, flags=re.I)
    t = re.sub(r'\s*\*\s*R[\d ]+\*?\s*', ' ', t)
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


def _comeca_bolinha(t):
    t = t.strip()
    # A bolinha que o tesseract leu como "O)" já virou marcador na hora de
    # ler a palavra (ver `_corrige`); ela conta tanto quanto as outras, senão
    # o grupo de 4 ou 5 quebra e a questão inteira perde as letras.
    return t.startswith(BOLINHA) or bool(BOLINHA_VARIANTES.match(t))


def _marca_bolinhas(linhas_txt):
    """Troca a bolinha inicial (lida como 'O') pelo marcador da alternativa.

    O tesseract não distingue a bolinha da letra O — mesmo desenho. A
    assinatura é o CONJUNTO: as alternativas de uma questão vêm em 4 ou 5
    linhas marcadas, e nada mais vem assim. Uma frase normal ("O gestor de
    um hotel...") vem sozinha e é deixada intacta.

    O agrupamento é por SEQUÊNCIA (vão pequeno entre uma bolinha e a outra).
    Uma alternativa pode ocupar 3 ou 4 linhas de texto, então o vão em
    *linhas do texto* chega a 5 — medir só "as quatro seguintes" deixava
    passar justamente as questões de alternativa longa.
    """
    cand = [i for i, t in enumerate(linhas_txt) if _comeca_bolinha(t)]
    if len(cand) < 4:
        return linhas_txt

    VAO = 8
    runs = [[cand[0]]]
    for i in cand[1:]:
        if i - runs[-1][-1] <= VAO:
            runs[-1].append(i)
        else:
            runs.append([i])

    for run in runs:
        if len(run) < 4:
            continue
        for i in run:
            if linhas_txt[i].startswith(BOLINHA):
                continue
            linhas_txt[i] = BOLINHA + BOLINHA_VARIANTES.sub('', linhas_txt[i], count=1)
    return linhas_txt


def _componentes(banda, min_w, max_w, min_h, max_h, min_preench):
    """Caixas (x0, y0, x1, y1) dos blobs escuros com a forma pedida.

    `banda` é uma imagem "L" em que o que interessa é PRETO (255). Antes de
    rotular, a imagem é CORROÍDA: o traço do texto tem 2-3 px e some, a
    bolinha (disco de ~57 px) continua inteira. Sem isso o rotulamento teria
    que percorrer a página inteira palavra por palavra; depois da corrosão
    sobram poucas centenas de pixels.
    """
    from PIL import ImageFilter

    w, h = banda.size
    # 1) FECHAMENTO: a letra branca dentro da bolinha corta o disco ao meio,
    #    e a dilatação seguida de erosão junta as duas metades de volta. Sem
    #    isso a corroação seguinte acha dois arcos estreitos e nada.
    k = 13
    fina = banda.filter(ImageFilter.MaxFilter(k)).filter(ImageFilter.MinFilter(k))
    # 2) CORROSÃO: o traço do texto (2-3 px) some, a bolinha continua
    fina = fina.filter(ImageFilter.MinFilter(5))
    buf = fina.tobytes()
    vistos = bytearray(w * h)
    achados = []
    for py in range(h):
        base = py * w
        for px0 in range(w):
            if buf[base + px0] != 255 or vistos[base + px0]:
                continue
            pilha = [(px0, py)]
            vistos[base + px0] = 1
            x0 = x1 = px0
            y0 = y1 = py
            n = 0
            while pilha:
                cx, cy = pilha.pop()
                n += 1
                if cx < x0:
                    x0 = cx
                if cx > x1:
                    x1 = cx
                if cy < y0:
                    y0 = cy
                if cy > y1:
                    y1 = cy
                b = cy * w
                for nx in (cx - 1, cx + 1):
                    if 0 <= nx < w and buf[b + nx] == 255 and not vistos[b + nx]:
                        vistos[b + nx] = 1
                        pilha.append((nx, cy))
                for ny in (cy - 1, cy + 1):
                    if 0 <= ny < h:
                        k = ny * w + cx
                        if buf[k] == 255 and not vistos[k]:
                            vistos[k] = 1
                            pilha.append((cx, ny))
            bw, bh = x1 - x0 + 1, y1 - y0 + 1
            if not (min_w <= bw <= max_w and min_h <= bh <= max_h):
                continue
            # a corrosão come 2 px de cada lado: a caixa real é maior
            ax0, ay0, ax1, ay1 = max(0, x0 - 2), max(0, y0 - 2), min(w - 1, x1 + 2), min(h - 1, y1 + 2)
            area = (ax1 - ax0 + 1) * (ay1 - ay0 + 1)
            if n / float(area) < min_preench:
                continue
            achados.append((ax0, ay0, ax1, ay1))
    return achados


def _bolinhas_da_imagem(img, dpi=400):
    """-> [(x0, y0, y1)] das bolinhas de alternativa, em pixel da imagem.

    A bolinha é um CÍRCULO PRETO com a letra branca dentro, do tamanho
    exato da fonte (15.6 pt de altura contra 12.3 do corpo). O tesseract
    não a reconhece em boa parte das linhas — e sem ela a alternativa
    perde a marca e as letras saem deslocadas. Na imagem não há dúvida: o
    desenho é sempre o mesmo, então dá para achá-la pelo formato.
    """
    from PIL import Image

    W, H = img.size
    esc = dpi / 72.0 / 2          # meio ponto: metade da escala, 4x menos
    achados = []
    for x0, x1 in ((0, int(W * 0.34)), (int(W * 0.46), W)):
        banda = img.crop((x0, 0, x1, H)).convert('L')
        # NEAREST: um resize bicúbico transforma o binário em cinza e a
        # corrosão seguinte não acha mais nada
        banda = banda.resize(
            (max(1, banda.width // 2), max(1, banda.height // 2)),
            Image.NEAREST,
        )
        banda = banda.point(lambda v: 255 if v < 110 else 0)
        # em meia escala a bolinha (12 x 15.6 pt) sai com ~28 x 43 px, e a
        # corrosão come 2 de cada lado -> o rótulo pega ~24 x 39
        for cx0, cy0, cx1, cy1 in _componentes(
            banda, int(6 * esc), int(17 * esc), int(6 * esc), int(23 * esc), 0.45
        ):
            achados.append((
                x0 + cx0 * 2, cy0 * 2, cy1 * 2 + 2, cx1 - cx0 + 1,
            ))
    return sorted(achados, key=lambda b: b[1])


def _marca_bolinhas_visiveis(palavras, img, dpi):
    """Insere o marcador `[LETRA]` onde a imagem mostra a bolinha.

    Só entra no lugar de uma bolinha REALMENTE detectada e de tamanho certo,
    e só numa linha que ainda não tem marca — assim o ganho é só o que o
    tesseract perdeu.
    """
    if not palavras:
        return palavras
    H = img.size[1]
    tol = max(2, int(H * 0.004))
    linhas = _agrupar(palavras, tol)
    for x0, y0, y1, larg in _bolinhas_da_imagem(img, dpi):
        cy = (y0 + y1) / 2
        melhor, dist = None, 1e9
        for ln in linhas:
            if not ln[1]:
                continue
            # a bolinha é o PRIMEIRO desenho da linha: a linha precisa começar
            # logo à direita dela
            if not (x0 - 30 <= ln[1][0][0] <= x0 + larg + 140):
                continue
            d = abs(ln[0] - cy)
            if d < dist:
                melhor, dist = ln, d
        if melhor is None or dist > (y1 - y0) * 0.6:
            continue
        ws = melhor[1]
        if ws[0][4] == BOLINHA or ws[0][0] < x0 + larg:
            continue                      # já tem marca, ou é o texto mesmo
        if ws[0][2] - ws[0][0] > larg * 1.6:
            continue                      # primeira palavra larga demais: não é bolinha
        h = (y1 - y0)
        ws.insert(0, (x0, cy - h / 2, x0 + larg, cy + h / 2, BOLINHA, 100))
    return [w for _y, ws, _x in linhas for w in ws]


def _paginas_do_questionario(pdf):
    """Páginas do "QUESTIONÁRIO DE PERCEPÇÃO DA PROVA" (não pontua).

    Vem no fim das provas de 2014 e 2017 e tem o mesmo desenho A..E das
    alternativas; detectá-lo aqui evita o OCR e o corte errado de uma
    questão.
    """
    info = subprocess.run(['pdfinfo', pdf], capture_output=True).stdout.decode()
    m = re.search(r'Pages:\s+(\d+)', info)
    total = int(m.group(1)) if m else 0
    for p in range(4, total + 1):
        t = subprocess.run(
            ['pdftotext', '-f', str(p), '-l', str(p), pdf, '-'],
            capture_output=True,
        ).stdout.decode('utf-8', 'replace')
        if re.search(r'QUESTION[ÁÃ]RIO DE PERCEP[ÇC]Ã?O', t, re.I):
            return set(range(p, total + 1))
    return set()


def processar(pdf, nome, paginas=None, dpi=400):
    """OCR de todas as páginas -> texto na ordem de leitura."""
    from PIL import Image

    os.makedirs(SAIDA, exist_ok=True)
    info = subprocess.run(['pdfinfo', pdf], capture_output=True).stdout.decode()
    m = re.search(r'Pages:\s+(\d+)', info)
    total = int(m.group(1)) if m else 0
    if paginas:
        total = max(paginas)

    sem_questao = _paginas_do_questionario(pdf)
    partes = []
    for p in range(1, total + 1):
        if p in sem_questao:
            partes.append('')
            continue
        png = render(pdf, p, dpi)
        with Image.open(png) as im:
            W, H = im.size
            palavras = _marca_bolinhas_visiveis(ocr(png), im, dpi)
            partes.append(montar(palavras, W, H, pdf, p))
        os.remove(png)
        print(f'  {nome} p{p}/{total} ok ({len(partes[-1])} car.)', flush=True)
    return '\n'.join(partes)


if __name__ == '__main__':
    base = '/root/enade-simulado/fontes/'
    for nome, arq in (('2014', '2014-e1_prova.pdf'), ('2017', '2017-e1_prova.pdf')):
        print(f'== OCR {nome} ==', flush=True)
        t = processar(base + arq, nome)
        with open(f'{SAIDA}/{nome}-ocr.txt', 'w', encoding='utf-8') as fh:
            fh.write(t)
        print(f'== {nome} pronto ==', flush=True)
