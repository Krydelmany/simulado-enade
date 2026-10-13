"""Porta de qualidade do banco: o que NÃO pode entrar no site.

Uma questão com alternativa faltando ou trocada é PIOR do que não existir —
o aluno marcaria uma letra e levaria o resultado errado sem perceber. E uma
questão em que o enunciado vazou para dentro das alternativas é ilegível.

A extração das provas de 2014 e 2017 passa por OCR (a fonte delas não tem
ToUnicode), e o OCR erra justamente a bolinha da alternativa: quando ela some,
o bloco de Alternatives não fecha e o enunciado inteiro cai dentro das
alternativas. Aqui isso é detectado pelo FORMATO — o enunciado da prova é
muito mais longo que qualquer alternativa, e traz as frases de comando que
só aparecem antes das opções.

Para 2019 e 2023 o texto vem íntegro do PDF; o filtro também passa por lá,
e é a rede de segurança contra uma regressão silenciosa.
"""

import re

# frases que só aparecem no ENUNCIADO, nunca na alternativa
COMANDO_ENUNCIADO = re.compile(
    r'assinale\s+(a\s+)?(a\s+)?op[çc][ãa]o'
    r'|avalie\s+as\s+afirma'
    r'|a\s+partir\s+das\s+informa[çc][õo]es\s+apresentadas'
    r'|conclus[õo]es?\s+que'
    r'|com\s+base\s+nas\s+informa[çc][õo]es'
    r'|considerando?\s+o\s+texto',
    re.I,
)

LIXO_PROVA = re.compile(
    r'EN[GW]?ENHARIA\s+(?:DE|N[DE])|Exame\s+Nacional|\benade\b'
    r'|COMPONENTE\s+ESPEC|CADERNOS?\s+DE|FORMA[ÇC][ÃA]O\s+GERAL'
    r'|\*\s*R\d{6,}',
    re.I,
)

# Bloco de código cercado por ``` — o `formato.py` marca antes deste módulo
# rodar, e a quebra de linha dentro dele é informação, não ruído.
FENCE = re.compile(r'```[^\n`]*\n[\s\S]*?```')

# A prova de 2023 CE tem alternativas muito verborrágicas (a maior tem 352
# caracteres); enunciado vazado na alternativa passa de 470. O corte fica no
# meio, e o teste de "trecho de enunciado" pega o resto.
MAX_ALTERNATIVA = 400
MIN_ENUNCIADO = 60         # enunciado mais curto que este é corte errado

# SUFIXO de rodapé que o extrador deixa grudado na última alternativa (é
# sempre a E, que é a última da página). Corta do marcador até o fim.
SUFIXO_RODAPE = re.compile(
    r'\s*(?:'
    r'EN[GW]?ENHARIA\s+(?:DE|N[DE])(?:\s+COMPUTA[\wÇÃ]*)?'
    r'|COMPUTA[ÇC][ÃA]O'
    r'|Engenharia\s*MAT[ÉE]RIA\s*de\s*Computa[Çc][Ãa]o'
    r'|MAT[ÉE]RIA'
    r'|LOGO'
    r'|COMPONENTE\s+ESPEC\w*'
    r'|FORMA[ÇC][ÃA]O\s+GERAL'
    r'|CADERNOS?\s+DE'
    r'|\d{4}\s+enade'
    r'|enade'
    r'|Exame\s+Nacional.*'
    # Marcador de fonte do INEP: `*R0820235**8*`. Tem `R` + dígitos logo
    # depois — é isso que distingue do `*` de ponteiro em C (`void *s`),
    # do `*` de Kleene em linguagem formal (`{0,1}*`) e do `SELECT *`.
    #
    # NÃO existe regra "número de página no fim" aqui. Já houve uma
    # (`\d{1,3}\s*$`) e ela cortava dado bom: `= 0` virava `=`, `I1` virava
    # `I`, os binários `1010`/`111111` viravam `10`/`111`. O rodapé real
    # ("COMPUTAÇÃO 23", "LOGO", "ENGENHARIA DE COMPUTAÇÃO") já é pego pelas
    # alternativas acima, que vem antes na alternância.
    r'|\*R\d{5,}\*?\d*\*?'
    r').*$',
    re.I,
)


