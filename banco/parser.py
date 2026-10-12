"""Quebra o texto de uma prova em questões (objetivas e discursivas).

Entrada: saída de layout.texto_pdf() (ou do OCR) — uma linha por linha de
PDF, já na ordem de leitura e sem cabeçalho/rodapé.

As faixas FG/CE vêm da capa de cada prova (a parte "COMPONENTE ESPECÍFICO"
às vezes não sobrevive à extração), então aedition define os limites:

    2014/2017/2019 -> FG 1–8 (+D1,D2) · CE 9–35 (+D3..D5) · percepção 1–9
    2023           -> FG 1–9 (+D1)    · CE 10–38 (+D2)
"""

import re

EDICOES = {
    2014: {'fg': (1, 8), 'fg_d': (1, 2), 'ce': (9, 35), 'ce_d': (3, 5), 'percep': 9},
    2017: {'fg': (1, 8), 'fg_d': (1, 2), 'ce': (9, 35), 'ce_d': (3, 5), 'percep': 9},
    2019: {'fg': (1, 8), 'fg_d': (1, 2), 'ce': (9, 35), 'ce_d': (3, 5), 'percep': 9},
    2023: {'fg': (1, 9), 'fg_d': (1, 1), 'ce': (10, 38), 'ce_d': (2, 2), 'percep': 9},
}

INICIO_OBJ = re.compile(r'^\s*QUEST[ÃA]O\s+(\d{1,2})\s*$', re.I)
INICIO_DIS = re.compile(r'^\s*QUEST[ÃA]O\s+DISCURSIVA\s+(\d{1,2})\s*$', re.I)

# cabeçalho de duas questões na mesma linha (página em colunas)
CABECALHO_COMPOSTO = re.compile(
    r'QUEST[ÃA]O\s+(?:DISCURSIVA\s+)?\d{1,2}', re.I
)

# o questionário de percepção da prova não pontua -> fora do banco.
# precisa ser o TÍTULO da seção (linha inteira, curta): na capa a palavra
# aparece minúscula dentro de um parágrafo e não pode cortar nada.
PERCEPCAO = re.compile(
    r'^\s*[A-Za-zÀ-ÿ\s]{0,60}\bpercep[çc][ãa]o\s+d[ao]\s+prov[ae]\s*$', re.I
)


def cortar(txt, edicao):
    """-> [(idx, tipo, numero, parte, corpo)] na ordem do documento."""
    cfg = EDICOES[edicao]
    linhas = txt.split('\n')

    # 1) corta no questionário de percepção (não pontua -> fora do banco)
    #    precisa ser o TÍTULO da seção (linha inteira, curta): na capa a
    #    palavra aparece minúscula dentro de um parágrafo.
    fim = len(linhas)
    for i, ln in enumerate(linhas):
        if i > 40 and PERCEPCAO.match(ln):
            fim = i
            break

    # 2) Em página de DUAS colunas o cabeçalho das duas questões cai na mesma
    #    linha ("QUESTÃO 10        QUESTÃO 11"). Achata cada cabeçalho para a
    #    sua própria linha antes de casar.
    achatado = []
    for ln in linhas[:fim]:
        pedacos = CABECALHO_COMPOSTO.findall(ln)
        if len(pedacos) > 1:
            achatado.extend(pedacos)
        else:
            achatado.append(ln)
    fim = len(achatado)

    # 3) marca os começos
    marca = []
    for i, ln in enumerate(achatado):
        m = INICIO_DIS.match(ln)
        if m:
            marca.append((i, 'discursiva', int(m.group(1))))
            continue
        m = INICIO_OBJ.match(ln)
        if m:
            marca.append((i, 'objetiva', int(m.group(1))))

    out = []
    for k, (i, tipo, num) in enumerate(marca):
        fim_bloco = marca[k + 1][0] if k + 1 < len(marca) else fim
        corpo = '\n'.join(achatado[i + 1 : fim_bloco])
        out.append((i, tipo, num, _parte(cfg, tipo, num), corpo))
    return out


def _parte(cfg, tipo, num):
    if tipo == 'discursiva':
        lo, hi = cfg['fg_d']
        return 'FG' if lo <= num <= hi else 'CE'
    lo, hi = cfg['fg']
    return 'FG' if lo <= num <= hi else 'CE'


# --- alternativas ----------------------------------------------------------

ALT_RE = re.compile(r'^([A-E])\s+(\S.*)$', re.S)


