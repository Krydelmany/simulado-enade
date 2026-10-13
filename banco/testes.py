"""Testes do `formato.py`.

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


def main():
    erros = [(t, formato._codigo_da_linha(t)) for t, esp in CASOS
             if formato._codigo_da_linha(t) != esp]
    print(f'{"OK" if not erros else "FALHOU"} '
          f'{len(CASOS) - len(erros)}/{len(CASOS)}')
    for t, obtido in erros:
        print(f'   esperava {"codigo" if not obtido else "texto"}: {t[:70]!r}')
    return 1 if erros else 0


if __name__ == '__main__':
    sys.exit(main())
