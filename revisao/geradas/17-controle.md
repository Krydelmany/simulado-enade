# Geradas — XVII. Automação e Controle — PARA REVISÃO

Área da Portaria INEP nº 161/2026: *automação e sistemas de controle*. 9 questões escritas para revisão (não são do INEP). Confira o gabarito de cada uma; para corrigir, edite `banco/geradas/` e rode `python3 banco/geradas.py`.

---

## GER-XVII-F1 — Controle em malha fechada
- **Gabarito:** E
- Nível: **Fácil**

````text
O sistema de climatização de uma sala mede continuamente a temperatura ambiente, compara a medição com a temperatura desejada e ajusta a potência do equipamento conforme a diferença.

Esse sistema é um exemplo de controle
````

A) em malha aberta, pois não depende da saída.
B) manual, pois exige operador.
C) por tempo, como o de um temporizador de máquina de lavar.
D) sequencial, pois executa passos fixos.
E) em malha fechada, pois usa a realimentação da saída medida. ✔

---

## GER-XVII-F2 — Ações de controle PID
- **Gabarito:** A
- Nível: **Fácil**

````text
Em um controlador PID, uma das ações acumula o erro ao longo do tempo e, com isso, elimina o erro em regime permanente para uma referência em degrau.

Essa ação é a
````

A) integral. ✔
B) proporcional.
C) derivativa.
D) liga-desliga.
E) de antecipação (feedforward).

---

## GER-XVII-F3 — Linguagens de CLP
- **Gabarito:** B
- Nível: **Fácil**

````text
Entre as linguagens de programação de controladores lógicos programáveis (CLP) definidas pela norma IEC 61131-3, uma é gráfica e baseada na representação de contatos e bobinas dos antigos diagramas de relés.

Essa linguagem é a
````

A) Texto Estruturado (ST).
B) Ladder (LD). ✔
C) Lista de Instruções (IL).
D) Python.
E) linguagem de máquina do processador.

---

## GER-XVII-M1 — Sistemas de primeira ordem
- **Gabarito:** C
- Nível: **Média**

````text
A velocidade de um motor é modelada pela função de transferência G(s) = 5 / (2s + 1). Aplica-se à entrada um degrau unitário, com o sistema inicialmente em repouso.

O valor final da saída e a constante de tempo do sistema são, respectivamente,
````

A) 1 e 2 s.
B) 5 e 0,5 s.
C) 5 e 2 s. ✔
D) 2,5 e 1 s.
E) 0 e 2 s.

---

## GER-XVII-M2 — Estabilidade pela posição dos polos
- **Gabarito:** D
- Nível: **Média**

````text
Os polos de um sistema de controle em malha fechada estão em s = −1, s = −3 + j2, s = −3 − j2 e s = 0,5.

Sobre a estabilidade desse sistema, é correto afirmar que ele é
````

A) estável, pois a maioria dos polos tem parte real negativa.
B) marginalmente estável, pois há polos complexos conjugados.
C) estável, pois nenhum polo está sobre o eixo imaginário.
D) instável, pois há um polo com parte real positiva. ✔
E) estável, pois o polo em s = 0,5 é muito próximo da origem.

---

## GER-XVII-M3 — Erro em regime permanente
- **Gabarito:** E
- Nível: **Média**

````text
Um sistema com função de transferência de malha aberta G(s) = 10 / (s + 1) é ligado em malha fechada com realimentação unitária e recebe uma referência em degrau unitário.

O erro em regime permanente é de, aproximadamente,
````

A) 0.
B) 0,1.
C) 1.
D) 0,5.
E) 0,091 (isto é, 1/11). ✔

---

## GER-XVII-D1 — Sintonia de controlador PID
- **Gabarito:** A
- Nível: **Difícil**

````text
Ao sintonizar o controlador PID de temperatura de um forno industrial, a equipe aumentou o ganho proporcional e observou resposta mais rápida, mas com sobressinal maior. Em seguida, analisou os efeitos das demais ações. O aquecedor tem potência máxima limitada.

Considerando essa situação, avalie as afirmações a seguir.

I. O aumento do ganho proporcional tende a reduzir o tempo de subida, mas pode aumentar o sobressinal.
II. A ação derivativa tende a amortecer a resposta, mas amplifica o ruído de medição de alta frequência.
III. Com a saturação do aquecedor, a ação integral pode causar o efeito windup, que é tratado com técnicas anti-windup.

É correto o que se afirma em
````

A) I, II e III. ✔
B) I, apenas.
C) II, apenas.
D) I e III, apenas.
E) II e III, apenas.

---

## GER-XVII-D2 — CLP e sensores industriais
- **Gabarito:** B
- Nível: **Difícil**

````text
Em uma linha de envase, um controlador lógico programável (CLP) aciona esteiras e válvulas a partir de sinais de sensores que detectam a passagem de latas de alumínio e de tampas de aço.

Nesse contexto, avalie as asserções a seguir e a relação proposta entre elas.

I. O CLP executa seu programa de forma cíclica: lê as entradas, executa a lógica e, em seguida, atualiza as saídas.

PORQUE

II. Sensores indutivos detectam a presença de objetos metálicos sem contato físico.

A respeito dessas asserções, assinale a opção correta.
````

A) As asserções I e II são proposições verdadeiras, e a II é uma justificativa correta da I.
B) As asserções I e II são proposições verdadeiras, mas a II não é uma justificativa correta da I. ✔
C) A asserção I é uma proposição verdadeira, e a II é uma proposição falsa.
D) A asserção I é uma proposição falsa, e a II é uma proposição verdadeira.
E) As asserções I e II são proposições falsas.

---

## GER-XVII-D3 — PID digital em software
- **Gabarito:** C
- Nível: **Difícil**

````text
O trecho a seguir, em C, é executado a cada período de amostragem dt pelo firmware de um controlador de velocidade.

```c
erro = ref - medida;
integral += erro * dt;
derivada = (erro - erro_ant) / dt;
u = Kp * erro + Ki * integral + Kd * derivada;
erro_ant = erro;
```

Com base nesse código, avalie as afirmações a seguir.

I. O termo integral é aproximado pela soma dos erros multiplicados pelo período de amostragem (aproximação retangular).
II. O termo derivativo é aproximado pela diferença regressiva entre o erro atual e o anterior.
III. O período dt deve ser constante, ou corretamente medido, para que os ganhos Ki e Kd tenham o efeito projetado.
IV. O código dispensa a escolha de um período de amostragem, pois o controle implementado é contínuo.

É correto apenas o que se afirma em
````

A) I e IV.
B) II e IV.
C) I, II e III. ✔
D) I, III e IV.
E) II, III e IV.

---
