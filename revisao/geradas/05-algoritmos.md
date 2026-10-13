# Geradas — V. Algoritmos e Estruturas de Dados — PARA REVISÃO

Área da Portaria INEP nº 161/2026: *algoritmos, fundamentos de programação e estruturas de dados*. 9 questões escritas para revisão (não são do INEP). Confira o gabarito de cada uma; para corrigir, edite `banco/geradas/` e rode `python3 banco/geradas.py`.

---

## GER-V-F1 — Pilha (LIFO)
- **Gabarito:** B
- Nível: **Fácil**

````text
O recurso “desfazer” de um editor de texto recupera sempre a última alteração feita, depois a penúltima, e assim por diante.

A estrutura de dados que segue essa política, em que o último elemento inserido é o primeiro a ser removido, é a
````

A) fila.
B) pilha. ✔
C) lista circular.
D) árvore binária de busca.
E) tabela hash.

---

## GER-V-F2 — Complexidade da busca binária
- **Gabarito:** C
- Nível: **Fácil**

````text
Um vetor com n elementos ordenados é consultado por busca binária.

No pior caso, a complexidade de tempo dessa busca é
````

A) O(1).
B) O(n).
C) O(log n). ✔
D) O(n log n).
E) O(n²).

---

## GER-V-F3 — Rastreamento de laço
- **Gabarito:** D
- Nível: **Fácil**

````text
Considere o trecho de código em Python a seguir.

```python
soma = 0
for i in range(1, 5):
    if i % 2 == 0:
        soma += i
print(soma)
```

O valor impresso é
````

A) 4.
B) 10.
C) 2.
D) 6. ✔
E) 0.

---

## GER-V-M1 — Operações em fila (FIFO)
- **Gabarito:** E
- Nível: **Média**

````text
Uma fila, inicialmente vazia, recebe a seguinte sequência de operações:

enfileira(3), enfileira(7), desenfileira(), enfileira(5), enfileira(1), desenfileira()

Ao final, o elemento que está na frente da fila é
````

A) 3.
B) 7.
C) 1.
D) nenhum, pois a fila está vazia.
E) 5. ✔

---

## GER-V-M2 — Árvore binária de busca e percurso em pré-ordem
- **Gabarito:** A
- Nível: **Média**

````text
Os valores 50, 30, 70, 20, 40, 60 e 80 são inseridos, nessa ordem, em uma árvore binária de busca inicialmente vazia, sem balanceamento.

O percurso em pré-ordem (raiz, subárvore esquerda, subárvore direita) dessa árvore é
````

A) 50, 30, 20, 40, 70, 60, 80. ✔
B) 20, 30, 40, 50, 60, 70, 80.
C) 20, 40, 30, 60, 80, 70, 50.
D) 50, 30, 70, 20, 40, 60, 80.
E) 50, 70, 80, 60, 30, 40, 20.

---

## GER-V-M3 — Recursão
- **Gabarito:** B
- Nível: **Média**

````text
Considere a função recursiva em C a seguir.

```c
int f(int n) {
    if (n <= 1) return 1;
    return n * f(n - 2);
}
```

O valor retornado pela chamada f(7) é
````

A) 5040.
B) 105. ✔
C) 48.
D) 15.
E) 35.

---

## GER-V-D1 — Tabela hash com encadeamento
- **Gabarito:** C
- Nível: **Difícil**

````text
Um serviço de cache armazena 3 000 chaves em uma tabela hash com encadeamento separado: cada uma das 1 000 posições da tabela aponta para uma lista com as chaves que caíram naquela posição. A função de dispersão distribui as chaves de forma aproximadamente uniforme.

Considerando essa situação, avalie as afirmações a seguir.

I. O fator de carga da tabela é 3, de modo que cada lista tem, em média, 3 chaves.
II. No pior caso, se todas as chaves colidirem na mesma posição, uma busca custa O(n), em que n é o número de chaves.
III. No encadeamento separado, o fator de carga não pode ultrapassar 1.

É correto o que se afirma em
````

A) I, apenas.
B) III, apenas.
C) I e II, apenas. ✔
D) II e III, apenas.
E) I, II e III.

---

## GER-V-D2 — Merge sort: tempo e memória
- **Gabarito:** D
- Nível: **Difícil**

````text
Uma equipe precisa ordenar registros de log em um dispositivo com pouca memória RAM e avalia o uso do Merge Sort, que divide o vetor ao meio, ordena recursivamente cada metade e intercala as metades ordenadas.

Nesse contexto, avalie as asserções a seguir e a relação proposta entre elas.

I. O Merge Sort ordena um vetor de n elementos em tempo O(n log n) no pior caso, usando apenas memória auxiliar constante, O(1).

PORQUE

II. A etapa de intercalação percorre as duas metades ordenadas e as combina em tempo linear no tamanho delas.

A respeito dessas asserções, assinale a opção correta.
````

A) As asserções I e II são proposições verdadeiras, e a II é uma justificativa correta da I.
B) As asserções I e II são proposições verdadeiras, mas a II não é uma justificativa correta da I.
C) A asserção I é uma proposição verdadeira, e a II é uma proposição falsa.
D) A asserção I é uma proposição falsa, e a II é uma proposição verdadeira. ✔
E) As asserções I e II são proposições falsas.

---

## GER-V-D3 — Programação dinâmica e memoização
- **Gabarito:** E
- Nível: **Difícil**

````text
Para acelerar o cálculo da sequência de Fibonacci, em que fib(0) = 0 e fib(1) = 1, um desenvolvedor escreveu a função a seguir, que guarda resultados já calculados em um dicionário.

```python
memo = {}

def fib(n):
    if n <= 1:
        return n
    if n in memo:
        return memo[n]
    memo[n] = fib(n - 1) + fib(n - 2)
    return memo[n]
```

Com base nesse código, avalie as afirmações a seguir.

I. Sem o dicionário memo, a mesma função recursiva teria complexidade de tempo exponencial em n.
II. Com o dicionário memo, cada valor fib(k), para k ≤ n, é calculado uma única vez, e a complexidade de tempo passa a ser O(n).
III. A chamada fib(10) retorna 55.

É correto o que se afirma em
````

A) I, apenas.
B) II, apenas.
C) I e III, apenas.
D) II e III, apenas.
E) I, II e III. ✔

---
