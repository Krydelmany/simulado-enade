"""Correções determinísticas no texto extraído, depois da porta de qualidade.

O OCR de 2014 e 2017 erra os mesmos caracteres sempre, porque a fonte é
embutida sem ToUnicode e a substituição acontece no renderizador. Os erros
são tão repetitivos que dá para consertar por regra — e é melhor consertar
por regra do que deixar a pergunta errada no ar, porque uma alternativa
trocada não dá sintoma: o aluno marca uma letra e leva nota sem saber que
errou.

Cada regra aqui é reversível por inspeção: são substituições literais com um
padrão visível no texto quebrado. O que não dá para corrigir por regra
(numerais perdidos na extração de fórmula, por exemplo) NÃO está aqui — vai
para a lista de exclusão em `qualidade.FORA`.
"""

import re

# --------------------------------------------------------------------------
# 1. Numerais romanos lidos como "|" e "Il"
#
# São as alternativas das questões de asserção verdadeiro/falso:
# "I, apenas." / "II, apenas." / "III, apenas." / "IV, apenas." /
# "III e IV, apenas.". O tesseract lê "I" como "|" ou "l", "II" como "Il" e
# "III e IV" como "Ile Ill".
# --------------------------------------------------------------------------
ROMANOS = [
    (re.compile(r'^Ile\s*Ill,\s*apenas\.$', re.I), 'III e IV, apenas.'),
    (re.compile(r'^Ile\s*Ill\s+apenas\.$', re.I), 'III e IV, apenas.'),
    (re.compile(r'^Ill,\s*apenas\.$'), 'III, apenas.'),
    (re.compile(r'^Il,\s*apenas\.$'), 'II, apenas.'),
    (re.compile(r'^\|,\s*apenas\.$'), 'I, apenas.'),
]

# "apenas." sozinho é o quarto item da sequência (IV) — só faz sentido
# quando as três anteriores são I, II e III. O contexto decide.
ROMANO_SOZTINHO = re.compile(r'^apenas\.$', re.I)


def arruma_romanos(q):
    alts = q.get('alternativas') or {}
    if not alts or q.get('tipo') != 'objetiva':
        return q
    vals = list(alts.values())
    tem_romanos = sum(
        1 for v in vals if re.match(r'^(I|Il|Ill|\|)[le,]*\s*apenas\.', v or '', re.I)
    )
    if tem_romanos < 3:
        return q
    novo = {}
    for letra, txt in alts.items():
        t = (txt or '').strip()
        for rx, bom in ROMANOS:
            if rx.match(t):
                t = bom
                break
        else:
            if ROMANO_SOZTINHO.match(t):
                t = 'IV, apenas.'
        novo[letra] = t
    q['alternativas'] = novo
    return q


# --------------------------------------------------------------------------
# 2. Asserções: "As asserções le Il são proposições verdadeiras…"
#
# O "le Il" é "I e II" com o "e" e o traço lidos como "l" e "e". Já o "|" solto
# é "I" ou "II" conforme o contexto: dentro de "As asserções … " são as duas,
# já "A asserção |" é só a primeira.
# --------------------------------------------------------------------------
ASSERCAO = [
    (re.compile(r'As\s+asser[çc][õo]es\s+le\s+Il\s+s[ãa]o'), 'As asserções I e II são'),
    (re.compile(r'As\s+asser[çc][õo]es\s+le\s+Il\s+s[ãa]o\s+proposi[çc][õo]es\s+falsas', re.I),
     'As asserções I e II são proposições falsas.'),
    (re.compile(r'As\s+asser[çc][õo]es\s+le\s+Il'), 'As asserções I e II'),
    (re.compile(r'\be\s+a\s+Il\s+n[ãa]o\s+[ée]'), 'e a II não é'),
    (re.compile(r'\be\s+a\s+Il\s+[ée]'), 'e a II é'),
    (re.compile(r'\ba\s+Il\s+n[ãa]o\s+[ée]'), 'a II não é'),
    (re.compile(r'\ba\s+Il\s+[ée]'), 'a II é'),
    (re.compile(r'\ba\s+Il\s+n[ãa]o\s+[ée]\s+justificativa'), 'a II não é justificativa'),
    (re.compile(r'A\s+asser[çc][ãa]o\s+\|'), 'A asserção I'),
    (re.compile(r'da\s+\|\.'), 'da I.'),
    (re.compile(r'da\s+II\s+n[ãa]o\s+[ée]\s+justificativa'), 'da II não é justificativa'),
]


