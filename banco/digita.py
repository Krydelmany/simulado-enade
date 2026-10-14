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
            # `_nova`: questão que a extração não produziu (ver `novas`);
            # `_imagem` / `_alternativas_visuais`: alternativas que são
            # desenho (gráficos, circuitos) e entram como recorte da página
            if chave in ('_nova', '_imagem') and isinstance(txt, dict):
                limpo[chave] = txt
                continue
            if chave == '_alternativas_visuais':
                limpo[chave] = bool(txt)
                continue
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

    Com as CINCO letras digitadas, as cinco substituem as da extração.
    Antes só os ids de `SUBSTITUIR_TUDO` eram substituídos, e os demais só
    ganhavam a letra que faltava: uma alternativa presente porém lida errado
    ("|, apenas." no lugar de "I, apenas.") ficava no site, embora a leitura
    certa estivesse aqui. Foi assim que 2014-FG-Q06 — gabarito C — chegou ao
    aluno com a alternativa C escrita "apenas.".

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
    if bloco.get('_imagem'):
        q['imagem'] = dict(bloco['_imagem'])
    if bloco.get('_alternativas_visuais'):
        # a resposta é o desenho: não há texto de alternativa para mostrar
        q['alternativas'] = {}
        q['alternativas_visuais'] = True
        return q

    novo = dict(q.get('alternativas') or {})
    todas = set('ABCDE') <= set(bloco)
    for letra, txt in bloco.items():
        if letra in 'ABCDE' and (
            todas or qid in SUBSTITUIR_TUDO or not (novo.get(letra) or '').strip()
        ):
            novo[letra] = txt
    # em ordem A–E: o OCR às vezes entrega fora de ordem (A no fim)
    q['alternativas'] = dict(sorted(novo.items()))
    return q


def novas(edicao=None):
    """-> questões que a extração NÃO produziu e foram lidas inteiras do PDF.

    Caso real: na prova de 2014 o OCR perdeu o cabeçalho "QUESTÃO DISCURSIVA
    4", e o texto da D04 foi parar no fim da D03. A entrada traz `_nova` com
    os campos de identificação; `tema`, `dificuldade` e `materia` vêm de
    `classificacao.json`, como as outras.
    """
    saida = []
    for qid, bloco in carregar().items():
        meta = bloco.get('_nova')
        if not meta or (edicao is not None and meta.get('edicao') != edicao):
            continue
        q = {
            'id': qid,
            'edicao': meta['edicao'],
            'parte': meta['parte'],
            'numero': meta['numero'],
            'tipo': meta['tipo'],
            'tema': None,
            'dificuldade': None,
            'figura': None,
            'enunciado': bloco.get('_enunciado', ''),
            'alternativas': {},
        }
        if meta['tipo'] == 'discursiva':
            q['padrao'] = bloco.get('_padrao', '')
        else:
            q['gabarito'] = meta.get('gabarito', '')
        if meta.get('imagem'):
            q['imagem'] = dict(meta['imagem'])
        saida.append(aplica(q))
    return saida


def acrescenta(qs, edicao):
    """Junta à extração as questões de `novas` que ela não trouxe."""
    tem = {q['id'] for q in qs}
    return list(qs) + [q for q in novas(edicao) if q['id'] not in tem]


def finaliza(q):
    """Última etapa: o texto lido do PDF entra por cima do que a cadeia fez.

    `arruma`, `formato` e `qualidade` existem para consertar a camada de
    texto/OCR; passados sobre um texto já digitado com blocos de código e
    indentação, desfazem o que está certo (o bloco VHDL de 2023-CE-Q25 virava
    "q: = 0;" picotado em quatro blocos). Por isso o `gerar.py` chama esta
    função no FIM da cadeia, e `reaplicar_banco` também.

    O enunciado e o padrão passam só pela `paragrafo.estrutura` (o texto
    digitado já vem com os parágrafos — refluir mediria "largura de coluna"
    sobre parágrafos); as alternativas, só pelo conserto de espaços.
    """
    import paragrafo

    bloco = carregar().get(q.get('id'))
    if not bloco:
        return q
    q = aplica(q)
    if bloco.get('_enunciado') or bloco.get('_nova'):
        q['enunciado'] = paragrafo.estrutura(q['enunciado'])
    if q.get('padrao') and (bloco.get('_padrao') or bloco.get('_nova')):
        q['padrao'] = paragrafo.estrutura(q['padrao'], comandos=False)
    q['alternativas'] = {
        k: paragrafo.espacos(v) for k, v in (q.get('alternativas') or {}).items()
    }
    return q


def reaplicar_banco():
    """Aplica `digitadas.json` direto nos JSON do site, sem reextrair.

    Para o texto lido do PDF entrar no banco sem os PDFs, o poppler e o
    tesseract da extração. Só toca nas questões com entrada aqui (ver
    `finaliza`). Questão de `novas` que não existe no banco é inserida no
    arquivo da edição/parte, com a classificação de `classificacao.json`.
    """
    import glob
    import anuladas
    import classificar

    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    banco = os.path.join(raiz, 'app', 'static', 'banco')
    entradas = carregar()
    mudou = 0
    for arq in sorted(glob.glob(os.path.join(banco, 'enade*.json'))):
        with open(arq, encoding='utf-8') as fh:
            qs = json.load(fh)
        ids = {q['id'] for q in qs}
        nome = os.path.basename(arq)
        for nova in novas():
            alvo = f"enade{nova['edicao']}-{nova['parte'].lower()}.json"
            if alvo == nome and nova['id'] not in ids:
                classificar.aplicar([nova])
                qs.append(nova)
                # a anulada entra só para sair logo abaixo, atualizada
                if not anuladas.anulada(nova):
                    print(f'  + {nova["id"]} (nova)')
        for i, q in enumerate(qs):
            if q['id'] not in entradas:
                continue
            antes = json.dumps(q, ensure_ascii=False)
            q = finaliza(q)
            if json.dumps(q, ensure_ascii=False) != antes:
                mudou += 1
            qs[i] = q
        # mesma ordem do gerar.py: discursivas primeiro, depois por número
        ordem = {'discursiva': 0, 'objetiva': 1}
        qs.sort(key=lambda q: (ordem.get(q['tipo'], 9), q['numero']))
        # anulada pelo INEP sai do site para `banco/anuladas.json`; grava lá
        # antes, para a questão nunca ficar sem estar em lugar nenhum
        qs, fora = anuladas.separar(qs)
        anuladas.guardar(fora)
        for q in fora:
            print(f'  - {q["id"]} -> anuladas.json')
        with open(arq, 'w', encoding='utf-8', newline='\n') as fh:
            json.dump(qs, fh, ensure_ascii=False, indent=1)
            fh.write('\n')
    print(f'{mudou} questões atualizadas a partir de digitadas.json')
    return 0


if __name__ == '__main__':
    import sys
    if '--banco' in sys.argv:
        sys.exit(reaplicar_banco())
    print(__doc__)
