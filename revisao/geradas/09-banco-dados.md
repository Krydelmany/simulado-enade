# Geradas — IX. Banco de Dados — PARA REVISÃO

Área da Portaria INEP nº 161/2026: *banco de dados*. 9 questões escritas para revisão (não são do INEP). Confira o gabarito de cada uma; para corrigir, edite `banco/geradas/` e rode `python3 banco/geradas.py`.

---

## GER-IX-F1 — Chave primária
- **Gabarito:** C
- Nível: **Fácil**

````text
No modelo relacional, a chave primária de uma tabela é
````

A) o atributo que referencia a chave de outra tabela.
B) o atributo que pode conter valores nulos e repetidos.
C) o atributo, ou conjunto de atributos, que identifica de forma única cada linha da tabela. ✔
D) um índice usado apenas para ordenar os resultados das consultas.
E) uma coluna cujo valor é calculado a partir das demais.

---

## GER-IX-F2 — Comandos de manipulação de dados (DML)
- **Gabarito:** D
- Nível: **Fácil**

````text
Um administrador precisa remover da tabela cliente apenas os registros de clientes inativos há mais de cinco anos, mantendo a tabela e os demais registros.

O comando SQL adequado para essa tarefa é o
````

A) DROP TABLE.
B) ALTER TABLE.
C) UPDATE.
D) DELETE. ✔
E) SELECT.

---

## GER-IX-F3 — Propriedades ACID
- **Gabarito:** E
- Nível: **Fácil**

````text
Em uma transferência bancária, o débito em uma conta e o crédito na outra devem acontecer juntos: se qualquer passo falhar, nenhum dos dois pode ficar registrado.

A propriedade das transações que garante esse comportamento é a
````

A) consistência.
B) isolamento.
C) durabilidade.
D) normalização.
E) atomicidade. ✔

---

## GER-IX-M1 — Agregação com GROUP BY e HAVING
- **Gabarito:** A
- Nível: **Média**

````text
A tabela aluno(id, nome, curso) guarda os alunos de uma universidade. Deseja-se listar os cursos com mais de 30 alunos, junto com a quantidade de alunos de cada um.

A consulta SQL correta é
````

A) SELECT curso, COUNT(*) FROM aluno GROUP BY curso HAVING COUNT(*) > 30; ✔
B) SELECT curso, COUNT(*) FROM aluno WHERE COUNT(*) > 30 GROUP BY curso;
C) SELECT curso, COUNT(*) FROM aluno ORDER BY curso HAVING COUNT(*) > 30;
D) SELECT curso FROM aluno WHERE COUNT(*) > 30;
E) SELECT COUNT(curso) FROM aluno HAVING curso > 30;

---

## GER-IX-M2 — Normalização: segunda forma normal
- **Gabarito:** B
- Nível: **Média**

````text
A tabela item_pedido(num_pedido, cod_produto, nome_produto, quantidade) tem chave primária composta (num_pedido, cod_produto). O atributo nome_produto depende apenas de cod_produto.

Essa tabela
````

A) não está na primeira forma normal, por ter chave composta.
B) não está na segunda forma normal, por haver dependência parcial da chave primária. ✔
C) está na segunda forma normal, mas não na terceira, por haver dependência transitiva.
D) está na terceira forma normal, mas não na forma normal de Boyce-Codd.
E) está plenamente normalizada.

---

## GER-IX-M3 — LEFT JOIN e agregação
- **Gabarito:** C
- Nível: **Média**

````text
Considere as tabelas a seguir.

cliente(id, nome): (1, Ana), (2, Bruno), (3, Carla)
pedido(id, cliente_id, valor): (10, 1, 100), (11, 1, 50), (12, 3, 80)

```sql
SELECT c.nome, SUM(p.valor)
FROM cliente c
LEFT JOIN pedido p ON p.cliente_id = c.id
GROUP BY c.nome;
```

O resultado dessa consulta tem
````

A) 2 linhas, e Bruno não aparece no resultado.
B) 3 linhas, e a soma de Bruno é 0.
C) 3 linhas, e a soma de Bruno é NULL. ✔
D) 3 linhas, e a soma de Ana é 100.
E) 4 linhas, uma para cada pedido mais uma para Bruno.

---

## GER-IX-D1 — Concorrência e atualização perdida
- **Gabarito:** D
- Nível: **Difícil**

````text
Duas transações concorrentes operam sobre uma conta com saldo de R$ 500,00, sem nenhum controle de concorrência. A sequência de operações é a seguinte:

1. T1 lê o saldo (500).
2. T2 lê o saldo (500).
3. T1 grava o saldo 500 − 100 = 400.
4. T2 grava o saldo 500 + 200 = 700.
5. T1 e T2 são confirmadas (commit).

Considerando essa situação, avalie as afirmações a seguir.

I. O saldo final será de R$ 600,00, como esperado.
II. Ocorre a anomalia de atualização perdida (lost update).
III. O uso de bloqueio em duas fases (2PL) estrito impediria essa anomalia.

É correto o que se afirma em
````

A) I, apenas.
B) II, apenas.
C) I e III, apenas.
D) II e III, apenas. ✔
E) I, II e III.

---

## GER-IX-D2 — Índices e custo de escrita
- **Gabarito:** E
- Nível: **Difícil**

````text
Para acelerar os relatórios, um analista propôs criar índices em todas as colunas da tabela de vendas, que recebe milhares de inserções por minuto ao longo do dia.

Nesse contexto, avalie as asserções a seguir e a relação proposta entre elas.

I. Índices sempre aceleram todas as operações sobre a tabela, inclusive inserções e atualizações.

PORQUE

II. Um índice em árvore B+ dispensa a atualização da própria estrutura quando a tabela é modificada.

A respeito dessas asserções, assinale a opção correta.
````

A) As asserções I e II são proposições verdadeiras, e a II é uma justificativa correta da I.
B) As asserções I e II são proposições verdadeiras, mas a II não é uma justificativa correta da I.
C) A asserção I é uma proposição verdadeira, e a II é uma proposição falsa.
D) A asserção I é uma proposição falsa, e a II é uma proposição verdadeira.
E) As asserções I e II são proposições falsas. ✔

---

## GER-IX-D3 — Mapeamento de relacionamento N:N
- **Gabarito:** A
- Nível: **Difícil**

````text
No modelo entidade-relacionamento de um sistema acadêmico, a entidade Aluno (identificada por matrícula) e a entidade Disciplina (identificada por código) participam do relacionamento N:N “cursa”, que tem o atributo nota. Considere que um aluno cursa cada disciplina uma única vez.

Ao mapear esse modelo para o modelo relacional, avalie as afirmações a seguir.

I. O relacionamento deve ser mapeado para uma tabela própria, com chave primária composta por matrícula e código.
II. O atributo nota deve ficar na tabela que representa o relacionamento.
III. As colunas matrícula e código, na tabela do relacionamento, são chaves estrangeiras para Aluno e Disciplina.
IV. Bastaria acrescentar a coluna código à tabela Aluno para representar o relacionamento.

É correto apenas o que se afirma em
````

A) I, II e III. ✔
B) I e IV.
C) II e IV.
D) I, III e IV.
E) II, III e IV.

---
