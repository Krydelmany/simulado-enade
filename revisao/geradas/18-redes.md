# Geradas — XVIII. Redes de Computadores — PARA REVISÃO

Área da Portaria INEP nº 161/2026: *redes de comunicação e redes de computadores*. 9 questões escritas para revisão (não são do INEP). Confira o gabarito de cada uma; para corrigir, edite `banco/geradas/` e rode `python3 banco/geradas.py`.

---

## GER-XVIII-F1 — Protocolos de transporte
- **Gabarito:** D
- Nível: **Fácil**

````text
Uma aplicação de transferência de arquivos precisa que todos os bytes cheguem ao destino, sem perdas e na ordem em que foram enviados.

O protocolo de transporte da internet que oferece esse serviço, orientado à conexão, é o
````

A) UDP.
B) IP.
C) ICMP.
D) TCP. ✔
E) ARP.

---

## GER-XVIII-F2 — Camadas do modelo OSI
- **Gabarito:** E
- Nível: **Fácil**

````text
No modelo de referência OSI, uma das camadas é responsável pelo endereçamento lógico e pelo roteamento dos pacotes entre redes diferentes.

Essa camada é a de
````

A) física.
B) enlace.
C) transporte.
D) aplicação.
E) rede. ✔

---

## GER-XVIII-F3 — Resolução de nomes
- **Gabarito:** A
- Nível: **Fácil**

````text
Ao digitar o endereço www.exemplo.com.br no navegador, o computador precisa descobrir o endereço IP correspondente a esse nome antes de abrir a conexão.

O serviço responsável por essa tradução é o
````

A) DNS. ✔
B) DHCP.
C) HTTP.
D) FTP.
E) SMTP.

---

## GER-XVIII-M1 — Sub-redes e hosts utilizáveis
- **Gabarito:** B
- Nível: **Média**

````text
Um administrador criou uma sub-rede IPv4 com máscara /26 para o laboratório de uma universidade.

O número máximo de hosts que podem receber endereço nessa sub-rede, excluídos os endereços de rede e de broadcast, é
````

A) 64.
B) 62. ✔
C) 30.
D) 126.
E) 254.

---

## GER-XVIII-M2 — Tempo de transmissão
- **Gabarito:** C
- Nível: **Média**

````text
Um arquivo de 10 MB (considere 1 MB = 8 Mbit) é enviado por um enlace dedicado de 100 Mbit/s. Despreze cabeçalhos, atrasos de propagação e retransmissões.

O tempo de transmissão do arquivo é de
````

A) 0,1 s.
B) 8 s.
C) 0,8 s. ✔
D) 80 s.
E) 1,25 s.

---

## GER-XVIII-M3 — Endereço de rede a partir do IP e da máscara
- **Gabarito:** D
- Nível: **Média**

````text
Um computador está configurado com o endereço IPv4 192.168.10.77 e máscara /27.

O endereço da sub-rede a que esse computador pertence é
````

A) 192.168.10.0.
B) 192.168.10.32.
C) 192.168.10.77.
D) 192.168.10.64. ✔
E) 192.168.10.96.

---

## GER-XVIII-D1 — Controle de congestionamento do TCP
- **Gabarito:** E
- Nível: **Difícil**

````text
Ao analisar a captura de tráfego de uma transferência longa, uma equipe observou que a janela de congestionamento do TCP crescia rapidamente no início da conexão, passava depois a crescer devagar e, em alguns momentos, era reduzida após o emissor receber ACKs duplicados.

Considerando o controle de congestionamento do TCP, avalie as afirmações a seguir.

I. Na partida lenta (slow start), a janela de congestionamento cresce exponencialmente a cada RTT, até atingir o limiar.
II. Na fase de prevenção de congestionamento, a janela cresce de forma aproximadamente linear, cerca de um segmento por RTT.
III. A recepção de três ACKs duplicados é interpretada como indício de perda de segmento e leva à retransmissão rápida.

É correto o que se afirma em
````

A) I, apenas.
B) II, apenas.
C) I e III, apenas.
D) II e III, apenas.
E) I, II e III. ✔

---

## GER-XVIII-D2 — UDP em aplicações de tempo real
- **Gabarito:** A
- Nível: **Difícil**

````text
Em uma chamada de voz pela internet, perder alguns milissegundos de áudio quase não é percebido pelos participantes, mas atrasos acima de algumas centenas de milissegundos tornam a conversa difícil.

Nesse contexto, avalie as asserções a seguir e a relação proposta entre elas.

I. Aplicações de voz sobre IP costumam usar o UDP para transportar a mídia.

PORQUE

II. Em áudio em tempo real, retransmitir pacotes perdidos costuma ser inútil, pois eles chegariam tarde demais, e o UDP não impõe retransmissões nem controle de congestionamento.

A respeito dessas asserções, assinale a opção correta.
````

A) As asserções I e II são proposições verdadeiras, e a II é uma justificativa correta da I. ✔
B) As asserções I e II são proposições verdadeiras, mas a II não é uma justificativa correta da I.
C) A asserção I é uma proposição verdadeira, e a II é uma proposição falsa.
D) A asserção I é uma proposição falsa, e a II é uma proposição verdadeira.
E) As asserções I e II são proposições falsas.

---

## GER-XVIII-D3 — VLANs e domínios de broadcast
- **Gabarito:** B
- Nível: **Difícil**

````text
Uma empresa ocupa dois andares, cada um com um switch gerenciável, ligados entre si por um único cabo. Ela quer separar o tráfego do setor financeiro, que tem computadores nos dois andares, do tráfego dos demais setores, e para isso vai configurar VLANs.

Considerando essa situação, avalie as afirmações a seguir.

I. Computadores em VLANs diferentes precisam de um roteador ou de um switch de camada 3 para se comunicar.
II. As VLANs reduzem o domínio de broadcast, pois os quadros de broadcast ficam restritos à VLAN de origem.
III. O enlace entre os dois switches deve ser configurado como tronco (trunk), com marcação IEEE 802.1Q, para transportar mais de uma VLAN.
IV. Hubs separam domínios de colisão por porta, assim como os switches.

É correto apenas o que se afirma em
````

A) I e IV.
B) I, II e III. ✔
C) II e IV.
D) I, III e IV.
E) II, III e IV.

---
