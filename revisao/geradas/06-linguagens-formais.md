# Geradas — VI. Linguagens Formais e Autômatos — PARA REVISÃO

Área da Portaria INEP nº 161/2026: *linguagens formais e autômatos*. 9 questões escritas para revisão (não são do INEP). Confira o gabarito de cada uma; para corrigir, edite `banco/geradas/` e rode `python3 banco/geradas.py`.

---

## GER-VI-F1 — Expressões regulares
- **Gabarito:** A
- Nível: **Fácil**

````text
Considere a expressão regular a(b|c)*, sobre o alfabeto {a, b, c}, que descreve cadeias formadas por um a seguido de zero ou mais símbolos b ou c.

A cadeia que pertence à linguagem descrita por essa expressão é
````

A) acbb. ✔
B) ba.
C) aab.
D) abca.
E) cab.

---

## GER-VI-F2 — Hierarquia de Chomsky
- **Gabarito:** B
- Nível: **Fácil**

````text
Na hierarquia de Chomsky, cada classe de linguagens está associada a um tipo de máquina reconhecedora.

A classe de linguagens reconhecida pelos autômatos de pilha é a das linguagens
````

A) regulares.
B) livres de contexto. ✔
C) sensíveis ao contexto.
D) recursivamente enumeráveis.
E) finitas.

---

## GER-VI-F3 — Autômato finito determinístico
- **Gabarito:** C
- Nível: **Fácil**

````text
Em um autômato finito determinístico (AFD), para cada estado e para cada símbolo do alfabeto,
````

A) podem existir várias transições possíveis.
B) podem existir transições vazias (ε), sem consumir símbolo.
C) existe exatamente uma transição definida. ✔
D) só existe transição a partir do estado inicial.
E) a transição depende do símbolo que está no topo de uma pilha.

---

## GER-VI-M1 — Linguagem aceita por AFD
- **Gabarito:** D
- Nível: **Média**

````text
Um AFD sobre o alfabeto {0, 1} tem dois estados, P (inicial e de aceitação) e Q (não de aceitação). Ao ler 0, o autômato permanece no estado em que está; ao ler 1, alterna entre P e Q.

A cadeia aceita por esse autômato é
````

A) 1.
B) 0111.
C) 10.
D) 1001. ✔
E) 111.

---

## GER-VI-M2 — Linguagens não regulares
- **Gabarito:** E
- Nível: **Média**

````text
O lema do bombeamento permite provar que certas linguagens não podem ser reconhecidas por nenhum autômato finito.

Entre as linguagens a seguir, sobre o alfabeto {a, b}, a que NÃO é regular é
````

A) {aⁿ | n ≥ 0}.
B) o conjunto das cadeias que terminam em ab.
C) {aᵐbⁿ | m ≥ 0 e n ≥ 0}.
D) o conjunto das cadeias com número par de símbolos a.
E) {aⁿbⁿ | n ≥ 0}. ✔

---

## GER-VI-M3 — Derivação em gramática livre de contexto
- **Gabarito:** A
- Nível: **Média**

````text
Considere a gramática livre de contexto com símbolo inicial S e as produções S → aSb | ε, em que ε é a cadeia vazia.

A cadeia gerada por essa gramática é
````

A) aabb. ✔
B) abab.
C) aab.
D) ba.
E) abb.

---

## GER-VI-D1 — Análise léxica e autômatos finitos
- **Gabarito:** B
- Nível: **Difícil**

````text
Ao implementar o analisador léxico de uma linguagem de configuração, uma equipe definiu que identificadores são formados por uma letra seguida de letras ou dígitos, que números são sequências de um ou mais dígitos e que algumas palavras são reservadas. A equipe também cogitou validar, já no analisador léxico, o balanceamento de parênteses aninhados nas expressões.

Considerando essa situação, avalie as afirmações a seguir.

I. Os padrões de identificadores e de números podem ser especificados por expressões regulares e reconhecidos por autômatos finitos.
II. O balanceamento de parênteses aninhados, com profundidade arbitrária, pode ser verificado por um autômato finito determinístico.
III. Todo autômato finito não determinístico pode ser convertido em um determinístico equivalente, possivelmente com um número exponencialmente maior de estados.

É correto o que se afirma em
````

A) I, apenas.
B) I e III, apenas. ✔
C) II, apenas.
D) II e III, apenas.
E) I, II e III.

---

## GER-VI-D2 — Palíndromos e autômatos de pilha
- **Gabarito:** C
- Nível: **Difícil**

````text
Ferramentas de verificação de sequências de DNA e de validação de textos simétricos frequentemente lidam com palíndromos, cadeias que são lidas da mesma forma da esquerda para a direita e da direita para a esquerda.

Nesse contexto, avalie as asserções a seguir e a relação proposta entre elas.

I. A linguagem L = {w ∈ {a, b}* | w é palíndromo} é livre de contexto.

PORQUE

II. Toda linguagem livre de contexto é reconhecida por algum autômato de pilha determinístico.

A respeito dessas asserções, assinale a opção correta.
````

A) As asserções I e II são proposições verdadeiras, e a II é uma justificativa correta da I.
B) As asserções I e II são proposições verdadeiras, mas a II não é uma justificativa correta da I.
C) A asserção I é uma proposição verdadeira, e a II é uma proposição falsa. ✔
D) A asserção I é uma proposição falsa, e a II é uma proposição verdadeira.
E) As asserções I e II são proposições falsas.

---

## GER-VI-D3 — Decidibilidade e problema da parada
- **Gabarito:** D
- Nível: **Difícil**

````text
Uma empresa de ferramentas de desenvolvimento pretende lançar um analisador que, dado o código-fonte de qualquer programa e uma entrada qualquer, informe com certeza se o programa termina ou se entra em execução infinita.

Considerando essa proposta, avalie as afirmações a seguir.

I. O problema corresponde ao problema da parada, que é indecidível para máquinas de Turing.
II. Seria possível construir esse analisador para qualquer programa, desde que houvesse memória suficiente disponível.
III. Ferramentas de análise estática podem detectar laços infinitos em casos particulares, embora não em todos.
IV. A tese de Church-Turing afirma que as máquinas de Turing são mais poderosas que qualquer computador real.

É correto apenas o que se afirma em
````

A) I e II.
B) II e IV.
C) III e IV.
D) I e III. ✔
E) I, II e III.

---