# Frases que ENCERRAM o enunciado — o enunciado está fechado e as
# alternativas vêm a seguir. O PDF às vezes cola espaço dentro da palavra
# (kerning da Calibri): "af irma", por isso o "\s?" nos pontos onde isso
# acontece de fato.
FIM_ENUNCIADO = re.compile(
    r'(?:'
    # "é correto o que se afirma em" / "está incorreto o que se afirma em"
    r'|[\u00e9\u00ea]\s+corret[oa]s?\s+(?:apenas\s+)?o\s*que\s*se\s*af\s?irm(?:a|am)'
    # "é correto afirmar que" / "é correto afirmar"
    r'|[\u00e9\u00ea]\s+corret[oa]\s*af\s?irm[ao]\s+que'
    r'|est[\u00e1a]\s+(?:in)?corret[oa]\s+o\s+que'
    r'|assinale\s+a\s+(?:alternativa|op[\u00e7c][\u00e3a]o)'
    r'|assinale\s+(?:a|o)\s+que\s+est[\u00e1a]\s+corret[oa]'
    r'|a\s+alternativa\s+(?:correta|incorreta)'
    r'|escolha\s+a\s+(?:alternativa|op[\u00e7c][\u00e3a]o)'
    r'|qual\s+(?:d[ao]s|das)\s+alternativas'
    r'|marque\s+a\s+alternativa'
    r'|selecione\s+a\s+alternativa'
    r'|com\s+base\s+n[ao]s\s+informa[\u00e7c][\u00f5o]es'
    # "avalie as afirmações" (também vem com espaço colado: "af irmações")
    r'|avalie\s+as?\s+afirma(?:\u00e7|c)(?:\u00f5|o)es'
    r')',
    re.I,
)


MAX_ALT_LINHA = 220    # alternativa que cabe numa linha do PDF


_LETRA_OCR = re.compile(r'^\[LETRA\]\s*\)?\s*(.*)$')


def _ocr_para_letra(linhas):
    """OCR lê a bolinha da alternativa como 'O'. Recebe as 5 posições em
    ordem e devolve A..E; fora dessa forma, devolve None."""
    achados = []
    for i, ln in enumerate(linhas):
        m = _LETRA_OCR.match(ln.strip())
        if m:
            achados.append((i, m.group(1).strip()))
    if len(achados) == 5:
        return achados
    return None


def _comeca_com_letra(ln):
    m = re.match(r'^([A-E])\s+(\S.*)$', ln.strip())
    if m:
        return m
    # OCR: a bolinha da alternativa volta como [LETRA]
    m = _LETRA_OCR.match(ln.strip())
    if m:
        return _LetraOcr(m.group(1))
    return None


class _LetraOcr:
    """Letra vinda da bolinha do OCR: casa como 'LETRAOCR' + o texto."""

    def __init__(self, texto):
        self._t = texto

    def group(self, n):
        return 'LETRAOCR' if n == 1 else self._t


def _fecha_enunciado(trecho):
    return bool(FIM_ENUNCIADO.search(trecho))


def _checar_ocr(linhas):
    """-> [(i, texto)] das linhas marcadas [LETRA], se forem 4 ou 5 em bloco.

    A bolinha às vezes vem numa linha e o texto na seguinte (o tesseract
    separates os dois); nesse caso junta as linhas até o próximo [LETRA].
    """
    marcas = [
        i for i, ln in enumerate(linhas) if _LETRA_OCR.match(ln.strip())
    ]
    if len(marcas) < 4:
        return None
    p = []
    for k, i in enumerate(marcas):
        txt = _LETRA_OCR.match(linhas[i].strip()).group(1).strip()
        j = i + 1
        while j < len(linhas) and j not in marcas and linhas[j].strip():
            txt = (txt + ' ' + linhas[j].strip()).strip()
            j += 1
        p.append((i, txt))
    return p


def _sequencia(linhas):
    """-> (inicio, fim) da maior sequência A,B,C,D,E consecutively.

    É o padrão mais firme: alternativas sempre vêm na ordem, uma por linha.
    """
    melhor = None
    for i, ln in enumerate(linhas):
        if not re.match(r'^A\s+\S', ln.strip()):
            continue
        achadas = []
        letra = 'A'
        k = i
        while letra <= 'E' and k < len(linhas):
            if re.match(rf'^{letra}\s+\S', linhas[k].strip()):
                achadas.append(k)
                letra = chr(ord(letra) + 1)
            k += 1
            if len(achadas) == 5:
                break
        if len(achadas) >= 4 and (melhor is None or achadas[-1] > melhor[-1]):
            melhor = achadas
    if melhor is None or len(melhor) < 4:
        return None
    return melhor[0], melhor[-1]


