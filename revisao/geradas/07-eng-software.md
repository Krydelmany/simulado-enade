# Geradas — VII. Engenharia de Software — PARA REVISÃO

Área da Portaria INEP nº 161/2026: *engenharia de software*. 9 questões escritas para revisão (não são do INEP). Confira o gabarito de cada uma; para corrigir, edite `banco/geradas/` e rode `python3 banco/geradas.py`.

---

## GER-VII-F1 — Modelos de processo de software
- **Gabarito:** E
- Nível: **Fácil**

````text
Em um modelo de processo de software, as fases de requisitos, projeto, implementação, testes e manutenção são executadas em sequência, e cada fase começa somente após a conclusão da anterior.

Esse modelo é conhecido como
````

A) Scrum.
B) espiral.
C) Extreme Programming (XP).
D) Kanban.
E) cascata. ✔

---

## GER-VII-F2 — Níveis de teste
- **Gabarito:** A
- Nível: **Fácil**

````text
Um desenvolvedor escreveu testes automatizados que verificam, de forma isolada, se a função que calcula o frete retorna os valores esperados para diferentes pesos e distâncias.

Esse tipo de teste é denominado teste
````

A) de unidade. ✔
B) de aceitação.
C) de sistema.
D) de usabilidade.
E) de carga.

---

## GER-VII-F3 — Requisitos funcionais e não funcionais
- **Gabarito:** B
- Nível: **Fácil**

````text
Durante o levantamento de requisitos de um sistema de vendas, a equipe listou várias necessidades.

A necessidade que corresponde a um requisito NÃO funcional é:
````

A) O sistema deve permitir cadastrar clientes.
B) O sistema deve responder a 95% das consultas em menos de 2 segundos. ✔
C) O sistema deve emitir nota fiscal para cada venda.
D) O usuário deve poder recuperar a senha por e-mail.
E) O sistema deve gerar um relatório mensal de vendas.

---

## GER-VII-M1 — Papéis no Scrum
- **Gabarito:** C
- Nível: **Média**

````text
Em um time que adota Scrum, uma pessoa é responsável por maximizar o valor do produto, gerenciar o Product Backlog e decidir a ordem de prioridade dos itens a desenvolver.

Esse papel é o de
````

A) Scrum Master.
B) desenvolvedor.
C) Product Owner. ✔
D) gerente de projeto.
E) cliente final.

---

## GER-VII-M2 — Acoplamento e coesão
- **Gabarito:** D
- Nível: **Média**

````text
Em um sistema, o módulo de relatórios lê e altera diretamente as variáveis internas do módulo de faturamento. Toda vez que a estrutura interna do faturamento muda, o módulo de relatórios quebra.

Essa situação caracteriza
````

A) alta coesão, desejável por concentrar responsabilidades relacionadas.
B) baixo acoplamento, que facilita a reutilização dos módulos.
C) alta coesão e baixo acoplamento, o que dispensa mudanças.
D) alto acoplamento, sendo recomendável que a comunicação ocorra por meio de uma interface pública bem definida. ✔
E) baixa coesão, que se resolve unindo os dois módulos em um só.

---

## GER-VII-M3 — Padrões de projeto: Singleton
- **Gabarito:** E
- Nível: **Média**

````text
Em uma aplicação, o objeto que gerencia o pool de conexões com o banco de dados deve existir em uma única instância, acessível a partir de qualquer parte do código.

O padrão de projeto que atende a essa necessidade é o
````

A) Observer.
B) Strategy.
C) Adapter.
D) Factory Method.
E) Singleton. ✔

---

## GER-VII-D1 — Integração contínua
- **Gabarito:** A
- Nível: **Difícil**

````text
Uma equipe de desenvolvimento adotou integração contínua: a cada push no repositório, um servidor compila o projeto e executa a suíte de testes automatizados, avisando a equipe quando algo falha. Em reunião, foram feitas algumas observações sobre a prática.

Considerando essa situação, avalie as afirmações a seguir.

I. A integração contínua reduz o custo de corrigir defeitos de integração, porque eles são detectados logo após a alteração que os introduziu.
II. Se todos os testes automatizados passam, está garantido que o software não tem defeitos.
III. Com integração contínua, os testes de unidade tornam-se dispensáveis, pois o servidor já verifica se o projeto compila.

É correto o que se afirma em
````

A) I, apenas. ✔
B) II, apenas.
C) I e III, apenas.
D) II e III, apenas.
E) I, II e III.

---

## GER-VII-D2 — Scrum e Manifesto Ágil
- **Gabarito:** B
- Nível: **Difícil**

````text
Uma empresa que desenvolvia software pelo modelo em cascata decidiu migrar para métodos ágeis, depois de vários projetos entregues com atraso e com funcionalidades que os clientes não usavam.

Nesse contexto, avalie as asserções a seguir e a relação proposta entre elas.

I. No Scrum, o trabalho é organizado em sprints de duração fixa, ao final das quais se produz um incremento potencialmente utilizável do produto.

PORQUE

II. O Manifesto Ágil valoriza mais os indivíduos e as interações do que os processos e as ferramentas.

A respeito dessas asserções, assinale a opção correta.
````

A) As asserções I e II são proposições verdadeiras, e a II é uma justificativa correta da I.
B) As asserções I e II são proposições verdadeiras, mas a II não é uma justificativa correta da I. ✔
C) A asserção I é uma proposição verdadeira, e a II é uma proposição falsa.
D) A asserção I é uma proposição falsa, e a II é uma proposição verdadeira.
E) As asserções I e II são proposições falsas.

---

## GER-VII-D3 — Projeto de casos de teste e valores-limite
- **Gabarito:** C
- Nível: **Difícil**

````text
O método a seguir, em Java, classifica a nota de um aluno: devolve −1 para nota inválida, 1 para aprovado e 0 para reprovado. Notas válidas vão de 0 a 100.

```java
int classificar(int nota) {
    if (nota < 0 || nota > 100) {
        return -1;
    }
    if (nota >= 60) {
        return 1;
    }
    return 0;
}
```

Com base nesse código, avalie as afirmações a seguir sobre o projeto de casos de teste.

I. Os casos de teste com nota = 59 e nota = 60 exercitam o limite entre os retornos 0 e 1.
II. Três casos de teste, com notas −5, 70 e 30, são suficientes para executar todos os comandos return do método.
III. O caso nota = 100 deve retornar −1, pois está no limite do intervalo válido.

É correto o que se afirma em
````

A) I, apenas.
B) III, apenas.
C) I e II, apenas. ✔
D) II e III, apenas.
E) I, II e III.

---
