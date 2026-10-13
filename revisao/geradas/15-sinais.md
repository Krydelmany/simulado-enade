# Geradas — XV. Processamento de Sinais — PARA REVISÃO

Área da Portaria INEP nº 161/2026: *processamento de sinais*. 9 questões escritas para revisão (não são do INEP). Confira o gabarito de cada uma; para corrigir, edite `banco/geradas/` e rode `python3 banco/geradas.py`.

---

## GER-XV-F1 — Teorema da amostragem
- **Gabarito:** B
- Nível: **Fácil**

````text
Um sinal de áudio contém componentes de frequência de até 4 kHz.

Pelo teorema de Nyquist, a menor taxa de amostragem que permite reconstruir esse sinal sem perda de informação é de
````

A) 4 kHz.
B) 8 kHz. ✔
C) 2 kHz.
D) 16 kHz.
E) 44,1 kHz.

---

## GER-XV-F2 — Período e frequência
- **Gabarito:** C
- Nível: **Fácil**

````text
A tensão da rede elétrica de um laboratório é senoidal, com frequência de 50 Hz.

O período desse sinal é de
````

A) 50 ms.
B) 2 ms.
C) 20 ms. ✔
D) 0,5 s.
E) 5 ms.

---

## GER-XV-F3 — Tipos de filtro
- **Gabarito:** D
- Nível: **Fácil**

````text
Para remover o chiado de alta frequência de um sinal de sensor de temperatura, que varia lentamente, usa-se um filtro que deixa passar as baixas frequências e atenua as altas.

Esse filtro é do tipo
````

A) passa-altas.
B) rejeita-faixa.
C) passa-faixa.
D) passa-baixas. ✔
E) passa-tudo.

---

## GER-XV-M1 — Resolução de conversor A/D
- **Gabarito:** E
- Nível: **Média**

````text
Um conversor analógico-digital de 8 bits digitaliza sinais na faixa de 0 V a 5 V, com 2⁸ níveis de quantização.

O passo de quantização (resolução) desse conversor é de, aproximadamente,
````

A) 625 mV.
B) 39 mV.
C) 5 mV.
D) 1,95 mV.
E) 19,5 mV. ✔

---

## GER-XV-M2 — Aliasing
- **Gabarito:** A
- Nível: **Média**

````text
Um sinal senoidal de 7 kHz é amostrado a 10 kHz, sem filtro anti-aliasing.

No sinal amostrado, essa componente aparecerá com frequência de
````

A) 3 kHz. ✔
B) 7 kHz.
C) 17 kHz.
D) 10 kHz.
E) 5 kHz.

---

## GER-XV-M3 — Filtro de média móvel
- **Gabarito:** B
- Nível: **Média**

````text
Um filtro digital de média móvel é definido por y[n] = (x[n] + x[n − 1]) / 2, com x[n] = 0 para n < 0. A entrada é a sequência x = [2, 4, 6, 8], para n = 0, 1, 2, 3.

A saída y, para n = 0, 1, 2, 3, é
````

A) [2, 4, 6, 8].
B) [1, 3, 5, 7]. ✔
C) [3, 5, 7, 8].
D) [2, 6, 10, 14].
E) [1, 2, 3, 4].

---

## GER-XV-D1 — Filtros FIR e IIR
- **Gabarito:** C
- Nível: **Difícil**

````text
Uma equipe vai implementar, em um microcontrolador, o filtro digital que limpa o sinal de um eletrocardiograma e discute se usa um filtro de resposta ao impulso finita (FIR) ou infinita (IIR). A preservação da forma de onda do sinal é importante para o diagnóstico, e a capacidade de processamento é limitada.

Considerando essa situação, avalie as afirmações a seguir.

I. Filtros FIR são sempre estáveis, por não terem realimentação da saída.
II. Filtros FIR podem ter fase linear, preservando a forma de onda dos sinais na faixa de passagem.
III. Para uma mesma seletividade, filtros IIR costumam exigir ordem menor que filtros FIR.
IV. Filtros IIR têm resposta ao impulso de duração finita.

É correto apenas o que se afirma em
````

A) I e IV.
B) II e IV.
C) I, II e III. ✔
D) I, III e IV.
E) II, III e IV.

---

## GER-XV-D2 — Quantização e taxa de amostragem
- **Gabarito:** D
- Nível: **Difícil**

````text
Um engenheiro precisa digitalizar o sinal de um sensor de vibração com componentes de até 20 kHz. Para economizar, cogita manter a taxa de amostragem do sistema atual, de 25 kHz, e trocar o conversor de 10 bits por um de 16 bits.

Nesse contexto, avalie as asserções a seguir e a relação proposta entre elas.

I. Aumentar o número de bits do conversor A/D amplia a faixa de frequências que pode ser amostrada sem aliasing.

PORQUE

II. Cada bit adicional em um conversor A/D reduz pela metade o passo de quantização, o que melhora a relação sinal-ruído de quantização em cerca de 6 dB.

A respeito dessas asserções, assinale a opção correta.
````

A) As asserções I e II são proposições verdadeiras, e a II é uma justificativa correta da I.
B) As asserções I e II são proposições verdadeiras, mas a II não é uma justificativa correta da I.
C) A asserção I é uma proposição verdadeira, e a II é uma proposição falsa.
D) A asserção I é uma proposição falsa, e a II é uma proposição verdadeira. ✔
E) As asserções I e II são proposições falsas.

---

## GER-XV-D3 — Transformada discreta de Fourier
- **Gabarito:** E
- Nível: **Difícil**

````text
Para identificar a frequência de ruído em uma máquina, um sinal de vibração é amostrado a 1 000 Hz, e sobre um bloco de N = 500 amostras calcula-se a transformada discreta de Fourier (DFT), por meio do algoritmo FFT.

Com base nessas informações, avalie as afirmações a seguir.

I. A resolução em frequência da DFT é de 2 Hz.
II. A maior frequência representável sem aliasing é de 500 Hz.
III. A FFT calcula a mesma DFT com complexidade O(N log N), em vez de O(N²).
IV. Uma componente de 100 Hz aparece no índice k = 50 da DFT.

É correto o que se afirma em
````

A) I e II, apenas.
B) III e IV, apenas.
C) I, II e III, apenas.
D) II, III e IV, apenas.
E) I, II, III e IV. ✔

---
