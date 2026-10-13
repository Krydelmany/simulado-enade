"""Formatação do enunciado: código, matemática e legibilidade.

O extrator entrega o enunciado como o PDF traz: o texto corrido. Numa prova
de Engenharia de Computação isso é ruim de ler — um trecho de Java aparece
colado na frase ("…no vetor a[lo..hi]. public class MergeSort { private
static…"), e o identificador `LED1` chega como `LED1` em vez de LED com
índice 1.

Aqui essas coisas viram marcação, nunca texto novo:

- trecho de código vira bloco ``` delimitado, que o `TextoRico.svelte`
  renderiza em monoespaçada com quebra correta;
- índice de identificador vira subscrito (LED₁, x₁, IC₁B) — o índice é
  parte do nome do componente, e ler "LED1" como "LED um" muda o circuito;
- o operador `<` digitalizado como `1` volta a ser `<` — `1<i, j` estava
  significando `<i, j`;
- some o número de linha que o PDF imprime ao lado do código ("2 if low ==
  None") e a régua de separação ("--- VHDL: //---"), que viram parte da
  linha de código e confundem quem lê.

Cada regra aqui tem que ser segura: uma troca errada neste arquivo aparece
na frente do aluno como enunciado com sentido diferente. Onde a regra não
tem certeza, ela não age — a porta de qualidade (`qualidade.py`) é quem
decide se a questão sai.
"""

import re

# --------------------------------------------------------------------------
# 1. Subscritos de identificador
#
# O PDF escreve LED com "1" subscrito; a camada de texto achata tudo na mesma
# linha. Só vale para identificadores que sabemos ser indexados, senão
# "Lei 12.965/2014", "Q1", "D1", "ENADE 2014" viram lixo.
# --------------------------------------------------------------------------
SUBSCRITO = {str(d): chr(0x2080 + d) for d in range(10)}  # ₁ ₂ ₃ …

# prefixos de componente/varíavel que o INEP indexa
PREFIXOS_INDEXADOS = (
    'LED', 'CH', 'SW', 'IC', 'R', 'C', 'L', 'S', 'G', 'D', 'T', 'M', 'X', 'Y',
    'A', 'B', 'E', 'F', 'P', 'N', 'Q', 'K', 'W', 'H', 'U', 'V', 'Z', 'J',
    'CLK', 'RESET', 'SEL', 'EN', 'ADDR', 'DATA', 'OUT', 'IN', 'TABELA', 'TAB', 'SPK', 'COL', 'LIN',
)

RX_INDICE = re.compile(
    r'(?<![A-Za-z0-9_])('
    + '|'.join(sorted(PREFIXOS_INDEXADOS, key=len, reverse=True))
    + r')(\d{1,2})(?![0-9])'
)

# x_1, x_2, ... x_k, x_n — variáveis de sequência, o INEP usa minúscula
RX_SEQUENCIA = re.compile(r'(?<![A-Za-z0-9])([a-z])(\d{1,2})(?![0-9])')

# 2. Código
# --------------------------------------------------------------------------
# Régua do PDF: `---------------- VHDL: //---------------`.
#
# A linha INTEIRA é régua, nada mais. O padrão anterior (`-{4,}\s*\w+:?...`)
# sem âncora matchava no meio de qualquer linha de código e COMIA o
# conteúdo — `OpenHayesChannel((Hayes&)m, frq);` virava
# `OpenHayesChannel((Hayesm, frq);`, porque o `&` era lido como "&" da régua.
# Régua que não é a linha inteira não é régua.
RX_RÉGUA = re.compile(
    r'^\s*-{4,}\s*(?:[A-Za-z#][\w .+/-]{0,24}:?\s*)?(?://\s*-*|-\s*//\s*-*)?-*\s*$'
)
RX_RÉGUA_BARRA = re.compile(r'^\s*//-{4,}\s*$')
# Número de linha que o PDF imprime na margem e o OCR cola no começo do
# código: "2 if low == None", "16 OpenHayesChannel(…)". Só remove quando o
# que vem DEPOIS é inequivocamente código — senão "202 pessoas" perdia o 202.
RX_LINHA_NUM = re.compile(
    r'(?<![A-Za-z0-9_])(?<![\d.])(\d{1,2}) (?='
    r'(?:if |elif |else|for |while |return |def |class |public |private |'
    r'struct |enum |int |void |char |float |double |#|@|end|begin|endmod|'
    r'library |use |entity |port |architecture |process|variable|case |'
    r'else|input |output |wire |reg |logic |port |elsif |'
    r'//|/\*|\w+\s*[({=;+\-*/])'
    r')'
)

