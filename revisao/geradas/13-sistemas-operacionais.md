# Geradas — XIII. Sistemas Operacionais — PARA REVISÃO

Área da Portaria INEP nº 161/2026: *sistemas operacionais*. 9 questões escritas para revisão (não são do INEP). Confira o gabarito de cada uma; para corrigir, edite `banco/geradas/` e rode `python3 banco/geradas.py`.

---

## GER-XIII-F1 — Estados de um processo
- **Gabarito:** D
- Nível: **Fácil**

````text
Um processo solicitou a leitura de um arquivo em disco e não pode continuar até que a operação de E/S termine.

Enquanto aguarda, esse processo está no estado
````

A) em execução.
B) pronto.
C) novo.
D) bloqueado (em espera). ✔
E) terminado.

---

## GER-XIII-F2 — Troca de contexto
- **Gabarito:** E
- Nível: **Fácil**

````text
Em um sistema multitarefa, o escalonador interrompe o processo em execução e passa o processador para outro processo.

A troca de contexto, nessa operação, consiste em
````

A) compilar novamente o código do processo interrompido.
B) apagar a memória do processo interrompido.
C) transferir o processo interrompido para outro computador.
D) reiniciar o sistema operacional.
E) salvar o estado do processo em execução (registradores, contador de programa etc.) e carregar o estado do próximo processo. ✔

---

## GER-XIII-F3 — Threads e processos
- **Gabarito:** A
- Nível: **Fácil**

````text
Um servidor web cria várias threads dentro de um mesmo processo para atender requisições simultâneas.

As threads de um mesmo processo compartilham
````

A) o espaço de endereçamento e os recursos do processo, como arquivos abertos. ✔
B) a mesma pilha de execução.
C) o mesmo contador de programa.
D) os mesmos valores de registradores durante a execução.
E) nenhum recurso, pois cada thread é isolada das demais.

---

## GER-XIII-M1 — Escalonamento SJF
- **Gabarito:** B
- Nível: **Média**

````text
Três processos chegam juntos ao sistema, no instante 0, com os seguintes tempos de CPU: P1 = 6 ms, P2 = 3 ms e P3 = 1 ms. O escalonamento é feito pelo algoritmo SJF (menor job primeiro), não preemptivo.

O tempo médio de espera dos processos é de, aproximadamente,
````

A) 5,0 ms.
B) 1,67 ms. ✔
C) 3,33 ms.
D) 2,0 ms.
E) 6,0 ms.

---

## GER-XIII-M2 — Paginação e divisão do endereço virtual
- **Gabarito:** C
- Nível: **Média**

````text
Um sistema com endereços virtuais de 32 bits usa paginação com páginas de 4 KB.

O endereço virtual é dividido em
````

A) 12 bits para o número da página e 20 bits para o deslocamento.
B) 16 bits para o número da página e 16 bits para o deslocamento.
C) 20 bits para o número da página e 12 bits para o deslocamento. ✔
D) 22 bits para o número da página e 10 bits para o deslocamento.
E) 32 bits para o número da página, sem deslocamento.

---

## GER-XIII-M3 — Condições para deadlock
- **Gabarito:** D
- Nível: **Média**

````text
Para que ocorra um impasse (deadlock) entre processos que disputam recursos, certas condições precisam valer ao mesmo tempo.

A opção que NÃO é uma dessas condições necessárias é
````

A) exclusão mútua.
B) posse e espera.
C) não preempção de recursos.
D) escalonamento por prioridade. ✔
E) espera circular.

---

## GER-XIII-D1 — Produtor-consumidor com semáforos
- **Gabarito:** E
- Nível: **Difícil**

````text
Um sistema de aquisição de dados usa um buffer circular de N posições, compartilhado entre uma thread produtora, que insere leituras, e uma thread consumidora, que as grava em disco. A sincronização usa três semáforos: vazio, iniciado com N; cheio, iniciado com 0; e mutex, iniciado com 1.

Considerando essa solução, avalie as afirmações a seguir.

I. O produtor deve executar down(vazio) antes de down(mutex), para não ficar bloqueado segurando o mutex quando o buffer estiver cheio.
II. O semáforo mutex garante exclusão mútua no acesso aos índices e ao conteúdo do buffer.
III. Se o consumidor executar down(mutex) antes de down(cheio), pode ocorrer deadlock quando o buffer estiver vazio.

É correto o que se afirma em
````

A) I, apenas.
B) II, apenas.
C) I e III, apenas.
D) II e III, apenas.
E) I, II e III. ✔

---

## GER-XIII-D2 — Memória virtual e paginação sob demanda
- **Gabarito:** A
- Nível: **Difícil**

````text
Em um computador com 8 GB de memória física, um engenheiro executa simultaneamente uma máquina virtual, um navegador e uma ferramenta de simulação cujos espaços de endereçamento somados ultrapassam 12 GB, e o sistema continua funcionando, ainda que mais lento.

Nesse contexto, avalie as asserções a seguir e a relação proposta entre elas.

I. A memória virtual permite executar processos cujo tamanho total excede a memória física disponível.

PORQUE

II. Com paginação sob demanda, apenas as páginas efetivamente referenciadas precisam estar na memória física, e as demais permanecem em armazenamento secundário.

A respeito dessas asserções, assinale a opção correta.
````

A) As asserções I e II são proposições verdadeiras, e a II é uma justificativa correta da I. ✔
B) As asserções I e II são proposições verdadeiras, mas a II não é uma justificativa correta da I.
C) A asserção I é uma proposição verdadeira, e a II é uma proposição falsa.
D) A asserção I é uma proposição falsa, e a II é uma proposição verdadeira.
E) As asserções I e II são proposições falsas.

---

## GER-XIII-D3 — Algoritmos de substituição de páginas
- **Gabarito:** B
- Nível: **Difícil**

````text
Um processo faz referência às páginas na sequência 1, 2, 3, 1, 4, 1, 5, em um sistema com 3 quadros de memória física, inicialmente vazios. Cada referência a uma página ausente da memória conta como uma falta de página, inclusive as primeiras.

Com base nessas informações, avalie as afirmações a seguir.

I. Com o algoritmo FIFO, ocorrem 6 faltas de página.
II. Com o algoritmo LRU, ocorrem 5 faltas de página.
III. Com o algoritmo ótimo, o número de faltas seria menor que 5.
IV. No algoritmo FIFO, aumentar o número de quadros sempre reduz ou mantém o número de faltas de página.

É correto apenas o que se afirma em
````

A) I e III.
B) I e II. ✔
C) II e IV.
D) I, III e IV.
E) II, III e IV.

---
