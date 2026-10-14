"""Parágrafos e espaçamento do texto das questões.

O texto sai do PDF com uma quebra a cada linha da coluna, e a porta de
qualidade colapsava TUDO num parágrafo só: 147 das 158 questões oficiais
chegavam ao aluno como um bloco único — texto-base, fonte, comando, as
afirmações I a V e a pergunta final emendados. Com `white-space: pre-line`
no `.enunciado`, o app já desenha `\\n` como quebra; faltava o texto trazê-la.

Duas fontes de quebra, nesta ordem:

1. **As linhas do PDF** (`reflui`), quando ainda existem — na extração e nos
   padrões de resposta, que guardam as linhas cruas. Linha cheia emenda com
   a seguinte; linha curta que termina em ponto fecha parágrafo; linha curta
   sem pontuação (linha de tabela, de código, título) fica sozinha.
2. **A estrutura da prova** (`estrutura`), que é sempre a mesma e sobrevive
   ao texto já achatado: fonte ("Disponível em", "SOBRENOME, X."), comando
   ("Considerando…", "Nesse contexto…", "É correto…"), afirmações I., II.,
   itens a), b), marcadores •, o PORQUE da asserção-razão, o "TEXTO 1" e a
   pergunta final que termina sem ponto ("…o tempo mínimo é de").

A regra que governa o módulo: **só espaço em branco muda**. As duas exceções
são a tabela de palavras grudadas (em que a correção é exatamente pôr
espaços de volta) e o "•" da fonte Symbol (\\uf0b7, que o navegador desenha
como quadradinho vazio). Fora isso, nenhum caractere visível é criado,
apagado ou trocado — `--banco` confere isso questão por questão e não grava
se falhar. Rótulo lido errado pelo OCR ("|." no lugar de "I.") NÃO é
corrigido aqui: "Il." pode ser II ou III, e trocar o rótulo de uma
afirmação muda a resposta.

    python3 banco/paragrafo.py --banco   # reaplica nos JSON do site
"""

import glob
import json
import os
import re
import sys

# --------------------------------------------------------------------------
# Palavras grudadas — o poppler perdeu os espaços de alguns trechos de 2019
# (fonte com espaçamento por kerning). Cada entrada só devolve os espaços:
# `correto.replace(' ', '') == grudado.replace(' ', '')`, conferido no import.
# --------------------------------------------------------------------------
GRUDADAS = {
    'Écomumaexpressão"servidorweb"serutilizadaparadenominar processoscujafinalidade édisponibilizar':
        'É comum a expressão "servidor web" ser utilizada para denominar processos cuja finalidade é disponibilizar',
    'UmsistemaoperacionalqueutilizaoalgoritmoRoundRobinprecisaexecutardoisprocessos, amboscomtempos':
        'Um sistema operacional que utiliza o algoritmo Round Robin precisa executar dois processos, ambos com tempos',
    '450litros per capita, enquantonaRegiãoNordesteelenãochegouàmetadedestamarca':
        '450 litros per capita, enquanto na Região Nordeste ele não chegou à metade desta marca',
    'Aprevalênciadoprotocoloclínicopautadonotratamentomedicamentosoécondiçãodeterminante':
        'A prevalência do protocolo clínico pautado no tratamento medicamentoso é condição determinante',
    'Númerodecasospor100milhabitantes': 'Número de casos por 100 mil habitantes',
    'CAMPOECONÔMICOESOCIOCULTURAL': 'CAMPO ECONÔMICO E SOCIOCULTURAL',
}
for _g, _c in GRUDADAS.items():
    assert _g.replace(' ', '') == _c.replace(' ', ''), _g

FENCE = re.compile(r'```[^\n`]*\n[\s\S]*?```')

ROMANO = r'(?:I|II|III|IV|V|VI|VII|VIII|IX|X|\||Il|Ill|lI|lll|lV)'
# o que vem depois do rótulo: começo de frase, não "I. Título" de referência
DEPOIS_ROTULO = r'(?=\s+["“(]?[A-ZÀ-Ú0-9])'