def separar_alternativas(corpo):
    """-> (enunciado, {letra: texto}).

    Estratégia: achar a SEQUÊNCIA A,B,C,D,E (ou as bolinhas do OCR) e voltar
    dela. A sequência é a assinatura mais firme — "A sociedade do século XXI…"
    no começo do enunciado não forma sequência, e "A linguagem Python…" também
    não. Se a sequência fechar na linha 0, o enunciado foi engolido: aí se usa
    a frase de encerramento ("assinale a alternativa…") como âncora.
    """
    linhas = corpo.split('\n')

    seq = _sequencia(linhas)
    if seq is None:
        ocr = _checar_ocr(linhas)
        if ocr is None:
            return corpo.strip(), {}
        inicio, fim = ocr[0][0], ocr[-1][0]
        # as bolinhas dão a letra pela ordem
        enunciado = '\n'.join(linhas[:inicio]).strip()
        alt = {}
        for k, (i, txt) in enumerate(ocr[:5]):
            alt[chr(ord('A') + k)] = txt
        # continuação depois da última bolinha
        if fim + 1 < len(linhas) and alt:
            ult = chr(ord('A') + len(alt) - 1)
            alt[ult] = (alt[ult] + ' ' + ' '.join(linhas[fim + 1:]).strip()).strip()
        return enunciado, alt

    inicio, _fim = seq
    if inicio <= 1 and linhas and linhas[0].strip().upper().startswith('TEXTO'):
        # "TEXTO 1 / TEXTO 2" — os textos vêm antes do enunciado, e o
        # "A Inteligência…" do primeiro texto não é alternativa.
        inicio += 1
        while inicio < len(linhas) and not re.match(r'^[A-E]\s+\S', linhas[inicio].strip()):
            inicio += 1
    if inicio == 0:
        # A sequência colou na linha 0: isso é porque o enunciado COMEÇOU com
        # "A ..." (ex.: "A sociedade do século XXI…"). A真正 âncora é a frase
        # de encerramento — as alternativas começam na letra A logo depois.
        ancora = next(
            (k for k, ln in enumerate(linhas) if _fecha_enunciado(ln)), None
        )
        if ancora is not None:
            inicio = ancora + 1
            while inicio < len(linhas) and (
                not linhas[inicio].strip()
                or re.match(r'^[A-E]\s+\S', linhas[inicio].strip())
            ):
                if linhas[inicio].strip():
                    break
                inicio += 1

    enunciado = '\n'.join(linhas[:inicio]).strip()
    alt = {}
    letra_atual = None
    proxima = 'A'
    for ln in linhas[inicio:]:
        s2 = ln.strip()
        m = _comeca_com_letra(s2)
        if m and len(s2) <= 500:
            if m.group(1) == 'LETRAOCR':
                letra_atual = proxima
                proxima = chr(ord(proxima) + 1)
            else:
                letra_atual = m.group(1)
                proxima = letra_atual
            alt[letra_atual] = m.group(2).strip()
        elif letra_atual:
            alt[letra_atual] = (alt[letra_atual] + ' ' + s2).strip()
    return enunciado, alt


def juntar(alt):
    return [(k, alt[k]) for k in 'ABCDE' if alt.get(k)]


# --- limpeza de artefatos --------------------------------------------------

def limpar_texto(s):
    s = re.sub(r'[ \t]{2,}', ' ', s)
    linhas = [ln.rstrip() for ln in s.split('\n')]
    out, vazia = [], False
    for ln in linhas:
        if not ln.strip():
            if vazia:
                continue
            vazia = True
        else:
            vazia = False
        out.append(ln)
    # junta linha quebrada no meio de um parágrafo
    res = []
    for ln in out:
        if (
            res
            and res[-1].strip()
            and len(res[-1]) > 100
            and not res[-1].endswith(('.', '!', '?', ':', ';'))
            and not re.match(r'^\s*(I{1,3}V?|IV|V)\.\s', ln)
            and not re.match(r'^\s*[A-E]\s', ln)
        ):
            res[-1] = res[-1] + ' ' + ln.strip()
            continue
        res.append(ln)
    return '\n'.join(res).strip()