# Uma linha só é código quando tem sinal forte E a forma é de código.
#
# O sinal sozinho não basta: `\bdo\b\s` casa com "aumento do volume" e
# `\bif\s*\(` casa com "se (algo)". Por isso há três portas, em ordem:
#
#   1. citação de fonte e URL nunca são código;
#   2. sinal que não existe em português (`{`, `=>`, `#include`, `//`, `&x`,
#      os literais `None`/`null`, `range 0 to 3`) decide sozinho;
#   3. sinal típico de código só vale junto com densidade — texto corrido fica
#      na mediana de 5,1 letra por palavra, código abaixo disso.
#
# Errar para "não é código" deixa o trecho feio; errar para "é código" parte a
# frase ao meio na tela. Daí a assimetria: a porta 3 existe, a que faria o
# contrário não.
#
# Nível 1 — impossível em português, decide sozinho.
RX_CERTO = [
    # Bloco/escopo. A `{` solta é código; `{-1, +1}` é conjunto matemático.
    re.compile(r'\}\s*;?\s*$|\}\s*(?:else|\))|\{\s*$|\{\s+[A-Za-z_]'),
    re.compile(r'#\s*(?:include|define|pragma|import)\b'),  # diretiva C/PHP
    re.compile(r'=>|::|\|\||&&|\?\?|:=|\+\+|--'),
    re.compile(r'(?<![:\w])//(?!/)'),                   # comentário de linha
    # endereço de memória: `&salariol`. O `&` colado no nome é o que separa do
    # "e comercial" do português, que vem com espaço dos dois lados.
    re.compile(r'(?<![\s&])&\s*[A-Za-z_]\w*'),
    re.compile(r'\b(?:None|True|False|null|undefined|NULL|TRUE|FALSE|Nil)\b'),
    re.compile(r'\b(?:std_logic|std_logic_1164|posedge|negedge|'
               r'entity\s+\w+\s+is\b|port\s*\(|endmodule|endcase|endtask)'),
    re.compile(r'\b0x[0-9A-Fa-f]{2,}\b\s*=\s*'),         # literal hex em código
    re.compile(r'\brange\s+\d+\s+to\s+\d+'),             # VHDL/Ada
    re.compile(r'^\s*(?:var|let|const)\s+\w+\s*='),
    re.compile(r'^\s*(?:return|break|continue|pass|raise)\s*;?\s*$'),
    re.compile(r'^\s*end(?:if|while|for|module|case|task|function)?\s*[;:]?\s*$'),
    # `private static Comparable[] aux;` — modificador de acesso que não existe
    # em português ("privada" não é "private"), seguido de tipo e nome
    re.compile(r'\b(?:public|private|protected|static|abstract)\s+'
               r'(?:static\s+|final\s+|abstract\s+|unsigned\s+)*'
               r'[\w<>\[\]]+\s+[\w<>\[\]*]+\s*[=;,(]'),
    # alocação: `aux = new Comparable[a.length];`
    re.compile(r'=\s*new\s+\w+\s*[(\[]'),
    # assinatura de tipo de função: `quicksort :: [Int] -> [Int]`
    re.compile(r'\w+\s*::\s*[\w\[\]()*\s.,]*->'),
]

