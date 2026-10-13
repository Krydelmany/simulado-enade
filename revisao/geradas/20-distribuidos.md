# Geradas — XX. Sistemas Distribuídos e Paralelos — PARA REVISÃO

Área da Portaria INEP nº 161/2026: *sistemas distribuídos e processamento paralelo*. 9 questões escritas para revisão (não são do INEP). Confira o gabarito de cada uma; para corrigir, edite `banco/geradas/` e rode `python3 banco/geradas.py`.

---

## GER-XX-F1 — Teorema CAP
- **Gabarito:** B
- Nível: **Fácil**

````text
Um banco de dados distribuído tem réplicas em duas cidades. Em determinado momento, o enlace entre as cidades cai, e as réplicas deixam de se comunicar, embora continuem recebendo requisições.

Segundo o teorema CAP, durante essa partição de rede, o sistema
````

A) consegue garantir consistência, disponibilidade e tolerância a partições ao mesmo tempo.
B) precisa abrir mão da consistência forte ou da disponibilidade. ✔
C) deixa de precisar de tolerância a partições.
D) deve desligar as duas réplicas até o enlace voltar.
E) passa automaticamente a funcionar como um sistema centralizado.

---

## GER-XX-F2 — Condição de corrida
- **Gabarito:** C
- Nível: **Fácil**

````text
Duas threads incrementam a mesma variável global sem nenhum mecanismo de sincronização, e o valor final varia de uma execução para outra.

Esse problema é conhecido como
````

A) inanição (starvation).
B) deadlock.
C) condição de corrida. ✔
D) falso compartilhamento de cache.
E) inversão de prioridade.

---

## GER-XX-F3 — Chamada de procedimento remoto (RPC)
- **Gabarito:** D
- Nível: **Fácil**

````text
Em uma arquitetura de microsserviços, o serviço de pedidos chama uma função do serviço de estoque, que roda em outra máquina, escrevendo o código como se fosse uma chamada de função local. O middleware cuida da serialização dos parâmetros e da comunicação pela rede.

Esse mecanismo é denominado
````

A) memória compartilhada distribuída.
B) multicast confiável.
C) balanceamento de carga.
D) chamada de procedimento remoto (RPC). ✔
E) replicação ativa.

---

## GER-XX-M1 — Speedup e eficiência
- **Gabarito:** E
- Nível: **Média**

````text
Uma simulação leva 120 s em um processador e 40 s quando executada em paralelo em 4 processadores.

O speedup e a eficiência obtidos são, respectivamente,
````

A) 4 e 100%.
B) 3 e 33%.
C) 0,33 e 75%.
D) 80 e 75%.
E) 3 e 75%. ✔

---

## GER-XX-M2 — Relógios lógicos de Lamport
- **Gabarito:** A
- Nível: **Média**

````text
Em um sistema que usa relógios lógicos de Lamport, o processo P1 tem relógio igual a 5 e recebe uma mensagem com timestamp 8. Ao receber, o processo ajusta seu relógio para o maior valor entre o seu e o da mensagem e, em seguida, incrementa-o em uma unidade.

Após a recepção, o relógio de P1 vale
````

A) 9. ✔
B) 8.
C) 6.
D) 13.
E) 5.

---

## GER-XX-M3 — Exclusão mútua com lock
- **Gabarito:** B
- Nível: **Média**

````text
Considere o código em Python a seguir, em que a função incrementa é executada simultaneamente por duas threads, iniciadas e aguardadas (join) pelo programa principal.

```python
import threading

contador = 0
trava = threading.Lock()

def incrementa():
    global contador
    for _ in range(100000):
        with trava:
            contador += 1
```

Ao final da execução das duas threads, o valor de contador é
````

A) imprevisível e, em geral, menor que 200 000.
B) 200 000, pois o lock garante exclusão mútua no incremento. ✔
C) 100 000, pois as threads compartilham o mesmo laço.
D) 0, pois o lock impede qualquer incremento.
E) indefinido, pois o programa entra em deadlock.

---

## GER-XX-D1 — Consistência eventual
- **Gabarito:** C
- Nível: **Difícil**

````text
O carrinho de compras de uma loja virtual é replicado em servidores de três regiões geográficas, com consistência eventual: cada escrita é confirmada por uma réplica e propagada às demais em segundo plano. Clientes relataram que, logo após incluir um produto, às vezes o carrinho aparece sem ele ao recarregar a página.

Considerando essa situação, avalie as afirmações a seguir.

I. Após uma atualização, leituras feitas em outra réplica podem retornar temporariamente o valor antigo.
II. Na consistência eventual, cessadas as atualizações, as réplicas convergem para o mesmo valor.
III. Na consistência eventual, toda leitura reflete a escrita mais recente confirmada no sistema.

É correto o que se afirma em
````

A) I, apenas.
B) III, apenas.
C) I e II, apenas. ✔
D) II e III, apenas.
E) I, II e III.

---

## GER-XX-D2 — Detecção de falhas em sistemas assíncronos
- **Gabarito:** D
- Nível: **Difícil**

````text
Um serviço de monitoramento considera que um nó do cluster falhou quando ele não responde a um sinal de vida (heartbeat) em até 2 segundos. Em horários de pico, nós saudáveis, porém sobrecarregados, passaram a ser removidos do cluster por engano.

Nesse contexto, avalie as asserções a seguir e a relação proposta entre elas.

I. Em um sistema distribuído assíncrono, é sempre possível distinguir um processo que falhou de um processo que está apenas lento.

PORQUE

II. Em sistemas assíncronos, não há limite conhecido para o atraso na entrega de mensagens nem para o tempo de processamento.

A respeito dessas asserções, assinale a opção correta.
````

A) As asserções I e II são proposições verdadeiras, e a II é uma justificativa correta da I.
B) As asserções I e II são proposições verdadeiras, mas a II não é uma justificativa correta da I.
C) A asserção I é uma proposição verdadeira, e a II é uma proposição falsa.
D) A asserção I é uma proposição falsa, e a II é uma proposição verdadeira. ✔
E) As asserções I e II são proposições falsas.

---

## GER-XX-D3 — MapReduce
- **Gabarito:** E
- Nível: **Difícil**

````text
Uma empresa precisa contar a frequência de cada palavra em 1 TB de registros de atendimento e vai usar o modelo MapReduce em um cluster de 50 nós.

Considerando o funcionamento desse modelo, avalie as afirmações a seguir.

I. Na fase map, cada tarefa processa um bloco da entrada e emite pares (palavra, 1).
II. Na fase de embaralhamento (shuffle), os pares com a mesma chave são agrupados e enviados à mesma tarefa de redução.
III. Um combinador (combiner) pode somar as contagens localmente, reduzindo o volume de dados transferido pela rede.
IV. Se um nó falhar, o framework pode reexecutar as tarefas desse nó em outro nó do cluster.

É correto o que se afirma em
````

A) I e II, apenas.
B) III e IV, apenas.
C) I, II e III, apenas.
D) II, III e IV, apenas.
E) I, II, III e IV. ✔

---
