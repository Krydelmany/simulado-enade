# Geradas — X. Circuitos Elétricos e Eletrônicos — PARA REVISÃO

Área da Portaria INEP nº 161/2026: *circuitos elétricos e eletrônicos*. 9 questões escritas para revisão (não são do INEP). Confira o gabarito de cada uma; para corrigir, edite `banco/geradas/` e rode `python3 banco/geradas.py`.

---

## GER-X-F1 — Lei de Ohm
- **Gabarito:** B
- Nível: **Fácil**

````text
Um resistor de 220 Ω é ligado diretamente aos terminais de uma fonte de 5 V.

A corrente no resistor é de, aproximadamente,
````

A) 1,1 A.
B) 22,7 mA. ✔
C) 44 mA.
D) 2,27 mA.
E) 227 mA.

---

## GER-X-F2 — Associação de resistores em série
- **Gabarito:** C
- Nível: **Fácil**

````text
Três resistores, de 100 Ω, 220 Ω e 330 Ω, são ligados em série.

A resistência equivalente da associação é de
````

A) 57 Ω.
B) 330 Ω.
C) 650 Ω. ✔
D) 220 Ω.
E) 1 000 Ω.

---

## GER-X-F3 — Potência elétrica
- **Gabarito:** D
- Nível: **Fácil**

````text
Um módulo de comunicação alimentado por 12 V consome corrente de 0,5 A.

A potência consumida pelo módulo é de
````

A) 24 W.
B) 0,04 W.
C) 12,5 W.
D) 6 W. ✔
E) 2,4 W.

---

## GER-X-M1 — Divisor de tensão
- **Gabarito:** E
- Nível: **Média**

````text
Para ler um sinal de 12 V com a entrada analógica de um microcontrolador, usa-se um divisor resistivo: R1 = 10 kΩ ligado entre o sinal e o ponto de leitura, e R2 = 2 kΩ ligado entre o ponto de leitura e o terra. Despreze a corrente drenada pela entrada do microcontrolador.

A tensão no ponto de leitura é de
````

A) 10 V.
B) 6 V.
C) 1 V.
D) 2,4 V.
E) 2 V. ✔

---

## GER-X-M2 — Constante de tempo de circuito RC
- **Gabarito:** A
- Nível: **Média**

````text
Um circuito de reset de um microcontrolador usa um resistor de 10 kΩ em série com um capacitor de 100 µF.

A constante de tempo desse circuito RC é de
````

A) 1 s. ✔
B) 0,1 s.
C) 10 s.
D) 1 ms.
E) 100 s.

---

## GER-X-M3 — Resistor limitador de LED
- **Gabarito:** B
- Nível: **Média**

````text
Um LED com queda de tensão direta de 2 V deve operar com corrente de 15 mA, alimentado por uma fonte de 5 V, por meio de um resistor em série.

O valor do resistor limitador deve ser de
````

A) 333 Ω.
B) 200 Ω. ✔
C) 133 Ω.
D) 150 Ω.
E) 75 Ω.

---

## GER-X-D1 — Amplificador operacional inversor e saturação
- **Gabarito:** C
- Nível: **Difícil**

````text
O sinal de um sensor é condicionado por um amplificador operacional na configuração inversora, com resistor de entrada de 4,7 kΩ e resistor de realimentação de 47 kΩ. O amplificador é alimentado com ±12 V, e a tensão de entrada é de 0,2 V. Considere o amplificador ideal dentro dos limites de alimentação.

Com base nessas informações, avalie as afirmações a seguir.

I. O ganho de tensão do circuito é −10.
II. A tensão de saída é de −2 V.
III. Se a tensão de entrada passar a 1,5 V, a saída será de −15 V.

É correto o que se afirma em
````

A) I, apenas.
B) III, apenas.
C) I e II, apenas. ✔
D) II e III, apenas.
E) I, II e III.

---

## GER-X-D2 — Indutores em corrente alternada
- **Gabarito:** D
- Nível: **Difícil**

````text
Indutores são usados em fontes chaveadas e em filtros de linha. Para dimensioná-los, o projetista precisa conhecer o comportamento de tensão e corrente no indutor em regime senoidal.

Nesse contexto, avalie as asserções a seguir e a relação proposta entre elas.

I. Em um circuito de corrente alternada puramente indutivo, a corrente está adiantada 90° em relação à tensão.

PORQUE

II. A reatância indutiva cresce proporcionalmente à frequência do sinal, conforme X_L = 2πfL.

A respeito dessas asserções, assinale a opção correta.
````

A) As asserções I e II são proposições verdadeiras, e a II é uma justificativa correta da I.
B) As asserções I e II são proposições verdadeiras, mas a II não é uma justificativa correta da I.
C) A asserção I é uma proposição verdadeira, e a II é uma proposição falsa.
D) A asserção I é uma proposição falsa, e a II é uma proposição verdadeira. ✔
E) As asserções I e II são proposições falsas.

---

## GER-X-D3 — Análise de circuito série-paralelo
- **Gabarito:** E
- Nível: **Difícil**

````text
Uma fonte de 9 V alimenta um resistor R1 = 1 kΩ, ligado em série com a associação em paralelo de R2 = 2 kΩ e R3 = 2 kΩ.

Com base nessas informações, avalie as afirmações a seguir.

I. A corrente fornecida pela fonte é de 4,5 mA.
II. A tensão sobre R2 é de 4,5 V.
III. A corrente em R3 é de 2,25 mA.
IV. A potência total dissipada pelos resistores é de 40,5 mW.

É correto o que se afirma em
````

A) I e II, apenas.
B) III e IV, apenas.
C) I, II e III, apenas.
D) II, III e IV, apenas.
E) I, II, III e IV. ✔

---