# Nível 2 — típico de código, mas a palavra também existe em português. Precisa
# da densidade junto.
RX_FORTES = [
    re.compile(r'^\s*(?:SELECT|INSERT\s+INTO|UPDATE|DELETE\s+FROM|'
               r'CREATE\s+TABLE|WHERE|GROUP\s+BY)\b', re.I),
    re.compile(r'^\s*(?:<[a-z][a-z0-9]*[\s>/]|<\?php|\$\w+\s*=|->\s*\$?\w)'),
    re.compile(r'\bSystem\.out|console\.log|printf\s*\(|cin\s*[<>]|cout\s*<<'),
    # chamada de função que ocupa a linha inteira e termina em `;`
    re.compile(r'^\s*[A-Za-z_]\w*(?:\s*\[[^\]]*\])*\s*\([^()]*\)\s*;\s*$'),
    # duas ou mais chamadas na mesma linha: `quicksort(a); quicksort(b);`
    re.compile(r'^\s*\w+\([^()]*\);\s*\w+\s*\([^()]*\);\s*$'),
    re.compile(r'^\s*@\w+[\w.]*\s*[({]'),               # anotação Java
    re.compile(r'^\s*(?:int|char|float|double|void|bool|boolean|long|'
               r'unsigned|short|byte)\s+[\w<>\[\]]+\s+\w+\s*[=;,(]'),
    re.compile(r'^\s*(?:struct|enum|typedef|namespace|package|interface|'
               r'class|def|function|module|architecture|process|entity)\s+\w'),
    re.compile(r'^\s*(?:input|output|inout)\s+(?:wire|reg|logic|bit)?\s*\w'),
    # atribuicao, com indice no alvo: `aux[k] = a[k];`
    re.compile(r'\b\w+(?:\s*\[[^\]]*\])*\s*(?:=|\+=|-=|\*=|/=)\s*[^=]*\s*;\s*$'),
    re.compile(r'^\s*=\s*[^=]+\s*;\s*$'),                # atribuição sem alvo
    # Palavra-chave no início. "for" é preposição em português ("for o
    # fluido"), então o que vem depois decide: `for (`, `for i in lst:` ou
    # `for x != y:` são código; "for o fluido, maior será" não é.
    re.compile(r'^\s*(?:if|elif|else|for|while|switch|case|return)\s*\('),
    re.compile(r'^\s*(?:for|while|if|elif)\s+\w+\s+(?:in\s|not\s|[<>=!]=)'),
    re.compile(r'^\s*(?:if|elif|else|for|while)\b.*:\s*$'),
    re.compile(r'\b\w+\s*(?:<=|>=|==|!=)\s*[\w(][^;]*;\s*$'),  # comparação
    re.compile(r'\b\w+\s*:\s*(?:integer|bit|std_logic|real|out|in|text)\b'),
]

# Nível 3 — palavra de código sem nenhum outro sinal. Só vale DENTRO de um
# bloco que já começou: `begin`, `else`, `);` e `end if;` não têm símbolo
# próprio, mas nenhuma frase de prova começa com "begin" nem fecha parêntese
# sozinha.
RX_SO_DENTRO = [
    re.compile(r'^\s*(?:begin|else|elsif|is\s*$|of\s+\w+\s+is\b|'
               r'end\s+(?:if|process|entity|architecture|module|case|task|'
               r'function|loop)\b)'),
    re.compile(r'^\s*[);]\s*$'),                       # fecha parêntese solto
    re.compile(r'^\s*\w+\s*[;,]\s*$'),                  # item de lista
]

# nunca código, mesmo com sinal forte: citação de fonte e URL
RX_NAO_CODIGO = re.compile(
    r'Disponível em|Acesso em|\(adaptado\)|http[s]?://|Disponível', re.I
)

RX_LETRAS = re.compile(r'[A-Za-zÀ-ÿ]')

# texto corrido fica na mediana de 5,1 letra por palavra; código real, abaixo.
LIMITE_DENSIDADE = 5.0


def _densao(linha):
    """Letras por palavra. Código é mais "chapado" que prosa."""
    palavras = linha.split()
    if not palavras:
        return 99.0
    return len(RX_LETRAS.findall(linha)) / len(palavras)


def _codigo_da_linha(linha, dentro=False):
    """A linha é código?

    `dentro` diz que a linha anterior já era código. Nesse caso as linhas de
    continuação (`begin`, `);`, `end if;`) também contam, porque nenhuma frase
    de prova começa com "begin" nem fecha parêntese sozinha.

    Três portas em ordem: citação/URL nunca é; sinal impossível em português
    sempre é; sinal típico só vale com densidade de código junto. Errar para
    "não é código" deixa o trecho feio; errar para "é código" parte a frase ao
    meio na tela — por isso a assimetria.
    """
    if RX_NAO_CODIGO.search(linha):
        return False
    if any(rx.search(linha) for rx in RX_CERTO):
        return True
    if not any(rx.search(linha) for rx in RX_FORTES):
        return dentro and any(rx.search(linha) for rx in RX_SO_DENTRO)
    return _densao(linha) < LIMITE_DENSIDADE


