# Geradas — I. Matemática e Estatística — PARA REVISÃO

Área da Portaria INEP nº 161/2026: *matemática e estatística*. 9 questões escritas para revisão (não são do INEP). Confira o gabarito de cada uma; para corrigir, edite `banco/geradas/` e rode `python3 banco/geradas.py`.

---

## GER-I-F1 — Média e mediana
- **Gabarito:** A
- Nível: **Fácil**

````text
Os tempos de resposta de um servidor, em milissegundos, foram medidos cinco vezes: 12, 15, 15, 18 e 40.

A mediana desses tempos é igual a
````

A) 15 ms. ✔
B) 20 ms.
C) 18 ms.
D) 12 ms.
E) 16 ms.

---

## GER-I-F2 — Derivada de polinômio
- **Gabarito:** B
- Nível: **Fácil**

````text
Considere a função f(x) = 3x² + 2x.

O valor da derivada f'(x) no ponto x = 1 é
````

A) 5.
B) 8. ✔
C) 6.
D) 11.
E) 2.

---

## GER-I-F3 — Probabilidade clássica
- **Gabarito:** C
- Nível: **Fácil**

````text
Um dado honesto de seis faces é lançado uma vez.

A probabilidade de o resultado ser um número par maior que 2 é
````

A) 1/2.
B) 1/6.
C) 1/3. ✔
D) 2/3.
E) 1/4.

---

## GER-I-M1 — Distribuição binomial
- **Gabarito:** D
- Nível: **Média**

````text
Em uma linha de montagem de placas, 10% das unidades saem com defeito, de forma independente umas das outras. Um inspetor retira 3 placas ao acaso.

A probabilidade de exatamente uma das 3 placas ser defeituosa é
````

A) 0,100.
B) 0,300.
C) 0,081.
D) 0,243. ✔
E) 0,271.

---

## GER-I-M2 — Integral definida como acumulação
- **Gabarito:** E
- Nível: **Média**

````text
A taxa de chegada de requisições a um servidor, nos primeiros segundos após um pico, é modelada por r(t) = 6t requisições por segundo, com t em segundos.

O número total de requisições recebidas entre t = 0 s e t = 2 s é
````

A) 6.
B) 24.
C) 3.
D) 18.
E) 12. ✔

---

## GER-I-M3 — Distribuição normal e regra empírica
- **Gabarito:** A
- Nível: **Média**

````text
A duração das baterias de um modelo de sensor segue distribuição aproximadamente normal, com média de 500 horas e desvio-padrão de 50 horas.

O percentual aproximado de baterias com duração entre 450 h e 550 h é
````

A) 68%. ✔
B) 95%.
C) 50%.
D) 34%.
E) 99,7%.

---

## GER-I-D1 — Regressão linear e coeficiente de determinação
- **Gabarito:** B
- Nível: **Difícil**

````text
Uma equipe de infraestrutura mediu a latência média de uma aplicação web sob diferentes cargas. Com os dados coletados, ajustou-se, pelo método dos mínimos quadrados, a reta y = 2,5x + 10, em que x é o número de usuários simultâneos, em centenas, e y é a latência média, em milissegundos. As medições cobriram cargas de 1 a 8 centenas de usuários, e o coeficiente de correlação linear obtido foi r = 0,9.

Com base nessas informações, avalie as afirmações a seguir.

I. Cada centena adicional de usuários está associada, em média, a um aumento de 2,5 ms na latência.
II. Cerca de 81% da variabilidade observada na latência é explicada pelo modelo linear.
III. O modelo garante que, com 50 centenas de usuários, a latência média será de 135 ms.

É correto o que se afirma em
````

A) I, apenas.
B) I e II, apenas. ✔
C) I e III, apenas.
D) II e III, apenas.
E) I, II e III.

---

## GER-I-D2 — Probabilidade condicional e teorema de Bayes
- **Gabarito:** C
- Nível: **Difícil**

````text
Um sistema de detecção de intrusão analisa conexões de rede. Sabe-se que 1% das conexões são ataques. Quando há ataque, o sistema emite alerta em 99% dos casos; quando não há ataque, emite alerta falso em 5% dos casos.

Nesse contexto, avalie as asserções a seguir e a relação proposta entre elas.

I. Mesmo com 99% de sensibilidade, a maior parte dos alertas emitidos pelo sistema corresponde a conexões legítimas.

PORQUE

II. A probabilidade de uma conexão ser um ataque, dado que ela gerou um alerta, é igual à sensibilidade do detector.

A respeito dessas asserções, assinale a opção correta.
````

A) As asserções I e II são proposições verdadeiras, e a II é uma justificativa correta da I.
B) As asserções I e II são proposições verdadeiras, mas a II não é uma justificativa correta da I.
C) A asserção I é uma proposição verdadeira, e a II é uma proposição falsa. ✔
D) A asserção I é uma proposição falsa, e a II é uma proposição verdadeira.
E) As asserções I e II são proposições falsas.

---

## GER-I-D3 — Processo de Poisson e distribuição exponencial
- **Gabarito:** D
- Nível: **Difícil**

````text
Um serviço de autenticação recebe requisições segundo um processo de Poisson, com taxa média de 4 requisições por segundo. A equipe de operações precisa dimensionar filas e alarmes com base nesse modelo.

Considerando essa situação, avalie as afirmações a seguir.

I. O número esperado de requisições em um intervalo de 2 segundos é 8.
II. A probabilidade de não chegar nenhuma requisição em um intervalo de 1 segundo é e⁻⁴.
III. O tempo entre chegadas consecutivas segue distribuição exponencial com média de 0,25 segundo.
IV. A variância do número de requisições em um intervalo de 1 segundo é 2.

É correto apenas o que se afirma em
````

A) I e IV.
B) II e III.
C) I, II e IV.
D) I, II e III. ✔
E) II, III e IV.

---
