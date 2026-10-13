# Geradas — XII. Arquitetura de Computadores — PARA REVISÃO

Área da Portaria INEP nº 161/2026: *organização e arquitetura de computadores*. 9 questões escritas para revisão (não são do INEP). Confira o gabarito de cada uma; para corrigir, edite `banco/geradas/` e rode `python3 banco/geradas.py`.

---

## GER-XII-F1 — Hierarquia de memória: cache
- **Gabarito:** E
- Nível: **Fácil**

````text
Em um computador, uma memória pequena e muito rápida, situada entre o processador e a memória principal, guarda cópias dos dados e das instruções usados com mais frequência, para reduzir o tempo médio de acesso.

Essa memória é a
````

A) memória secundária.
B) memória ROM.
C) memória virtual.
D) unidade lógica e aritmética.
E) memória cache. ✔

---

## GER-XII-F2 — Espaço de endereçamento
- **Gabarito:** A
- Nível: **Fácil**

````text
Um microprocessador simples tem barramento de endereços de 16 bits, e cada endereço corresponde a um byte.

O número máximo de posições de memória endereçáveis é
````

A) 65 536. ✔
B) 16.
C) 32 768.
D) 1 024.
E) 256.

---

## GER-XII-F3 — Arquitetura de von Neumann
- **Gabarito:** B
- Nível: **Fácil**

````text
Na arquitetura de von Neumann, adotada pela maioria dos computadores de uso geral,
````

A) dados e instruções ficam em memórias fisicamente separadas, com barramentos independentes.
B) dados e instruções compartilham a mesma memória e o mesmo caminho de acesso. ✔
C) não existe unidade de controle, apenas unidade lógica e aritmética.
D) as instruções são executadas sempre em paralelo, sem ordem definida.
E) o processador não utiliza registradores.

---

## GER-XII-M1 — Desempenho: CPI e frequência de clock
- **Gabarito:** C
- Nível: **Média**

````text
Um programa executa 2 × 10⁹ instruções em um processador de 3 GHz, com CPI (ciclos por instrução) médio de 1,5.

O tempo de execução do programa é de
````

A) 0,5 s.
B) 2 s.
C) 1 s. ✔
D) 4,5 s.
E) 9 s.

---

## GER-XII-M2 — Pipeline de instruções
- **Gabarito:** D
- Nível: **Média**

````text
Um processador tem pipeline de 5 estágios, cada um com duração de 1 ciclo de clock. Uma sequência de 100 instruções independentes, sem conflitos nem desvios, é executada a partir do pipeline vazio.

O número total de ciclos necessários para concluir as 100 instruções é
````

A) 500.
B) 100.
C) 99.
D) 104. ✔
E) 105.

---

## GER-XII-M3 — Tempo médio de acesso à memória
- **Gabarito:** E
- Nível: **Média**

````text
Em um sistema com uma memória cache, o tempo de acerto é de 1 ns, a taxa de falha é de 5% e a penalidade por falha é de 100 ns.

O tempo médio de acesso à memória é de
````

A) 5 ns.
B) 101 ns.
C) 1,05 ns.
D) 100 ns.
E) 6 ns. ✔

---

## GER-XII-D1 — Lei de Amdahl
- **Gabarito:** A
- Nível: **Difícil**

````text
Uma aplicação de processamento de imagens gasta 80% do seu tempo de execução em um trecho que pode ser perfeitamente paralelizado; os 20% restantes são estritamente sequenciais. A equipe pretende executá-la em um processador de 4 núcleos e cogita, no futuro, migrar para máquinas com muito mais núcleos.

Com base na lei de Amdahl, avalie as afirmações a seguir.

I. O ganho de desempenho (speedup) com 4 núcleos é de 2,5.
II. Por mais núcleos que se usem, o speedup fica limitado a 5.
III. Com 4 núcleos, o speedup é de 4, pois o trabalho é dividido igualmente entre eles.

É correto o que se afirma em
````

A) I e II, apenas. ✔
B) I, apenas.
C) III, apenas.
D) II e III, apenas.
E) I, II e III.

---

## GER-XII-D2 — RISC e localidade de referência
- **Gabarito:** B
- Nível: **Difícil**

````text
Processadores de dispositivos móveis costumam seguir a filosofia RISC e dependem de uma hierarquia de memória eficiente para alcançar bom desempenho com baixo consumo de energia.

Nesse contexto, avalie as asserções a seguir e a relação proposta entre elas.

I. Processadores RISC tendem a usar instruções de tamanho fixo e de formato simples, o que facilita a decodificação e o uso de pipeline.

PORQUE

II. A hierarquia de memória explora os princípios de localidade temporal e espacial dos programas.

A respeito dessas asserções, assinale a opção correta.
````

A) As asserções I e II são proposições verdadeiras, e a II é uma justificativa correta da I.
B) As asserções I e II são proposições verdadeiras, mas a II não é uma justificativa correta da I. ✔
C) A asserção I é uma proposição verdadeira, e a II é uma proposição falsa.
D) A asserção I é uma proposição falsa, e a II é uma proposição verdadeira.
E) As asserções I e II são proposições falsas.

---

## GER-XII-D3 — Conflitos de dados no pipeline
- **Gabarito:** C
- Nível: **Difícil**

````text
Considere o trecho a seguir, executado em um processador com o pipeline clássico de 5 estágios (busca, decodificação, execução, acesso à memória e escrita no registrador), com adiantamento de dados (forwarding).

```text
I1: LW  R1, 0(R2)
I2: ADD R3, R1, R4
I3: SUB R5, R6, R7
```

Com base nesse trecho, avalie as afirmações a seguir.

I. Há dependência de dados verdadeira (RAW) entre I1 e I2, envolvendo o registrador R1.
II. Mesmo com adiantamento, I2 precisa esperar uma bolha (stall) de um ciclo após o load.
III. Colocar I3 entre I1 e I2 pode eliminar a bolha sem alterar o resultado do programa.
IV. I3 depende de I2, pois usa o registrador R3.

É correto apenas o que se afirma em
````

A) I e IV.
B) II e IV.
C) I, II e III. ✔
D) I, III e IV.
E) II, III e IV.

---