def separa_codigo(texto):
    """-> [(tipo, valor)] com tipo 'texto' ou 'codigo'.

    Agrupa linhas de código consecutivas num bloco só. Uma linha isolada
    que só parece código (uma frase com `;` de citação) continua texto.
    """
    if not texto:
        return []
    linhas = [ln for ln in texto.split('\n') if not RX_RÉGUA_BARRA.match(ln)]
    partes = []
    buffer = []

    def fecha():
        if buffer:
            partes.append(('codigo', '\n'.join(buffer)))
            buffer.clear()

    for ln in linhas:
        if _codigo_da_linha(ln, dentro=bool(buffer)):
            buffer.append(ln)
        else:
            fecha()
            partes.append(('texto', ln))
    fecha()
    return partes


def normaliza_codigo(cod):
    """Tira número de linha e régua do PDF de dentro do bloco."""
    cod = RX_RÉGUA.sub('', cod)
    linhas = []
    for ln in cod.split('\n'):
        # número de linha no início, colado no código ("2 if low == None")
        ln = RX_LINHA_NUM.sub('', ln, count=1)
        linhas.append(ln.rstrip())
    return '\n'.join(linhas).strip('\n')


# --------------------------------------------------------------------------
# 3. Formatação do enunciado inteiro
# --------------------------------------------------------------------------


def arruma_texto(t):
    if not t:
        return t

    # As URLs e os blocos de código saem de cena antes de qualquer regra:
    # ambos têm ponto, barra e dois-pontos, e as regras de pontuação
    # bagunçariam os dois (a URL virava "http: //www…" e deixava de ser link;
    # dentro do código, `aux [k]` virava `aux[k]` e o operador de ponteiro
    # colava no nome). Cada um volta no fim, intacto.
    guarda = []

    def protege(m):
        guarda.append(m.group(0))
        return f'\x00{len(guarda) - 1}\x00'

    t = re.sub(r'```[\w]*\n[\s\S]*?```', protege, t)
    t = re.sub(r'https?://[^\s<>]+|https?:/(?!\s)[^\s<>]+', protege, t)

    t = RX_RÉGUA.sub('', t)
    # O "<" às vezes vem duplicado no OCR: `1<i, j` era `<i, j`. Exige o "<"
    # logo depois, senão "chave 1 (CH1)" viraria "chave <(CH1)".
    t = re.sub(r'(?<=[\s(,;])1(\s*<)', r'\1', t)

    t = RX_INDICE.sub(
        lambda m: m.group(1) + ''.join(SUBSCRITO[d] for d in m.group(2)),
        t,
    )
    t = RX_SEQUENCIA.sub(
        lambda m: m.group(1) + ''.join(SUBSCRITO[d] for d in m.group(2)), t
    )
    # espaço que o OCR colou antes da vírgula/ponto: "int a , int b"
    t = re.sub(r'\s+([,;.:!?])', r'\1', t)
    t = re.sub(r'([,;:])(?=[^\s\d])', r'\1 ', t)
    t = re.sub(r' {2,}', ' ', t)

    # devolve o que foi protegido
    t = re.sub(r'\x00(\d+)\x00', lambda m: guarda[int(m.group(1))], t)
    return t.strip()


def _juncla_codigo(partes):
    """Garante quebra de linha nos dois lados de cada bloco de código.

    Sem isto a marcação fica `texto ```c\\n…```texto` com o ``` colado na
    frase — e o renderizador lê ```texto como nome de linguagem do bloco, e
    some com a última linha de código junto. A quebra tem que vir ANTES (o
    fence abre linha) e DEPOIS (o fence fecha linha).
    """
    saida = []
    for tipo, valor in partes:
        if tipo == 'codigo':
            if saida:
                antes_tipo, antes = saida[-1]
                if antes_tipo == 'texto' and not antes.endswith('\n'):
                    saida[-1] = ('texto', antes + '\n')
        elif saida and saida[-1][0] == 'codigo' and not valor.startswith('\n'):
            valor = '\n' + valor
        saida.append((tipo, valor))
    return saida


