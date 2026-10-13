# Geradas — XI. Sistemas Digitais e Embarcados — PARA REVISÃO

Área da Portaria INEP nº 161/2026: *sistemas digitais e sistemas embarcados*. 9 questões escritas para revisão (não são do INEP). Confira o gabarito de cada uma; para corrigir, edite `banco/geradas/` e rode `python3 banco/geradas.py`.

---

## GER-XI-F1 — Conversão de binário para decimal
- **Gabarito:** A
- Nível: **Fácil**

````text
Um sensor digital envia o valor binário 1011₂.

Esse valor, em decimal, é
````

A) 11. ✔
B) 13.
C) 9.
D) 1011.
E) 7.

---

## GER-XI-F2 — Portas lógicas
- **Gabarito:** B
- Nível: **Fácil**

````text
Em uma máquina industrial, o motor só deve ligar quando a porta de proteção estiver fechada E o operador pressionar o botão de partida. Cada condição é representada por um sinal lógico que vale 1 quando satisfeita.

A porta lógica que implementa essa regra é a
````

A) OR.
B) AND. ✔
C) XOR.
D) NOR.
E) NOT.

---

## GER-XI-F3 — Conversão de hexadecimal para decimal
- **Gabarito:** C
- Nível: **Fácil**

````text
Um registrador de um microcontrolador contém o valor 0x2F.

Esse valor, em decimal, é
````

A) 32.
B) 215.
C) 47. ✔
D) 63.
E) 42.

---

## GER-XI-M1 — Simplificação booleana
- **Gabarito:** D
- Nível: **Média**

````text
Considere a função booleana F = A·B + A·B̄, em que B̄ é o complemento de B.

A forma simplificada de F é
````

A) B.
B) A + B.
C) A·B.
D) A. ✔
E) 1.

---

## GER-XI-M2 — Contadores com flip-flops
- **Gabarito:** E
- Nível: **Média**

````text
Um contador binário síncrono é construído com 4 flip-flops do tipo T e conta em sequência a partir de 0, voltando a 0 após o último valor.

O número de estados distintos percorridos por esse contador é
````

A) 4.
B) 8.
C) 15.
D) 32.
E) 16. ✔

---

## GER-XI-M3 — Manipulação de bits em C embarcado
- **Gabarito:** A
- Nível: **Média**

````text
Em um microcontrolador, o registrador de 8 bits PORTB controla 8 pinos de saída. Deseja-se colocar em nível alto o pino correspondente ao bit 3 (bits numerados de 0 a 7), sem alterar os demais pinos.

A instrução em C que faz isso é
````

A) PORTB |= (1 << 3); ✔
B) PORTB = (1 << 3);
C) PORTB &= (1 << 3);
D) PORTB ^= ~(1 << 3);
E) PORTB &= ~(1 << 3);

---

## GER-XI-D1 — Interrupções e baixo consumo
- **Gabarito:** B
- Nível: **Difícil**

````text
Um registrador de eventos alimentado por bateria deve contar quantas vezes um botão mecânico é acionado ao longo do dia e permanecer, na maior parte do tempo, em modo de baixo consumo. O projetista discute como tratar o botão no firmware do microcontrolador.

Considerando essa situação, avalie as afirmações a seguir.

I. Usar uma interrupção externa associada ao pino do botão permite que o microcontrolador fique em modo de espera até o acionamento.
II. Ler o botão por varredura contínua (polling), em laço, é a solução de menor consumo de energia.
III. Rotinas de tratamento de interrupção devem ser curtas, deixando o processamento demorado para o laço principal.
IV. Contatos mecânicos geram repiques (bouncing), que podem ser tratados por filtro RC ou por software.

É correto apenas o que se afirma em
````

A) I e II.
B) I, III e IV. ✔
C) II e IV.
D) I, II e III.
E) II, III e IV.

---

## GER-XI-D2 — Multiplexadores como geradores de funções
- **Gabarito:** C
- Nível: **Difícil**

````text
Em projetos com lógica programável e em provas de conceito em bancada, multiplexadores são usados não só para selecionar sinais, mas também para implementar funções booleanas diretamente a partir da tabela-verdade.

Nesse contexto, avalie as asserções a seguir e a relação proposta entre elas.

I. Um multiplexador 8:1 pode implementar qualquer função booleana de 3 variáveis.

PORQUE

II. Um multiplexador 8:1 possui 8 linhas de seleção, uma para cada mintermo da função.

A respeito dessas asserções, assinale a opção correta.
````

A) As asserções I e II são proposições verdadeiras, e a II é uma justificativa correta da I.
B) As asserções I e II são proposições verdadeiras, mas a II não é uma justificativa correta da I.
C) A asserção I é uma proposição verdadeira, e a II é uma proposição falsa. ✔
D) A asserção I é uma proposição falsa, e a II é uma proposição verdadeira.
E) As asserções I e II são proposições falsas.

---

## GER-XI-D3 — Circuito votador por maioria
- **Gabarito:** D
- Nível: **Difícil**

````text
Um sistema de segurança redundante usa três sensores, A, B e C, que valem 1 quando detectam falha. Para evitar alarmes falsos causados por um único sensor defeituoso, a saída S deve valer 1 somente quando pelo menos dois sensores indicarem falha.

Com base nessa especificação, avalie as afirmações a seguir.

I. A expressão mínima de S em soma de produtos é S = AB + AC + BC.
II. A tabela-verdade de S tem exatamente 4 linhas com saída igual a 1.
III. A expressão S = A ⊕ B ⊕ C implementa a mesma função.
IV. A função pode ser implementada usando apenas portas NAND.

É correto apenas o que se afirma em
````

A) I e III.
B) II e III.
C) I, III e IV.
D) I, II e IV. ✔
E) II, III e IV.

---
