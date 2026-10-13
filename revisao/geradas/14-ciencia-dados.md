# Geradas — XIV. Ciência de Dados — PARA REVISÃO

Área da Portaria INEP nº 161/2026: *ciência de dados*. 9 questões escritas para revisão (não são do INEP). Confira o gabarito de cada uma; para corrigir, edite `banco/geradas/` e rode `python3 banco/geradas.py`.

---

## GER-XIV-F1 — Medidas resistentes a valores extremos
- **Gabarito:** C
- Nível: **Fácil**

````text
Um analista resume a renda dos clientes de um banco digital. Alguns poucos clientes têm renda muito acima dos demais e distorcem a análise.

A medida de tendência central menos sensível a esses valores extremos é a
````

A) média aritmética.
B) amplitude.
C) mediana. ✔
D) variância.
E) média ponderada pela renda.

---

## GER-XIV-F2 — Aprendizado supervisionado e não supervisionado
- **Gabarito:** D
- Nível: **Fácil**

````text
Uma loja virtual quer separar seus clientes em grupos com perfis de compra semelhantes, sem dispor de nenhuma classificação prévia desses clientes.

A técnica adequada para essa tarefa é
````

A) a regressão linear, um método supervisionado.
B) a classificação supervisionada.
C) o aprendizado por reforço.
D) o agrupamento (clustering), um método não supervisionado. ✔
E) a validação cruzada.

---

## GER-XIV-F3 — Agrupamento de dados com pandas
- **Gabarito:** E
- Nível: **Fácil**

````text
Um DataFrame df, da biblioteca pandas, tem as colunas estado e vendas, com uma linha por venda realizada.

```python
resultado = df.groupby('estado')['vendas'].sum()
```

A variável resultado contém
````

A) a média das vendas de cada estado.
B) o número de linhas de cada estado.
C) o DataFrame sem a coluna estado.
D) as vendas ordenadas por estado.
E) a soma das vendas de cada estado. ✔

---

## GER-XIV-M1 — Precisão e revocação
- **Gabarito:** A
- Nível: **Média**

````text
Um classificador de transações fraudulentas foi avaliado em 200 casos, com o seguinte resultado: 40 verdadeiros positivos, 10 falsos positivos, 20 falsos negativos e 130 verdadeiros negativos.

A precisão e a revocação (recall) do classificador são, respectivamente, de aproximadamente
````

A) 0,80 e 0,67. ✔
B) 0,67 e 0,80.
C) 0,85 e 0,80.
D) 0,40 e 0,20.
E) 0,80 e 0,80.

---

## GER-XIV-M2 — Sobreajuste (overfitting)
- **Gabarito:** B
- Nível: **Média**

````text
Um modelo de previsão de demanda apresentou erro de 2% nos dados de treino e de 25% nos dados de validação.

Esse comportamento indica
````

A) subajuste (underfitting); deve-se aumentar a complexidade do modelo.
B) sobreajuste (overfitting); pode-se usar regularização, mais dados de treino ou um modelo mais simples. ✔
C) um modelo bem ajustado, pronto para produção.
D) que os dados de validação devem ser incluídos no treino para reduzir o erro.
E) que a métrica de erro escolhida é inadequada para o problema.

---

## GER-XIV-M3 — Normalização min-max
- **Gabarito:** C
- Nível: **Média**

````text
Em um pré-processamento, o atributo idade é normalizado pela técnica min-max para o intervalo [0, 1]. No conjunto de dados, a menor idade é 10 anos e a maior, 60 anos.

O valor normalizado de uma idade de 30 anos é
````

A) 0,5.
B) 0,6.
C) 0,4. ✔
D) 0,3.
E) 20.

---

## GER-XIV-D1 — Vazamento de dados (data leakage)
- **Gabarito:** D
- Nível: **Difícil**

````text
Uma equipe desenvolveu um modelo para prever a inadimplência de clientes no mês seguinte. Antes de separar os dados em treino e teste, normalizou todas as colunas com a média e o desvio-padrão do conjunto completo. Entre os atributos de entrada, incluiu a coluna data_cobranca_judicial, preenchida quando o cliente já está em cobrança na Justiça. O modelo obteve 99% de acerto no teste, mas teve desempenho fraco em produção.

Considerando essa situação, avalie as afirmações a seguir.

I. Normalizar com estatísticas do conjunto completo, antes da divisão, pode vazar informação do conjunto de teste para o treino.
II. A coluna data_cobranca_judicial só é conhecida depois da inadimplência e pode inflar artificialmente o desempenho medido.
III. O uso de validação cruzada elimina qualquer risco de vazamento de dados, independentemente do pré-processamento.

É correto o que se afirma em
````

A) I, apenas.
B) III, apenas.
C) I e III, apenas.
D) I e II, apenas. ✔
E) I, II e III.

---

## GER-XIV-D2 — Correlação de Pearson
- **Gabarito:** E
- Nível: **Difícil**

````text
Ao explorar um conjunto de dados de sensores, um analista calculou o coeficiente de correlação de Pearson entre a temperatura de um equipamento e o seu consumo de energia e obteve r = 0. O gráfico de dispersão, porém, mostrava os pontos dispostos em forma de parábola.

Nesse contexto, avalie as asserções a seguir e a relação proposta entre elas.

I. Um coeficiente de Pearson igual a zero indica que não há nenhuma relação entre as duas variáveis.

PORQUE

II. O coeficiente de Pearson mede qualquer tipo de relação entre duas variáveis, linear ou não linear.

A respeito dessas asserções, assinale a opção correta.
````

A) As asserções I e II são proposições verdadeiras, e a II é uma justificativa correta da I.
B) As asserções I e II são proposições verdadeiras, mas a II não é uma justificativa correta da I.
C) A asserção I é uma proposição verdadeira, e a II é uma proposição falsa.
D) A asserção I é uma proposição falsa, e a II é uma proposição verdadeira.
E) As asserções I e II são proposições falsas. ✔

---

## GER-XIV-D3 — Agrupamento com k-means
- **Gabarito:** A
- Nível: **Difícil**

````text
Uma empresa de energia aplicou o algoritmo k-means, com k = 3, para segmentar seus clientes a partir de dois atributos: renda mensal, em reais (de 1 000 a 50 000), e número de moradores da residência (de 1 a 8). Os atributos não foram padronizados antes do agrupamento.

Considerando essa situação, avalie as afirmações a seguir.

I. Sem padronização, a renda tende a dominar o cálculo das distâncias, e o número de moradores pouco influencia os grupos.
II. O resultado do k-means pode variar conforme a inicialização dos centróides.
III. O método do cotovelo pode auxiliar na escolha do número de grupos k.
IV. O k-means garante encontrar o agrupamento ótimo global, que minimiza a soma das distâncias quadráticas aos centróides.

É correto apenas o que se afirma em
````

A) I, II e III. ✔
B) I e IV.
C) II e IV.
D) I, III e IV.
E) II, III e IV.

---