def _com_blocos(texto, lang):
    """Reescreve o texto colocando ``` em volta de cada trecho de código."""
    partes = _juncla_codigo(separa_codigo(texto))
    saida = []
    for tipo, valor in partes:
        if tipo == 'texto':
            saida.append(valor)
            continue
        cod = normaliza_codigo(valor)
        if cod:
            saida.append(f'```{lang}\n{cod}\n```')
    return '\n'.join(saida).replace('\n\n\n', '\n\n').strip()


def formata(q):
    """Devolve a questão com enunciado, padrão e alternativas formatados.

    A linguagem é detectada por enunciado E alternativas juntas, porque a
    alternativa costuma ser justamente o código: é nela que está o `malloc`
    que diz que o enunciado é C, e é nela que está o `{` que fecha o bloco
    aberto no enunciado.
    """
    q = dict(q)
    lang = _linguagem(q)
    for campo in ('enunciado', 'padrao'):
        if q.get(campo):
            q[campo] = arruma_texto(_com_blocos(q[campo], lang))

    alt = q.get('alternativas') or {}
    if alt:
        novo = {}
        for letra, txt in alt.items():
            v = _com_blocos(txt, lang)
            novo[letra] = arruma_texto(v)
        q['alternativas'] = novo
    return q


# Ordem importa: a primeira que casar vence, então o sinal mais específico vem
# antes. Um enunciado que fala em Java e mostra SQL (consulta ao banco) tem as
# duas coisas — o que decide é qual delas é o TRECHO, não o tema da questão.
LINGUAGENS = [
    (r'\b(?:std_logic|std_logic_1164|posedge|negedge|endmodule|'
     r'entity\s+\w+\s+is\b|architecture\s+\w+\s+of\b|port\s*\()', 'vhdl'),
    (r'\b(?:SELECT\b|INSERT\s+INTO|UPDATE\s+\w+\s+SET\b|'
     r'DELETE\s+FROM\b|CREATE\s+TABLE\b)', 'sql'),
    (r'\b(?:def\s+\w+\s*\(|elif\s|None\b|True\b|False\b|print\s*\()', 'python'),
    (r'(?:<\?php|\$this\s*=|->\w+\s*\(|\bnamespace\s+\w)', 'php'),
    (r'\b(?:System\.out|public\s+static\s+void|public\s+class|private\s+\w+\s+\w+\s*[=;]|'
     r'String\[\]|@Override|@WebServlet|extends\s+HttpServlet|HttpServlet)', 'java'),
    (r'(?:#include\s*<|\bprintf\s*\(|\bscanf\s*\(|\bmalloc\s*\(|\bfree\s*\(|'
     r'\bint\s+main\s*\(|\bstruct\s+\w+\s*\{|\btypedef\b|\bchar\s*\*|'
     r'\b(?:int|char|float|double|void)\s+\**\w+\s*[=(;])', 'c'),
    (r'^\s*<\?xml|</?[a-z]+[^>]*>\s*$', 'xml'),
    (r'^\s*<[a-z][a-z0-9]*(?:\s+[^>]*)?>', 'html'),
]

# o sinal mais frequente vence: a linguagem que mais aparece no trecho
# é a dele
_RECONTAGEM = [(re.compile(rx, re.I | re.M), lang) for rx, lang in LINGUAGENS]


def _linguagem(q):
    """Adivinha a linguagem do TRECHO — só para destacar a sintaxe, nunca
    decide o conteúdo. Devolve 'text' quando não dá para saber, que é o
    honesto: pintar de java um código C ajuda menos do que não pintar.
    """
    texto = '\n'.join(
        [q.get('enunciado') or '', q.get('padrao') or '',
         '\n'.join((q.get('alternativas') or {}).values())]
    )
    melhor = ('text', 0)
    for rx, lang in _RECONTAGEM:
        n = len(rx.findall(texto))
        if n > melhor[1]:
            melhor = (lang, n)
    return melhor[0] if melhor[1] else 'text'
