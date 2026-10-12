"""Aplica tema / dificuldade / materia_ava às questões extraídas.

A taxonomia de `tema` é a de 17 áreas que o professor usou no relatório da
turma (ver INVENTARIO.md); `materia_ava` só recebe as 11 disciplinas que
existem de fato no AVA — o resto é FG transversal ou não tem matéria.
"""

import json
import sys

sys.path.insert(0, '/root/enade-simulado/banco')

# (tema, dificuldade, materia_ava) por id. `None` = FG transversal.
# Rótulos de disciplina copiados do nome da pasta no AVA.
CLASSIF = {'2019-CE-D03': ('Modelo de maturatione do processo de software e indicadores de qualidade', 'Média', 'PROJETO DE CONCLUSAO DE CURSO II'), '2019-CE-D04': ('Modelo de dados relacional e consultas SQL', 'Média', None), '2019-CE-D05': ('Modelo de dados relacional e consultas SQL', 'Difícil', None), '2019-CE-Q09': ('Ordenação e recursão: MergeSort', 'Difícil', 'PROGRAMACAO PARA CIENCIA DOS DADOS'), '2019-CE-Q10': ('Aprendizado de máquina: classificação e seleção de características', 'Média', 'PROGRAMACAO PARA CIENCIA DOS DADOS'), '2019-CE-Q11': ('Coloração de grafos e alocação de recursos', 'Difícil', 'COMPUTACAO PARALELA'), '2019-CE-Q12': ('Programação linear e região viável', 'Difícil', 'MATEMATICA APLICADA'), '2019-CE-Q13': ('Resposta em frequência e função de transferência', 'Difícil', 'TELECOMUNICACOES'), '2019-CE-Q14': ('Filtros digitais e normalização de frequência', 'Difícil', 'TELECOMUNICACOES'), '2019-CE-Q15': ('Mínimos quadrados e ajuste de reta', 'Média', 'MATEMATICA APLICADA'), '2019-CE-Q16': ('Circuitos lógicos: demultiplexador com CIs 7404 e 7411', 'Difícil', 'PROJETO DE SISTEMAS EMBARCADOS'), '2019-CE-Q17': ('Amplificador operacional e sensor NTC', 'Difícil', 'ROBOTICA INDUSTRIAL'), '2019-CE-Q18': ('Criptografia DES e 3DES', 'Média', None), '2019-CE-Q19': ('Hardware trojan e segurança de sistemas', 'Média', None), '2019-CE-Q20': ('Rigidez de software e acoplamento entre módulos', 'Difícil', None), '2019-CE-Q21': ('Critérios de decisão multicritério (HP)', 'Média', 'MATEMATICA APLICADA'), '2019-CE-Q22': ('Redes bayesianas e inferência probabilística', 'Difícil', 'ROBOTICA INDUSTRIAL'), '2019-CE-Q23': ('Autômatos de estados finitos e linguagens regulares', 'Difícil', 'TEORIA DA COMPUTACAO'), '2019-CE-Q24': ('Difusão em redes e spanning tree', 'Difícil', 'TELECOMUNICACOES'), '2019-CE-Q25': ('Recursão em cauda e otimização em Python', 'Difícil', 'PROGRAMACAO PARA CIENCIA DOS DADOS'), '2019-CE-Q26': ('Controlador PID e controlador de processo', 'Média', 'ROBOTICA INDUSTRIAL'), '2019-CE-Q27': ('Padrões de projeto: Strategy', 'Média', None), '2019-CE-Q28': ('Atraso de propagação em circuitos lógicos', 'Difícil', 'PROJETO DE SISTEMAS EMBARCADOS'), '2019-CE-Q29': ('Internet das Coisas e sistemas distribuídos', 'Fácil', 'TELECOMUNICACOES'), '2019-CE-Q30': ('Contêiner de servlets e ciclo de requisição', 'Média', None), '2019-CE-Q31': ('Estados de processos e sistema operacional', 'Média', None), '2019-CE-Q32': ('Quantização de sinal e desvio padrão', 'Média', 'ROBOTICA INDUSTRIAL'), '2019-CE-Q33': ('Impedância em trilhas de PCB (stripline)', 'Difícil', 'PROJETO DE SISTEMAS EMBARCADOS'), '2019-CE-Q34': ('Escalonamento Round Robin e troca de contexto', 'Média', 'COMPUTACAO PARALELA'), '2019-CE-Q35': ('Usabilidade: inteligibilidade e apagar', 'Fácil', 'IHC')}


def aplicar(qs):
    for q in qs:
        c = CLASSIF.get(q['id'])
        if c:
            q['tema'], q['dificuldade'], q['materia_ava'] = c
    return qs


if __name__ == '__main__':
    import montar

    ano = int(sys.argv[1])
    qs = aplicar(montar.extrair(ano))
    json.dump(qs, sys.stdout, ensure_ascii=False, indent=1)
