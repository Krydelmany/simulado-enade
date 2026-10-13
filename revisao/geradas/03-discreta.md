# Geradas — III. Matemática Discreta e Grafos — PARA REVISÃO

Área da Portaria INEP nº 161/2026: *matemática discreta e teoria dos grafos*. 9 questões escritas para revisão (não são do INEP). Confira o gabarito de cada uma; para corrigir, edite `banco/geradas/` e rode `python3 banco/geradas.py`.

---

## GER-III-F1 — Número máximo de arestas de um grafo simples
- **Gabarito:** D
- Nível: **Fácil**

````text
Um grafo simples (sem laços e sem arestas múltiplas) e não orientado tem 5 vértices.

O número máximo de arestas que esse grafo pode ter é
````

A) 5.
B) 20.
C) 25.
D) 10. ✔
E) 15.

---

## GER-III-F2 — Negação de proposição quantificada
- **Gabarito:** E
- Nível: **Fácil**

````text
Considere a proposição: “Todo servidor do cluster está ativo”.

A negação lógica dessa proposição é
````

A) Nenhum servidor do cluster está ativo.
B) Todo servidor do cluster está inativo.
C) Algum servidor do cluster está ativo.
D) Se um servidor do cluster está ativo, todos estão.
E) Existe pelo menos um servidor do cluster que não está ativo. ✔

---

## GER-III-F3 — Diferença de conjuntos
- **Gabarito:** A
- Nível: **Fácil**

````text
Sejam os conjuntos A = {1, 2, 3, 4} e B = {3, 4, 5}.

O conjunto A − B (elementos de A que não estão em B) é
````

A) {1, 2}. ✔
B) {3, 4}.
C) {5}.
D) {1, 2, 5}.
E) {1, 2, 3, 4, 5}.

---

## GER-III-M1 — Arranjos sem repetição
- **Gabarito:** B
- Nível: **Média**

````text
Um sistema de acesso usa códigos de 4 dígitos, formados com os algarismos de 0 a 9, sem repetir algarismo no mesmo código. A ordem dos algarismos importa.

O número de códigos distintos possíveis é
````

A) 10 000.
B) 5 040. ✔
C) 210.
D) 40.
E) 6 561.

---

## GER-III-M2 — Soma dos graus e número de arestas
- **Gabarito:** C
- Nível: **Média**

````text
Em uma rede modelada como grafo não orientado, os 6 vértices têm graus 3, 3, 2, 2, 1 e 1.

O número de arestas desse grafo é
````

A) 12.
B) 3.
C) 6. ✔
D) 7.
E) 24.

---

## GER-III-M3 — Trilhas e circuitos eulerianos
- **Gabarito:** D
- Nível: **Média**

````text
Um robô de inspeção deve percorrer todos os corredores de um galpão, passando por cada corredor exatamente uma vez. O galpão é modelado como um grafo conexo, em que os corredores são arestas e os cruzamentos são vértices. Exatamente dois vértices desse grafo têm grau ímpar.

Nessa situação, o grafo
````

A) possui um circuito euleriano, que começa e termina no mesmo vértice.
B) não possui nenhuma trilha que passe por todas as arestas uma única vez.
C) é necessariamente uma árvore.
D) possui uma trilha euleriana que começa em um dos vértices de grau ímpar e termina no outro. ✔
E) possui necessariamente um ciclo hamiltoniano.

---

## GER-III-D1 — Coloração de grafos e agendamento
- **Gabarito:** E
- Nível: **Difícil**

````text
Uma coordenação de curso quer agendar as provas finais usando o menor número possível de horários. Para isso, modelou o problema como um grafo: cada disciplina é um vértice, e há aresta entre duas disciplinas quando algum aluno está matriculado em ambas, pois essas provas não podem ocorrer no mesmo horário. O grafo obtido é planar e contém um subgrafo completo com 4 vértices (K₄).

Considerando essa modelagem, avalie as afirmações a seguir.

I. São necessários pelo menos 4 horários distintos.
II. Como o grafo é planar, 4 horários são suficientes.
III. Em qualquer grafo, o número cromático é igual ao grau máximo do grafo mais um.

É correto o que se afirma em
````

A) I, apenas.
B) III, apenas.
C) I e III, apenas.
D) II e III, apenas.
E) I e II, apenas. ✔

---

## GER-III-D2 — Propriedades das árvores
- **Gabarito:** A
- Nível: **Difícil**

````text
Árvores são usadas para representar hierarquias de diretórios, árvores geradoras de redes e estruturas de busca. Um resultado básico sobre elas relaciona o número de vértices com o número de arestas.

Nesse contexto, avalie as asserções a seguir e a relação proposta entre elas.

I. Toda árvore com n vértices possui exatamente n − 1 arestas.

PORQUE

II. Uma árvore é um grafo conexo e acíclico, e toda árvore com pelo menos dois vértices possui uma folha, cuja remoção gera uma árvore com um vértice e uma aresta a menos.

A respeito dessas asserções, assinale a opção correta.
````

A) As asserções I e II são proposições verdadeiras, e a II é uma justificativa correta da I. ✔
B) As asserções I e II são proposições verdadeiras, mas a II não é uma justificativa correta da I.
C) A asserção I é uma proposição verdadeira, e a II é uma proposição falsa.
D) A asserção I é uma proposição falsa, e a II é uma proposição verdadeira.
E) As asserções I e II são proposições falsas.

---

## GER-III-D3 — Relações e ordem parcial
- **Gabarito:** B
- Nível: **Difícil**

````text
Em um sistema de controle de versões, o histórico de commits forma um grafo orientado acíclico: cada commit aponta para o(s) commit(s) de que deriva. Sobre o conjunto C de commits de um repositório, define-se a relação R tal que a R b se, e somente se, a = b ou a é ancestral de b.

Com base nessa definição, avalie as afirmações a seguir.

I. R é reflexiva.
II. R é simétrica.
III. R é transitiva.
IV. R é uma relação de ordem parcial sobre C.

É correto apenas o que se afirma em
````

A) I e II.
B) I, III e IV. ✔
C) II e IV.
D) I, II e III.
E) III e IV.

---