# começo de frase de comando — o trecho em que a prova para de contar e
# começa a pedir. Quebra ANTES, só quando há fim de frase antes. Só entra
# o que é comando de verdade: "Nesse caso" e "De acordo com" também abrem
# frase no meio do texto-base e partiam parágrafo onde não havia.
_REFERE = (r'(?:o\s+text|os?\s+dados|as?\s+informa|a\s+situa|o\s+exposto|'
           r'o\s+quadro|o\s+gr[áa]fico|a\s+tabela|a\s+figura|o\s+cen[áa]rio|'
           r'o\s+contexto|ess|est)')
COMANDO = re.compile(
    r'(?:Considerando|Considere(?:-se)?\s+(?:ess|o\s+text|as\s+informa)|'
    r'Com\s+base|Com\s+refer[êe]ncia|Nes[st]e\s+contexto|Nes[st]a\s+situa[çc][ãa]o|'
    r'Nes[st]e\s+cen[áa]rio|Acerca\s+d|A\s+respeito\s+d|'
    rf'A\s+partir\s+d[oa]s?\s+{_REFERE}|De\s+acordo\s+com\s+{_REFERE}|'
    rf'(?:Em|Com)\s+rela[çc][ãa]o\s+(?:a|ao|à|aos|às)\s+{_REFERE}|'
    r'Tendo\s+em\s+vista|Levando\s+em\s+cont|'
    r'Assinale|Avalie|[ÉE]\s+correto|Est[áa]\s+corret|'
    r'Est[ãa]o\s+corret|Fa[çc]a\s+o\s+que\s+se\s+pede|Elabore|Redija)'
)

ITEM_ROMANO = re.compile(rf'{ROMANO}\.{DEPOIS_ROTULO}')
ITEM_LETRA = re.compile(r'[a-h]\)(?=\s+["“(]?[A-Za-zÀ-ú0-9])')
# \uf0b7 é o "•" da fonte Symbol do PDF: um caractere de uso privado que o
# navegador desenha como quadradinho vazio. `espacos` troca por "•".
BULLET = re.compile(r'[•▪●\uf0b7]')
PUA = {'\uf0b7': '•'}
PORQUE = re.compile(r'PORQUE\b')
TEXTO_N = re.compile(r'TEXTO\s+(?:\d{1,2}|[IVX]{1,4})\b')
DISPONIVEL = re.compile(r'Dispon[íi]vel\s+em\s*:')
# "MAGRANI, E.", "TANENBAUM, A. S.", "SEDGEWICK, R.; WAYNE, K.", "BRASIL."
REFERENCIA = re.compile(
    r"(?:[A-ZÀ-Ú][A-ZÀ-Ú'\-]+(?:\s+[A-ZÀ-Ú][A-ZÀ-Ú'\-]+){0,3},\s+(?:[A-ZÀ-Ú]\.\s?)+"
    r"|BRASIL\.\s)"
)
# fim de uma fonte: "(adaptado)." ou o ano seguido de ponto
FIM_FONTE = re.compile(
    r'\((?:adaptado|com\s+adapta[çc][õo]es|adaptada)\)\.?'
    r'|Acesso\s+em\s*:\s*\d{1,2}º?\s+[a-zç]{3,9}\.?\s+\d{4}\.?'
    r'|\b(?:1[89]|20)\d{2}(?:,\s*p\.\s*[\d\-–]+)?\.(?=\s|$)'
)
ADAPTADO = re.compile(r'\s*\((?:adaptado|com\s+adapta[çc][õo]es|adaptada)\)\.?')

# palavra antes de um ponto que NÃO fecha frase
ABREVIACOES = {
    'ed', 'p', 'pp', 'v', 'n', 'nº', 'vol', 'cap', 'fig', 'art', 'inc', 'sr',
    'sra', 'dr', 'dra', 'prof', 'profa', 'aprox', 'ex', 'obs', 'jan', 'fev',
    'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez',
}

PARAGRAFO, ITEM, LINHA = 'paragrafo', 'item', 'linha'