def _normaliza_texto(t):
    """Colapsa espaço em branco fora dos blocos de código.

    O texto extraído do PDF vem com quebra de linha a cada linha da coluna, e
    isso some quando o enunciado vira parágrafo. DENTRO de um bloco ``` a
    quebra é a informação — é ela que separa uma linha de código da
    seguinte —, então os blocos ficam intactos.

    O bloco volta com `\n` nas duas pontas. Sem isso o ``` fecha colado na
    frase seguinte, e o renderizador lê ```SEDGEWICK, como se fosse o nome da
    linguagem do bloco — o código some da tela.
    """
    if not t:
        return t
    partes = []
    ultimo = 0
    for m in FENCE.finditer(t):
        if m.start() > ultimo:
            partes.append(' '.join(t[ultimo:m.start()].split()))
        partes.append(m.group(0))
        ultimo = m.end()
    if ultimo < len(t):
        partes.append(' '.join(t[ultimo:].split()))
    return '\n'.join(p for p in partes if p).strip()


def limpa(q):
    """Tira o rodapé que sobrou grudado nas alternativas (em cópia)."""
    q = dict(q)
    alt = q.get('alternativas') or {}
    novo = {}
    for letra, txt in alt.items():
        t = SUFIXO_RODAPE.sub('', (txt or '').strip()).strip()
        t = _normaliza_texto(t)
        if t:
            novo[letra] = t
    q['alternativas'] = novo
    q['enunciado'] = _normaliza_texto(
        SUFIXO_RODAPE.sub('', (q.get('enunciado') or '').strip()).strip()
    )
    return q


# Questões fora do banco por um motivo que a checagem de formato não pega,
# com o motivo escrito — a lista é curta e revisável.
FORA = {
    '2014-FG-Q01': 'enunciado com DUAS questões coladas (o OCR juntou a do '
                   'texto de Milton Nascimento com a de asserções '
                   'verdadeiro/falso); as alternativas são da segunda e as '
                   'asserções sumiram',
    '2014-CE-Q09': 'as cinco alternativas saíram ilegíveis do OCR ("|.", '
                   '"leiv.", "llelll."); precisa de digitação manual',
    # As de numeral romano: o enunciado está bom, mas as alternativas são
    # "|, apenas." / "Ill, apenas." / "Ile Ill, apenas." — o tesseract leu "I"
    # como "|" e "II" como "Il". Reconstruir qual romano ia com qual letra
    # exigiria abrir o PDF de cada uma; chutar erraria a alternativa sem
    # nenhum sintoma visível, que é o pior jeito de errar.
    '2017-CE-Q11': 'alternativas com numerais romanos ilegíveis ("|, apenas.")',
    '2017-CE-Q15': 'alternativas com numerais romanos ilegíveis',
    '2017-CE-Q20': 'alternativas com numerais romanos ilegíveis',
    '2017-CE-Q33': 'alternativas com numerais romanos ilegíveis',
    '2017-FG-Q02': 'alternativas com numerais romanos ilegíveis',
}

# Questionário de alternativas em que duas ou mais são IDÊNTICAS. O
# gabarito aponta para uma delas, então o acerto vira sorteio — e o aluno é
#CommandsHOW punido por um defeito do dado, não por não saber a matéria.
def _duplicadas(alts):
    vals = [(v or '').strip() for v in alts.values() if (v or '').strip()]
    return len(vals) != len(set(vals))


def problema(q):
    """-> motivo string, ou None se a questão pode entrar no banco."""
    if q['id'] in FORA:
        return FORA[q['id']]

    if q.get('alternativas_visuais'):
        # alternativa é a própria imagem (código/fórmula/diagrama): não há
        # texto para conferir, e é assim que essas questões já estão no site
        return None

    if q['tipo'] != 'objetiva':
        if len(q['enunciado']) < MIN_ENUNCIADO:
            return 'enunciado curto demais'
        return None

    enun = q['enunciado'] or ''
    alts = q.get('alternativas') or {}

    if not enun.strip():
        return 'enunciado vazio'
    if len(enun) < MIN_ENUNCIADO:
        return f'enunciado curto demais ({len(enun)} car.)'

    if len(alts) != 5:
        return f'só {len(alts)} de 5 alternativas'
    if _duplicadas(alts):
        return 'alternativas repetidas (o acerto viraria sorteio)'
    for letra, txt in sorted(alts.items()):
        t = (txt or '').strip()
        if not t:
            return f'alternativa {letra} vazia'
        if len(t) > MAX_ALTERNATIVA:
            return f'alternativa {letra} com {len(t)} caracteres (enunciado)'
        if COMANDO_ENUNCIADO.search(t):
            return f'alternativa {letra} é trecho de enunciado'
        if LIXO_PROVA.search(t):
            return f'alternativa {letra} com lixo da página'

    gab = (q.get('gabarito') or '').strip()
    if gab and gab != 'ANULADA' and gab not in alts:
        return f'gabarito {gab} não está entre as alternativas'
    return None