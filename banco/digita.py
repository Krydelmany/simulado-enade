"""Alternativas lidas da IMAGEM do PDF oficial.

O OCR de 2014/2017 erra justamente onde dá para ler de olho: a bolinha da
alternativa e o bloco de opções quando a coluna quebra. Em vez de adivinhar,
`banco/olho.py` entrega o recorte da questão; quem lê digita aqui, e o
pipeline entra com as alternativas antes da porta de qualidade.

A regra que governa este arquivo: **nunca preencher por dedução**. Se a
imagem não deu para ler, a questão continua fora. Uma alternativa inventada
não dá sintoma — o aluno marca a letra errada e leva nota sem saber que o
problema era o dado. É o mesmo motivo pelo qual as questões de asserção com
numeral romano corrompido ficaram de fora em `qualidade.FORA`.
"""

import json
import os
import re

ARQUIVO = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       'digitadas.json')


def carregar():
    """-> {id: {letra: texto}} — só as questões que dão para aplicar."""
    if not os.path.exists(ARQUIVO):
        return {}
    with open(ARQUIVO, encoding='utf-8') as fh:
        bruto = json.load(fh)
    fora = {}
    for qid, alts in bruto.items():
        if qid.startswith('_'):
            continue
        if not isinstance(alts, dict):
            print(f'  digitadas: {qid} não é um dicionário de letras — ignorado')
            continue
        limpo = {}
        for chave, txt in alts.items():
            txt = (txt or '').strip()
            if not txt:
                continue
            # `_enunciado` / `_padrao`: texto lido da imagem para o caso em
            # que o OCR cortou o enunciado no meio (figura no meio da questão)
            if str(chave).strip() in ('_enunciado', '_padrao'):
                limpo[str(chave).strip()] = txt
                continue
            letra = str(chave).strip().upper()
            if letra in 'ABCDE':
                limpo[letra] = txt
        if limpo:
            fora[qid] = limpo
    return fora


# Questões cujo OCR destruiu o bloco de alternativas INTEIRO, e não apenas
# uma letra: o bloco vem como "|, apenas." / "Il, apenas." / "lell, apenas.",
# que são cinco leituras erradas da mesma coisa. Para essas a digitação
# substitui as cinco; para as outras, só preenche a letra que falta.
#
# Explícito de propósito. A alternativa seria um regex que tenta adivinhar
# "isso é lixo" — e já se viu que casa onde não deve ("lell" tem l minúsculo,
# "de Desempenho" não tem espaço no fim). Um erro aqui põe uma alternativa
# inventada na frente do aluno sem nenhum sintoma.
SUBSTITUIR_TUDO = {
    # bloco de alternativas destruído por inteiro: romanos corrompidos,
    # rodapé colado, ou duas opções que o OCR deixou IGUAIS depois de cortar
    # o rodapé (a repetição reprova na porta de qualidade, e com razão — o
    # acerto viraria sorteio)
    '2017-CE-Q11', '2017-CE-Q20', '2017-CE-Q33', '2017-CE-Q28', '2017-CE-Q10',
    '2017-CE-Q09',
    '2017-FG-Q01', '2017-FG-Q03', '2017-FG-Q08',
    '2014-FG-Q01', '2014-FG-Q05', '2014-CE-Q09',
    '2014-CE-Q11', '2014-CE-Q14', '2014-CE-Q16', '2014-CE-Q22', '2014-CE-Q28',
}


def completas():
    """-> ids com as CINCO alternativas digitadas.

    É o que autoriza `qualidade.problema` a ignorar a exclusão em `FORA`. Com
    quatro a exclusão continua valendo — a questão entraria com uma letra
    inventada no lugar da que não deu para ler.
    """
    return {qid for qid, alts in carregar().items()
            if set(alts) >= set('ABCDE')}


def aplica(q):
    """Preenche — ou substitui — alternativas e enunciado lidos da imagem.

    O OCR de 2014/2017 também erra o ENUNCIADO: quando a questão tem uma
    figura no meio, o extrator para nela e devolve meia frase ("A figura a
    seguir representa o diagrama de tensão" — 49 caracteres). Aí não é
    alternativa que falta, é texto cortado, e a porta reprova por "enunciado
    curto demais". A chave `_enunciado` no JSON resolve esse caso.
    """
    digitadas = carregar()
    qid = q.get('id')
    if qid not in digitadas:
        return q
    q = dict(q)
    bloco = digitadas[qid]

    if bloco.get('_enunciado'):
        q['enunciado'] = bloco['_enunciado']
    if bloco.get('_padrao'):
        q['padrao'] = bloco['_padrao']

    novo = dict(q.get('alternativas') or {})
    for letra, txt in bloco.items():
        if letra in 'ABCDE' and (
            qid in SUBSTITUIR_TUDO or not (novo.get(letra) or '').strip()
        ):
            novo[letra] = txt
    q['alternativas'] = novo
    return q