def _fim_de_frase(antes):
    """`antes` (o texto à esquerda do corte) termina uma frase?"""
    s = antes.rstrip()
    if not s:
        return True
    # logo depois de um marcador ("b) Considerando…", "II. Com base…") o
    # que vem é o texto do próprio item, não uma frase nova
    if re.search(rf'(?:^|\s)(?:[a-h]\)|{ROMANO}\.)$', s):
        return False
    ultimo = s[-1]
    if ultimo in '?!:;”"»)':
        return True
    if ultimo != '.':
        return False
    m = re.search(r'(\S+)\.$', s)
    palavra = m.group(1) if m else ''
    if re.fullmatch(r'[A-ZÀ-Ú]', palavra):         # inicial de nome: "E."
        return False
    return palavra.lower().strip('(') not in ABREVIACOES


def _cortes(linha, comandos=True):
    """-> [(posição, tipo)] onde a linha deve quebrar, em ordem.

    `tipo` diz o que COMEÇA na posição: um item de lista (que encosta no
    item anterior com uma quebra simples) ou um parágrafo (linha em branco).
    """
    cortes = {}

    def corta(pos, tipo, exige_fim=True):
        if pos <= 0 or pos >= len(linha):
            return
        if exige_fim and not _fim_de_frase(linha[:pos]):
            return
        # parágrafo vence item no mesmo ponto
        if cortes.get(pos) != PARAGRAFO:
            cortes[pos] = tipo

    for m in ITEM_ROMANO.finditer(linha):
        corta(m.start(), ITEM)
    for m in ITEM_LETRA.finditer(linha):
        corta(m.start(), ITEM)
    for m in BULLET.finditer(linha):
        corta(m.start(), ITEM, exige_fim=False)
    for m in (COMANDO.finditer(linha) if comandos else ()):
        antes = linha[:m.start()].rstrip()
        # comando colado no fim de uma tabela achatada ("…4 3 2 Considerando
        # essas informações"): a palavra é maiúscula no meio da linha, então
        # não há frase sendo cortada
        depois_de_tabela = bool(re.search(r'[\d|]$', antes)) and \
            not re.search(rf'(?:^|\s)(?:[a-h]\)|{ROMANO}\.)$', antes)
        corta(m.start(), PARAGRAFO, exige_fim=not depois_de_tabela)
    for m in PORQUE.finditer(linha):
        corta(m.start(), PARAGRAFO, exige_fim=False)
        corta(m.end(), PARAGRAFO, exige_fim=False)
    for m in TEXTO_N.finditer(linha):
        corta(m.start(), PARAGRAFO, exige_fim=False)
        corta(m.end(), LINHA, exige_fim=False)
    fontes = [m.start() for m in DISPONIVEL.finditer(linha)]
    # referência começa depois de ponto, não de ";" — senão cada autor de
    # "GOMES, R.; NASCIMENTO, E.; ARAUJO, F." vira um parágrafo
    fontes += [m.start() for m in REFERENCIA.finditer(linha)
               if _fim_de_frase(linha[:m.start()])
               and not linha[:m.start()].rstrip().endswith((';', ':', ','))]
    ate = -1
    for ini in sorted(fontes):
        if ini < ate:
            continue                       # dentro da fonte anterior
        corta(ini, PARAGRAFO, exige_fim=False)
        fim = FIM_FONTE.search(linha, ini, min(len(linha), ini + 400))
        if fim:
            # "Acesso em: 1 mar. 2023" ainda pode ter "(adaptado)." depois
            resto = ADAPTADO.match(linha, fim.end())
            fim_pos = resto.end() if resto else fim.end()
            # a fonte é um parágrafo inteiro: o que vem depois também quebra
            corta(fim_pos, PARAGRAFO, exige_fim=False)
            ate = fim_pos
    return sorted(cortes.items())


def _tipo_inicio(texto):
    """Tipo de uma linha pelo começo — para decidir como ela encosta na
    anterior quando a quebra já existia."""
    t = texto.lstrip()
    if ITEM_ROMANO.match(t) or ITEM_LETRA.match(t) or BULLET.match(t):
        return ITEM
    return PARAGRAFO


def _separador(tipo_antes, tipo_agora):
    if tipo_agora == LINHA:
        return '\n'
    if tipo_agora == ITEM and tipo_antes == ITEM:
        return '\n'
    return '\n\n'


def _ultima_linha(texto):
    return texto.rsplit('\n', 1)[-1]


