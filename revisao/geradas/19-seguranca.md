# Geradas — XIX. Segurança da Computação — PARA REVISÃO

Área da Portaria INEP nº 161/2026: *segurança de sistemas de computação*. 9 questões escritas para revisão (não são do INEP). Confira o gabarito de cada uma; para corrigir, edite `banco/geradas/` e rode `python3 banco/geradas.py`.

---

## GER-XIX-F1 — Pilares da segurança da informação
- **Gabarito:** C
- Nível: **Fácil**

````text
Um invasor alterou o valor de algumas notas fiscais armazenadas no servidor de uma empresa, sem que ninguém percebesse, embora os arquivos continuassem acessíveis e sigilosos.

O princípio de segurança da informação violado nesse caso foi a
````

A) confidencialidade.
B) disponibilidade.
C) integridade. ✔
D) privacidade.
E) escalabilidade.

---

## GER-XIX-F2 — Tipos de ataque
- **Gabarito:** D
- Nível: **Fácil**

````text
Milhares de dispositivos infectados passaram a enviar, ao mesmo tempo, um volume enorme de requisições ao site de uma loja virtual, que ficou fora do ar durante horas.

Esse tipo de ataque é denominado
````

A) phishing.
B) injeção de SQL.
C) homem no meio (man-in-the-middle).
D) negação de serviço distribuída (DDoS). ✔
E) ransomware.

---

## GER-XIX-F3 — Armazenamento seguro de senhas
- **Gabarito:** E
- Nível: **Fácil**

````text
Uma equipe está desenvolvendo o cadastro de usuários de um sistema web e precisa decidir como armazenar as senhas no banco de dados.

A prática recomendada é
````

A) guardar as senhas em texto puro, em uma tabela de acesso restrito.
B) cifrar as senhas com uma chave fixa escrita no código-fonte.
C) codificar as senhas em Base64.
D) armazenar o hash MD5 das senhas, sem salt.
E) aplicar uma função de hash própria para senhas, com salt, como bcrypt ou Argon2. ✔

---

## GER-XIX-M1 — Criptografia assimétrica e confidencialidade
- **Gabarito:** A
- Nível: **Média**

````text
Alice quer enviar a Bob um documento que somente Bob possa ler. Ambos têm pares de chaves pública e privada, e as chaves públicas são conhecidas por todos.

Para garantir a confidencialidade, Alice deve cifrar o documento com
````

A) a chave pública de Bob. ✔
B) a chave privada de Alice.
C) a chave privada de Bob.
D) a chave pública de Alice.
E) um hash do documento, sem usar chave.

---

## GER-XIX-M2 — Injeção de SQL
- **Gabarito:** B
- Nível: **Média**

````text
Um sistema monta a consulta de login concatenando diretamente os valores digitados pelo usuário.

```python
consulta = "SELECT * FROM usuarios WHERE login = '" + login + "' AND senha = '" + senha + "'"
```

A medida mais eficaz para eliminar a vulnerabilidade de injeção de SQL nesse código é
````

A) aumentar o tamanho máximo dos campos de login e senha.
B) usar consultas parametrizadas (prepared statements), separando o comando SQL dos dados. ✔
C) apenas ocultar as mensagens de erro do banco de dados.
D) cifrar a conexão com o banco de dados por TLS.
E) trocar as aspas simples por aspas duplas na consulta.

---

## GER-XIX-M3 — Assinatura digital
- **Gabarito:** C
- Nível: **Média**

````text
Um órgão público passou a assinar digitalmente os documentos que publica, usando a chave privada de seu certificado digital.

A assinatura digital garante
````

A) apenas a confidencialidade do documento.
B) a disponibilidade do documento em caso de ataque.
C) a autenticidade da origem, a integridade do conteúdo e o não repúdio. ✔
D) a confidencialidade e a disponibilidade do documento.
E) a compressão do documento para transmissão.

---

## GER-XIX-D1 — Vazamento de hashes de senhas
- **Gabarito:** D
- Nível: **Difícil**

````text
Uma rede social sofreu um vazamento da tabela de usuários. As senhas estavam armazenadas como hash SHA-256 simples, sem salt. Em nota, a empresa declarou que os usuários não corriam risco, pois funções de hash não podem ser invertidas.

Considerando essa situação, avalie as afirmações a seguir.

I. Senhas comuns podem ser descobertas por ataques de dicionário ou por tabelas pré-computadas (rainbow tables).
II. Usuários com a mesma senha têm o mesmo hash, o que facilita o ataque em massa.
III. Como o SHA-256 não pode ser invertido, as senhas vazadas estão totalmente protegidas.

É correto o que se afirma em
````

A) I, apenas.
B) III, apenas.
C) I e III, apenas.
D) I e II, apenas. ✔
E) I, II e III.

---

## GER-XIX-D2 — HTTPS e certificados digitais
- **Gabarito:** E
- Nível: **Difícil**

````text
Em uma campanha de conscientização, uma empresa orientou os funcionários a só digitar dados pessoais em sites que exibem o cadeado do HTTPS na barra de endereços, afirmando que isso garante que o site é confiável.

Nesse contexto, avalie as asserções a seguir e a relação proposta entre elas.

I. O HTTPS impede que um site malicioso colete os dados digitados pelo usuário.

PORQUE

II. O certificado digital de um site garante que o conteúdo do site é legítimo e livre de código malicioso.

A respeito dessas asserções, assinale a opção correta.
````

A) As asserções I e II são proposições verdadeiras, e a II é uma justificativa correta da I.
B) As asserções I e II são proposições verdadeiras, mas a II não é uma justificativa correta da I.
C) A asserção I é uma proposição verdadeira, e a II é uma proposição falsa.
D) A asserção I é uma proposição falsa, e a II é uma proposição verdadeira.
E) As asserções I e II são proposições falsas. ✔

---

## GER-XIX-D3 — DMZ, firewall e defesa em profundidade
- **Gabarito:** A
- Nível: **Difícil**

````text
Uma empresa mantém um servidor web acessível pela internet e um servidor de banco de dados com as informações dos clientes. Para reduzir riscos, a equipe de segurança vai reorganizar a rede, criando uma zona desmilitarizada (DMZ) protegida por firewall.

Considerando essa situação, avalie as afirmações a seguir.

I. O servidor web deve ficar na DMZ, e o banco de dados, na rede interna, acessível apenas pelo servidor web e somente nas portas necessárias.
II. As regras do firewall devem seguir o princípio do menor privilégio, bloqueando por padrão todo tráfego não permitido explicitamente.
III. Um sistema de detecção de intrusão (IDS) complementa o firewall, monitorando o tráfego em busca de padrões de ataque.
IV. Com firewall e DMZ, as atualizações de segurança do servidor web tornam-se desnecessárias.

É correto apenas o que se afirma em
````

A) I, II e III. ✔
B) I e IV.
C) II e IV.
D) I, III e IV.
E) II, III e IV.

---