def arruma_assercoes(q):
    alts = q.get('alternativas') or {}
    novo = {}
    for letra, txt in alts.items():
        t = txt or ''
        if 'asser' not in t.lower():
            novo[letra] = t
            continue
        for rx, bom in ASSERCAO:
            t = rx.sub(bom, t)
        novo[letra] = t
    q['alternativas'] = novo
    return q


# --------------------------------------------------------------------------
# 3. Sucata da página
#
# "RASCUNHO" é o rótulo da área de rascunho do caderno de prova — aparece no
# fim de TODAS as discursivas. O U+FFFD é caractere que o poppler não sabe
# decodificar. Os dois vão para o enunciado e para as alternativas.
# --------------------------------------------------------------------------
# "RASCUNHO" é o rótulo da área de rascunho do caderno de prova e vem
# seguido da grade de letras e números impressa nela. Às vezes fica no fim
# do enunciado, às vezes no meio — nos dois casos é sucata, nunca conteúdo.
RASCUNHO = re.compile(
    r'\s*\bRASCUNHO\b\s*(?:[-–—]?\s*\w+)?\s*$'          # no fim da linha
    r'|\s*\bRASCUNHO\b\s+(?:[A-ZÀ-Ý0-9]\s*){3,}.*$',    # grade do caderno
    re.I | re.M,
)
SUFixo_RODAPE_2 = re.compile(
    r'\s*\bde\s+Desempenho(?:\s+de\s+Desempenho)?\s*%?\s*$'
    # o rodapé da prova vem como "/%" repetido (o OCR duplica), então o
    # padrão precisa cobrir a repetição — um passe só tiraria o último
    r'|(?:\s*/?\s*%)+\s*$',
    re.I,
)
LIXO_CURTO = re.compile(r'\s*Lite\.\s*$', re.I)


def limpa_texto(t):
    if not t:
        return t
    t = t.replace('�', ' ')          # U+FFFD
    t = RASCUNHO.sub('', t)
    t = LIXO_CURTO.sub('', t)
    t = SUFixo_RODAPE_2.sub('', t)
    t = re.sub(r'\s*de\s+Desempenho\s+de\s+Desempenho.*$', '', t, flags=re.I)
    t = re.sub(r'[ \t]{2,}', ' ', t)
    return t.strip()


# Padrão de resposta que é PLACEHOLDER: o INEP escreve "o estudante deve
# apresentar um desenho tal como:" e o desenho é uma figura que não foi
# extraída. Sem o desenho, mandar o aluno se autoavaliar contra esse texto é
# pior que não mandar — ele compara a resposta com nada e se Dá nota por
# comparacao com o vazio.
PADRAO_PLACEHOLDER = re.compile(
    r'(o\s+estudante\s+deve\s+(apresentar|fazer)\s+um\s+desenho\s+tal\s+como)'
    r'|^\s*$',
    re.I,
)


def marca_padrao_placeholder(q):
    """Sinaliza quando o padrão de resposta é remissão a desenho ausente."""
    p = q.get('padrao') or ''
    if not p.strip():
        q['padrao_placeholder'] = True
        return q
    # tudo sem texto aproveitável = só remissões a desenho
    frases = [f for f in re.split(r'[;\n]', p) if f.strip()]
    if frases and all(PADRAO_PLACEHOLDER.search(f) for f in frases):
        q['padrao_placeholder'] = True
    return q


def limpa(q):
    """Aplica todas as correções numa cópia da questão."""
    q = dict(q)
    q['enunciado'] = limpa_texto(q.get('enunciado'))
    if q.get('padrao'):
        q['padrao'] = limpa_texto(q['padrao'])
    q['alternativas'] = {k: limpa_texto(v) for k, v in (q.get('alternativas') or {}).items()}
    q = arruma_assercoes(q)
    q = arruma_romanos(q)
    if q.get('tipo') == 'discursiva':
        q = marca_padrao_placeholder(q)
    return q