def _estrutura_prosa(prosa, comandos=True):
    """Quebra um trecho sem código. Quebras que já existem ficam como estão;
    as novas saem dos `_cortes` de cada linha.

    O separador olha a LINHA de cima, não o "tipo do bloco": um item só
    encosta no anterior (quebra simples) se a linha de cima também começa
    com marcador. É a mesma regra do `_reflui_prosa` — com regras
    diferentes, a segunda passada trocava as quebras da primeira.
    """
    blocos = re.split(r'(\n+)', prosa)
    saida = ''
    for k, bloco in enumerate(blocos):
        if k % 2 == 1:                      # separador existente
            if saida:
                saida += '\n\n' if len(bloco) > 1 else '\n'
            continue
        if not bloco.strip():
            continue
        ultimo = 0
        pedacos = []
        for pos, tipo in _cortes(bloco, comandos):
            pedacos.append((bloco[ultimo:pos], tipo))
            ultimo = pos
        pedacos.append((bloco[ultimo:], None))
        # o tipo de um pedaço é o do corte que o ABRIU (o anterior na lista)
        abriu = None
        for texto, proximo in pedacos:
            p = texto.strip()
            if p:
                if abriu is not None and saida and not saida.endswith('\n'):
                    saida += _separador(_tipo_inicio(_ultima_linha(saida)), abriu)
                saida += p
            abriu = proximo
    # nunca mais de uma linha em branco, nem quebra nas pontas
    return re.sub(r'\n{3,}', '\n\n', saida).strip()


def _por_fora_do_codigo(texto, funcao):
    """Aplica `funcao` só fora dos blocos ```; os blocos voltam intactos,
    cada um na sua linha."""
    partes, ultimo = [], 0
    for m in FENCE.finditer(texto):
        if m.start() > ultimo:
            partes.append(funcao(texto[ultimo:m.start()]))
        partes.append(m.group(0))
        ultimo = m.end()
    if ultimo < len(texto):
        partes.append(funcao(texto[ultimo:]))
    return '\n'.join(p for p in partes if p and p.strip()).strip()


def espacos(texto):
    """Correções que só mexem em espaço: palavras grudadas, hífen de fim de
    linha que virou "matéria- prima", fonte colada no ponto final."""
    if not texto:
        return texto

    def conserta(t):
        for grudado, certo in GRUDADAS.items():
            t = t.replace(grudado, certo)
        # "matéria- prima" -> "matéria-prima"; mas o hífen suspenso fica:
        # "pré- e pós-operatório" não é "pré-e"
        t = re.sub(r'(?<=[A-Za-zÀ-ÿ])- (?=[a-zà-ÿ])(?!(?:e|ou|a|até)\s)', '-', t)
        t = re.sub(r'(?<=[.)”"])(?=Dispon[íi]vel\s+em)', ' ', t)
        for pua, certo in PUA.items():
            t = t.replace(pua, certo)
        return t

    return _por_fora_do_codigo(texto, conserta) if '```' in texto else conserta(texto)


def estrutura(texto, comandos=True):
    """Parágrafos pela estrutura da prova. Idempotente: rodar de novo sobre a
    própria saída não muda nada.

    `comandos=False` para o padrão de resposta: lá não há comando de questão,
    e "Com base…" ou "Considerando…" são frases do meio do texto."""
    if not texto:
        return texto
    t = _por_fora_do_codigo(
        espacos(texto), lambda p: _estrutura_prosa(p, comandos))
    return _separa_pergunta(t) if comandos else t


def _separa_pergunta(texto):
    """Põe a pergunta final da questão no seu próprio parágrafo.

    Muitas objetivas terminam com a frase que leva às alternativas emendada
    no texto-base ("…o menor tempo possível para o acionamento do alarme é
    de"). Ela é reconhecível por terminar SEM ponto final — em "é de",
    "será", ":" ou "?". Frase final com ponto é texto-base e fica onde está.
    """
    if texto.rstrip().endswith('```'):
        return texto
    corpo, sep, ultimo = texto.rpartition('\n\n')
    if ('\n' in ultimo or len(ultimo) < 300 or _tipo_inicio(ultimo) == ITEM
            or ultimo.rstrip().endswith('.')):
        return texto
    fronteiras = [
        m.start() for m in re.finditer(r'(?<=[.?!])\s+(?=["“(]?[A-ZÀ-Ú])', ultimo)
        if _fim_de_frase(ultimo[:m.start()])
    ]
    if not fronteiras:
        return texto
    k = fronteiras[-1]
    pergunta = ultimo[k:].strip()
    if len(pergunta) < 25:
        return texto
    return corpo + sep + ultimo[:k].rstrip() + '\n\n' + pergunta


