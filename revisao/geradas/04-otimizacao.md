# Geradas — IV. Pesquisa Operacional e Otimização — PARA REVISÃO

Área da Portaria INEP nº 161/2026: *pesquisa operacional e otimização*. 9 questões escritas para revisão (não são do INEP). Confira o gabarito de cada uma; para corrigir, edite `banco/geradas/` e rode `python3 banco/geradas.py`.

---

## GER-IV-F1 — Região viável em programação linear
- **Gabarito:** C
- Nível: **Fácil**

````text
Em um problema de programação linear, a região viável é
````

A) o único ponto que maximiza ou minimiza a função objetivo.
B) o conjunto dos valores que a função objetivo pode assumir.
C) o conjunto dos pontos que satisfazem simultaneamente todas as restrições do problema. ✔
D) a reta que representa a função objetivo no plano.
E) o conjunto das restrições que podem ser removidas sem alterar a solução.

---

## GER-IV-F2 — Solução ótima nos vértices
- **Gabarito:** D
- Nível: **Fácil**

````text
A região viável de um problema de maximização de Z = 3x + 2y é um polígono convexo cujos vértices são (0, 0), (4, 0), (3, 3) e (0, 5).

O valor máximo de Z e o ponto em que ele ocorre são
````

A) 12, em (4, 0).
B) 10, em (0, 5).
C) 0, em (0, 0).
D) 15, em (3, 3). ✔
E) 18, em (6, 0).

---

## GER-IV-F3 — Caminho mínimo em grafos ponderados
- **Gabarito:** E
- Nível: **Fácil**

````text
Uma transportadora precisa calcular a rota de menor distância entre o depósito e cada cliente em uma malha viária modelada como grafo, em que todas as distâncias (pesos das arestas) são não negativas.

Um algoritmo clássico adequado para esse cálculo é o de
````

A) Kruskal.
B) Prim.
C) Ford-Fulkerson.
D) busca em profundidade.
E) Dijkstra. ✔

---

## GER-IV-M1 — Modelagem de problema de programação linear
- **Gabarito:** A
- Nível: **Média**

````text
Uma fábrica produz dois tipos de placa eletrônica, X e Y, com lucro unitário de R$ 40 e R$ 30, respectivamente. Cada placa X consome 2 horas de montagem e 1 hora de teste; cada placa Y consome 1 hora de montagem e 1 hora de teste. Por semana, há 100 horas de montagem e 80 horas de teste disponíveis. Sejam x e y as quantidades semanais produzidas de X e Y.

O modelo de programação linear que maximiza o lucro semanal é
````

A) maximizar 40x + 30y, sujeito a 2x + y ≤ 100, x + y ≤ 80, x ≥ 0 e y ≥ 0. ✔
B) minimizar 40x + 30y, sujeito a 2x + y ≤ 100, x + y ≤ 80, x ≥ 0 e y ≥ 0.
C) maximizar 40x + 30y, sujeito a 2x + y ≥ 100, x + y ≥ 80, x ≥ 0 e y ≥ 0.
D) maximizar 40x + 30y, sujeito a x + 2y ≤ 100, x + y ≤ 80, x ≥ 0 e y ≥ 0.
E) maximizar 2x + y, sujeito a 40x + 30y ≤ 100, x + y ≤ 80, x ≥ 0 e y ≥ 0.

---

## GER-IV-M2 — Solução gráfica de programação linear
- **Gabarito:** B
- Nível: **Média**

````text
Considere o problema: maximizar Z = 40x + 30y, sujeito a 2x + y ≤ 100, x + y ≤ 80, x ≥ 0 e y ≥ 0.

O valor ótimo de Z é
````

A) 2 000.
B) 2 600. ✔
C) 2 400.
D) 3 000.
E) 2 800.

---

## GER-IV-M3 — Variáveis de folga no simplex
- **Gabarito:** C
- Nível: **Média**

````text
Para aplicar o método simplex, as restrições de desigualdade são convertidas em igualdades por meio de variáveis auxiliares.

Ao introduzir a variável de folga s na restrição 2x + y ≤ 100, a restrição passa a ser escrita como
````

A) 2x + y − s = 100, com s ≥ 0.
B) 2x + y + s ≤ 100, com s livre.
C) 2x + y + s = 100, com s ≥ 0. ✔
D) 2x + y + s = 0, com s ≥ 0.
E) 2x + y = 100, com s = 0.

---

## GER-IV-D1 — Problema de designação
- **Gabarito:** D
- Nível: **Difícil**

````text
Uma empresa de suporte técnico precisa designar 4 técnicos a 4 chamados abertos. Cada técnico atende exatamente um chamado, e cada chamado é atendido por exatamente um técnico. O tempo estimado de cada técnico em cada chamado é conhecido, e o objetivo é minimizar o tempo total de atendimento.

Considerando essa situação, avalie as afirmações a seguir.

I. O problema pode ser modelado como programação linear inteira com variáveis binárias xᵢⱼ, com restrições que impõem um chamado por técnico e um técnico por chamado.
II. Uma estratégia gulosa que, a cada passo, escolhe o par técnico-chamado de menor tempo ainda disponível garante a solução ótima.
III. O método húngaro resolve esse problema de designação em tempo polinomial.
IV. Por haver 4 técnicos e 4 chamados, existem 16 designações possíveis a avaliar por enumeração completa.

É correto apenas o que se afirma em
````

A) I e II.
B) II e IV.
C) I, II e III.
D) I e III. ✔
E) III e IV.

---

## GER-IV-D2 — Existência de solução ótima em programação linear
- **Gabarito:** E
- Nível: **Difícil**

````text
Ao modelar problemas de alocação de recursos como programação linear, o engenheiro precisa saber em que condições o solver devolverá uma solução ótima e onde ela se encontra.

Nesse contexto, avalie as asserções a seguir e a relação proposta entre elas.

I. Todo problema de programação linear com região viável não vazia possui solução ótima finita.

PORQUE

II. Uma função objetivo linear atinge seu valor ótimo em um ponto interior da região viável.

A respeito dessas asserções, assinale a opção correta.
````

A) As asserções I e II são proposições verdadeiras, e a II é uma justificativa correta da I.
B) As asserções I e II são proposições verdadeiras, mas a II não é uma justificativa correta da I.
C) A asserção I é uma proposição verdadeira, e a II é uma proposição falsa.
D) A asserção I é uma proposição falsa, e a II é uma proposição verdadeira.
E) As asserções I e II são proposições falsas. ✔

---

## GER-IV-D3 — Caminho crítico (CPM)
- **Gabarito:** A
- Nível: **Difícil**

````text
O cronograma de um projeto de software tem as atividades a seguir, com durações em dias e suas predecessoras.

A: 3 dias, sem predecessora
B: 2 dias, após A
C: 4 dias, após A
D: 3 dias, após B e C
E: 2 dias, após B

O projeto termina quando todas as atividades terminam. Com base nessas informações, avalie as afirmações a seguir.

I. A duração mínima do projeto é de 10 dias.
II. O caminho crítico é A–C–D.
III. A atividade B pode atrasar até 2 dias sem atrasar o término do projeto.
IV. A atividade E é uma atividade crítica.

É correto apenas o que se afirma em
````

A) I, II e III. ✔
B) I e IV.
C) II e III.
D) I, III e IV.
E) II, III e IV.

---
