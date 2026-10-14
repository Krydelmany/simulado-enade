"""Testes do `formato.py`, do `paragrafo.py` e do texto lido do PDF.

Rodar: `python3 banco/testes.py`

Existe porque a detecção de código é uma heurística e heurística sem teste
regressa. Estes casos saíram de linhas reais das provas — o lado do texto são
frases que JÁ foram marcadas como código por engano (o bug que pintou 127 das
159 questões de monoespaçada), e o lado do código são trechos que precisam
entender. Se um teste quebrar, a linha diante do aluno mudou de cara — leia o
caso antes de mexer no limite.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import formato  # noqa: E402
import paragrafo  # noqa: E402
import digita  # noqa: E402

# (linha, é_código?)
CASOS = [
    # ---- texto corrido que JÁ foi classificado como código por engano ----
    ('e substitua lâmpadas incandescentes por', False),
    ('fluorescentes compactas ou lâmpadas de LED;', False),
    ('na posição "inverno" ou "quente";', False),
    ('1. Reflexividade. Para todo a Î S, a R a;', False),
    ('Mesmo com o aumento do volume de alimentos, o número de indivíduos '
     'subnutridos é grande, como', False),
    ('A ONU define esse desenvolvimento como aquele que assegura qualidade '
     'de vida, incluídos os componentes', False),
    ('A pé 15,9', False),
    ('A respeito dessas asserções, assinale a opção correta.', False),
    ('Os desafios da mobilidade urbana associam-se à necessidade de '
     'desenvolvimento', False),
    ('Modalidade Tipologia Porcentagem (%)', False),
    ('a) consequências, para o desenvolvimento sustentável, do uso do '
     'transporte', False),
    ('k é a rugosidade equivalente da parede do tubo (m);', False),
    ('f é o fator de atrito de Darcy-Weisbach (adimensional);', False),
    ('Chuveiro 3 500 W 3,500 0,5 1,750', False),
    ('for o fluido, maior será a perda de energia. A forma', False),
    ('for euleriano, então o PCV pode ser resolvido', False),
    ('Tendo em vista o texto e o quadro de mobilidade urbana apresentados, '
     'redija um texto', False),
    # ---- código que precisa ser reconhecido ----
    ('public class MergeSort {', True),
    ('private static Comparable[] aux;', True),
    ('int i = lo, j = mid+1;', True),
    ('ptr = &salariol;', True),
    ('salariol = 6750;', True),
    ('aux = new Comparable[a.length];', True),
    ('SELECT Fornecedor FROM TABELA1 WHERE CD1 > 100', True),
    ('if (hi == lo) return;', True),
    ('sort(a, lo, mid);', True),
    ('process(clk, reset) variable q : integer range 0 to 3;', True),
    ('mid = low + (high - low) // 2', True),
    ('if low == None : low = 0', True),
    ('count <= q;', True),
    ('mid = (high - lo)/2;', True),
    ('} else {', True),
    ('return;', True),
    ('endmodule', True),
    ('def binary_search(x, lst, low=None):', True),
    ('for i in lst:', True),
    ('for k in range(n):', True),
    ('0x007B 00 0x007B SE', False),   # tabela de memória, não código
    # ---- nunca código, mesmo com sinal forte ----
    ('SEDGEWICK, R.; WAYNE, K. Algorithms. 4. ed. Boston: Addison-Wesley, '
     '2011 (adaptado).', False),
    ('Disponível em: http://www.python-history.blogspot.com/x', False),
]


# ---- paragrafo.py: (função, entrada, saída esperada) --------------------
# Cada caso é a forma de uma questão real. A regra que todos respeitam: só
# espaço em branco muda (fora a tabela de palavras grudadas e o "•" da fonte
# Symbol) — a conferência `_visivel` roda em todos.
PARAGRAFOS = [
    # afirmações I/II: lista colada, comando e pergunta em parágrafos
    ('estrutura',
     'O OSPF usa Dijkstra. Disponível em: https://x.br/a.html. Acesso em: '
     '1 mar. 2023 (adaptado). Acerca do OSPF, avalie as afirmações a seguir. '
     'I. A rota tem menos conexões. II. Há uma base em cada roteador. '
     'É correto apenas o que se afirma em',
     'O OSPF usa Dijkstra.\n\nDisponível em: https://x.br/a.html. Acesso em: '
     '1 mar. 2023 (adaptado).\n\nAcerca do OSPF, avalie as afirmações a '
     'seguir.\n\nI. A rota tem menos conexões.\nII. Há uma base em cada '
     'roteador.\n\nÉ correto apenas o que se afirma em'),
    # asserção-razão: PORQUE sozinho
    ('estrutura',
     'Nesse contexto, avalie as asserções a seguir. I. A IoT exige '
     'consistência. PORQUE II. Há heterogeneidade. A respeito dessas '
     'asserções, assinale a opção correta.',
     'Nesse contexto, avalie as asserções a seguir.\n\nI. A IoT exige '
     'consistência.\n\nPORQUE\n\nII. Há heterogeneidade.\n\nA respeito dessas '
     'asserções, assinale a opção correta.'),
    # referência com vários autores é UM parágrafo; "b) Considerando" não
    # separa a letra do item
    ('estrutura',
     'Os homens buscam menos a saúde. GOMES, R.; NASCIMENTO, E. Por que os '
     'homens buscam menos? Cad. Saúde Pública, 2007 (adaptado). Nesse '
     'contexto, faça o que se pede nos itens a seguir. a) Cite um fator. '
     '(valor: 5,0 pontos) b) Considerando o texto, proponha uma ação. '
     '(valor: 5,0 pontos)',
     'Os homens buscam menos a saúde.\n\nGOMES, R.; NASCIMENTO, E. Por que os '
     'homens buscam menos? Cad. Saúde Pública, 2007 (adaptado).\n\nNesse '
     'contexto, faça o que se pede nos itens a seguir.\n\na) Cite um fator. '
     '(valor: 5,0 pontos)\nb) Considerando o texto, proponha uma ação. '
     '(valor: 5,0 pontos)'),
    # "Nesse caso" e "De acordo com o IBGE" são frase do texto, não comando;
    # inicial de nome ("E.") não fecha frase
    ('estrutura',
     'A best-fit deixa sobras. Nesse caso seria a 7ª partição. De acordo com '
     'o IBGE, MAGRANI, E. disse algo.',
     'A best-fit deixa sobras. Nesse caso seria a 7ª partição. De acordo com '
     'o IBGE, MAGRANI, E. disse algo.'),
    # pergunta final sem ponto vai para o próprio parágrafo
    ('estrutura',
     'Um sistema de tempo real satisfaz restrições de tempo de resposta e '
     'pode falhar caso não as cumpra. O circuito a seguir aciona um alarme e '
     'tem vários atrasos de propagação do sinal entre as portas lógicas. '
     'Cada porta AND atrasa 3 unidades de tempo, cada OR atrasa 4 e cada NOT '
     'atrasa 1, e o sistema exige resposta rápida. Após a simplificação do '
     'circuito, o menor tempo para o acionamento do alarme é de',
     'Um sistema de tempo real satisfaz restrições de tempo de resposta e '
     'pode falhar caso não as cumpra. O circuito a seguir aciona um alarme e '
     'tem vários atrasos de propagação do sinal entre as portas lógicas. '
     'Cada porta AND atrasa 3 unidades de tempo, cada OR atrasa 4 e cada NOT '
     'atrasa 1, e o sistema exige resposta rápida.\n\nApós a simplificação do '
     'circuito, o menor tempo para o acionamento do alarme é de'),
    # linhas do PDF: emenda o que quebrou no meio, fecha no ponto da linha
    # curta, mantém a tabela, junta o "•" da fonte Symbol à linha de baixo
    ('reflui',
     'O estudante deve apresentar uma tabela verdade e explicar\n'
     'o funcionamento do circuito com as entradas A, B e C,\n'
     'conforme abaixo:\n'
     'A B C Z\n'
     '1 0 0 0\n'
     '0 1 1 1\n'
     'Depois deve indicar as consequências do uso do\n'
     'transporte motorizado para a cidade, entre elas:\n'
     '\n'
     'aumento da emissão de poluentes;\n'
     '\n'
     'aumento da poluição sonora.',
     'O estudante deve apresentar uma tabela verdade e explicar o '
     'funcionamento do circuito com as entradas A, B e C, conforme abaixo:\n'
     'A B C Z\n1 0 0 0\n0 1 1 1\n'
     'Depois deve indicar as consequências do uso do transporte motorizado '
     'para a cidade, entre elas:\n\n• aumento da emissão de poluentes;\n'
     '• aumento da poluição sonora.'),
    # palavras grudadas pelo poppler e hífen de fim de linha
    ('estrutura',
     'Écomumaexpressão"servidorweb"serutilizadaparadenominar '
     'processoscujafinalidade édisponibilizar recursos. Trata- se de matéria- '
     'prima.',
     'É comum a expressão "servidor web" ser utilizada para denominar '
     'processos cuja finalidade é disponibilizar recursos. Trata-se de '
     'matéria-prima.'),
]


def testa_paragrafos():
    erros = []
    for nome, entrada, esperado in PARAGRAFOS:
        f = getattr(paragrafo, nome)
        obtido = f(entrada)
        if obtido != esperado:
            erros.append((nome, entrada, esperado, obtido))
        elif paragrafo._visivel(obtido) != paragrafo._visivel(entrada):
            erros.append((nome, entrada, 'texto visível igual à entrada', obtido))
        elif f(obtido) != obtido:
            erros.append((nome, entrada, 'segunda passada sem mudança', f(obtido)))
    print(f'paragrafo: {"OK" if not erros else "FALHOU"} '
          f'{len(PARAGRAFOS) - len(erros)}/{len(PARAGRAFOS)}')
    for nome, entrada, esperado, obtido in erros:
        print(f'   {nome}({entrada[:50]!r}…)')
        print(f'      esperava: {esperado!r}')
        print(f'      obteve:   {obtido!r}')
    return len(erros)


def testa_digitadas():
    """O texto de `digitadas.json` sobrevive à cadeia do `gerar.py`.

    `arruma`/`formato`/`qualidade` desmontam bloco de código e indentação de
    um texto já digitado; `digita.finaliza` no fim da cadeia é o que o põe de
    volta. Para cada questão do banco com enunciado ou padrão lido do PDF, a
    cadeia inteira tem de devolver exatamente o que está no banco.
    """
    import glob
    import json
    import arruma
    import qualidade

    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    banco = {q['id']: q
             for arq in glob.glob(os.path.join(raiz, 'app', 'static', 'banco', 'enade*.json'))
             for q in json.load(open(arq, encoding='utf-8'))}
    erros = []
    entradas = {qid: b for qid, b in digita.carregar().items()
                if (b.get('_enunciado') or b.get('_padrao')) and qid in banco}
    for qid, bloco in sorted(entradas.items()):
        q = banco[qid]
        r = digita.finaliza(
            qualidade.limpa(formato.formata(arruma.limpa(digita.aplica(q)))))
        for campo, chave in (('enunciado', '_enunciado'), ('padrao', '_padrao')):
            if bloco.get(chave) and r.get(campo) != q.get(campo):
                erros.append(f'{qid} {campo}')
        if r.get('alternativas') != q.get('alternativas'):
            erros.append(f'{qid} alternativas')
    print(f'digitadas: {"OK" if not erros else "FALHOU"} '
          f'{len(entradas) - len(erros)}/{len(entradas)}')
    for e in erros:
        print(f'   a cadeia do gerar.py muda {e}')
    return len(erros)


def main():
    erros = [(t, formato._codigo_da_linha(t)) for t, esp in CASOS
             if formato._codigo_da_linha(t) != esp]
    print(f'formato: {"OK" if not erros else "FALHOU"} '
          f'{len(CASOS) - len(erros)}/{len(CASOS)}')
    for t, obtido in erros:
        print(f'   esperava {"codigo" if not obtido else "texto"}: {t[:70]!r}')
    falhas = testa_paragrafos() + testa_digitadas()
    return 1 if erros or falhas else 0


if __name__ == '__main__':
    sys.exit(main())