# --------------------------------------------------------------------------
# Linhas do PDF -> parágrafos
# --------------------------------------------------------------------------

TERMINAL = re.compile(r'[.?!:;]["”»)]*$|\)$')


def _tabular(linha):
    """Linha de tabela: várias células curtas ("A B C Z", "1 0 0 0")."""
    celulas = linha.split()
    # célula de tabela: maiúscula, dígito ou x — "e o de" é texto corrido
    return len(celulas) >= 2 and all(
        len(c) <= 3 and re.fullmatch(r'[A-Z0-9xX.,%\-]+', c) for c in celulas)


def _tipo_fim(linha, comandos=True):
    """Tipo do ÚLTIMO pedaço da linha depois dos cortes da estrutura.

    Uma linha emendada pode terminar no meio de uma lista ("… a seguir. a)
    Apresente… b) Considerando…"): o item seguinte encosta nela com quebra
    simples, embora a linha comece como parágrafo."""
    cortes = _cortes(linha, comandos)
    return cortes[-1][1] if cortes else _tipo_inicio(linha)


def _reflui_prosa(prosa, comandos=True):
    linhas = [l.strip() for l in prosa.split('\n')]
    # "•" sozinho numa linha é o marcador do item da linha de baixo
    juntas = []
    for l in linhas:
        if juntas and BULLET.fullmatch(juntas[-1] or ''):
            juntas[-1] = juntas[-1] + ' ' + l
        else:
            juntas.append(l)
    linhas = juntas

    # Largura da coluna = mediana das linhas que quebram no meio da frase
    # (as que não terminam em pontuação). Mediana, não máximo: o
    # `parser.limpar_texto` já emendou parte das linhas, e uma linha emendada
    # tem o dobro da largura — com ela de régua, toda linha normal pareceria
    # "curta" e viraria quebra dura.
    quebradas = sorted(len(l) for l in linhas
                       if len(l) >= 30 and not TERMINAL.search(l))
    if len(quebradas) >= 2:
        largura = quebradas[len(quebradas) // 2]
    elif any(len(l) >= 40 for l in linhas):
        largura = max(len(l) for l in linhas)
    else:
        # só linhas curtas: tabela, código ou lista — fica como veio
        return '\n'.join(l for l in linhas if l)

    saida = ''
    for i, linha in enumerate(linhas):
        if not linha:
            if saida and not saida.endswith('\n\n'):
                saida = saida.rstrip('\n') + '\n\n'
            continue
        if not saida or saida.endswith('\n'):
            saida += linha
            continue
        anterior = saida.rsplit('\n', 1)[-1]
        prev_linha = linhas[i - 1] if i > 0 else ''
        # a primeira palavra de baixo caberia na linha de cima? Se não
        # caberia, a linha acabou cedo por falta de espaço (uma URL longa,
        # uma palavra comprida) e não por fim de parágrafo
        primeira = linha.split()[0]
        nao_cabia = len(prev_linha) + 1 + len(primeira) > largura
        if _tipo_inicio(linha) == ITEM or TEXTO_N.match(linha) \
                or PORQUE.match(linha) or DISPONIVEL.match(linha):
            saida += _separador(_tipo_fim(anterior, comandos),
                                _tipo_inicio(linha)) + linha
        elif _tabular(linha):
            saida += '\n' + linha             # cabeçalho/linha de tabela
        elif len(prev_linha) >= max(30, 0.7 * largura) or \
                (nao_cabia and len(prev_linha) >= 12):
            # linha cheia: o texto continua na de baixo
            if prev_linha.endswith('-') and re.match(r'[a-zà-ÿ]', linha):
                saida += linha
            else:
                saida += ' ' + linha
        elif TERMINAL.search(prev_linha):
            saida += '\n\n' + linha            # linha curta com ponto: fim
        else:
            saida += '\n' + linha              # tabela, código, título
    return saida.strip()


def reflui(texto, comandos=True):
    """Junta as linhas do PDF em parágrafos e aplica a estrutura da prova.

    Para texto que AINDA tem uma quebra por linha do PDF (extração, padrão
    de resposta). Para texto já achatado, use `estrutura`.
    """
    if not texto:
        return texto
    return estrutura(
        _por_fora_do_codigo(texto, lambda p: _reflui_prosa(p, comandos)),
        comandos)


# --------------------------------------------------------------------------
# Reaplicar no banco do site
# --------------------------------------------------------------------------

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANCO = os.path.join(RAIZ, 'app', 'static', 'banco')


def _visivel(t):
    t = t or ''
    for pua, certo in PUA.items():
        t = t.replace(pua, certo)
    return re.sub(r'\s', '', t)


# Linha crua de PDF não passa de ~115 caracteres (a maior no banco tem 112);
# linha mais longa que isto já é parágrafo emendado por uma passada anterior.
LINHA_CRUA_MAX = 200


def _ja_refluido(texto):
    sem_codigo = FENCE.sub('', texto or '')
    return any(len(l) > LINHA_CRUA_MAX for l in sem_codigo.split('\n'))


def formata_padrao(texto):
    """Padrão de resposta guardado no banco: as linhas do PDF ainda estão lá
    na primeira vez; depois disso, só a estrutura. Refluir de novo um texto
    já refluído mediria a "largura da coluna" sobre parágrafos, e as listas
    curtas terminadas em ";" seriam emendadas."""
    if _ja_refluido(texto):
        return estrutura(texto, comandos=False)
    return reflui(texto, comandos=False)


def reaplicar_banco():
    """Reformata enunciado, padrão e alternativas dos JSON das provas.

    O enunciado no banco já está achatado (só `estrutura`); o padrão ainda
    tem as linhas do PDF na primeira vez (`formata_padrao`). Grava só se
    nenhum caractere visível mudou e se uma segunda passada não muda nada —
    rodar o comando duas vezes tem de dar o mesmo banco.
    """
    import digita

    # padrão lido do PDF (`_padrao` em digitadas.json) nunca é "linha crua":
    # com linhas curtas de código fora do bloco, `_ja_refluido` o tomaria
    # por texto do PDF e `reflui` brigaria com `digita.finaliza`
    lidos = {qid for qid, b in digita.carregar().items()
             if b.get('_padrao') or b.get('_nova')}

    def padrao(q):
        return (lambda t: estrutura(t, comandos=False)) if q['id'] in lidos else formata_padrao

    total = mudou = 0
    problemas = []
    arquivos = {}
    for arq in sorted(glob.glob(os.path.join(BANCO, 'enade*.json'))):
        with open(arq, encoding='utf-8') as fh:
            qs = json.load(fh)
        arquivos[arq] = qs
        for q in qs:
            total += 1
            antes = json.dumps(q, ensure_ascii=False)
            for campo, f in (('enunciado', estrutura), ('padrao', padrao(q))):
                if not q.get(campo):
                    continue
                novo = f(q[campo])
                if _visivel(novo) != _visivel(q[campo]):
                    problemas.append(f'{q["id"]} {campo}: mudou texto visível')
                    continue
                if f(novo) != novo:
                    problemas.append(f'{q["id"]} {campo}: segunda passada muda')
                    continue
                q[campo] = novo
            alt = q.get('alternativas') or {}
            for letra, txt in alt.items():
                novo = espacos(txt)
                if _visivel(novo) == _visivel(txt):
                    alt[letra] = novo
            if json.dumps(q, ensure_ascii=False) != antes:
                mudou += 1
    if problemas:
        print('NADA GRAVADO:')
        for p in problemas:
            print('  ' + p)
        return 1
    # grava só depois de conferir TODOS os arquivos: um problema no último
    # não pode deixar os primeiros já reescritos
    for arq, qs in arquivos.items():
        with open(arq, 'w', encoding='utf-8', newline='\n') as fh:
            json.dump(qs, fh, ensure_ascii=False, indent=1)
            fh.write('\n')
    print(f'{mudou} de {total} questões reformatadas')
    return 0


if __name__ == '__main__':
    if '--banco' in sys.argv:
        sys.exit(reaplicar_banco())
    print(__doc__)
