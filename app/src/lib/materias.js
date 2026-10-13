// Taxonomia de matérias: as 20 áreas do Componente Específico (Portaria INEP
// nº 161/2026) + as matérias de Formação Geral herdadas do AVA.
//
// A lista mora em `materias.json` porque o pipeline Python (banco/) lê o mesmo
// arquivo — uma cópia em cada lado já divergiria na primeira edição. A questão
// guarda só o `id` (`q.materia`); o nome sai daqui, então renomear uma matéria
// não exige regenerar o banco.

import TAXONOMIA from './materias.json';

/** Áreas do Componente Específico, na ordem do inciso (I → XX). */
export const MATERIAS_CE = TAXONOMIA.ce;

/** Matérias de Formação Geral (sem par na lista da Portaria). */
export const MATERIAS_FG = TAXONOMIA.fg;

/** Grupos prontos para `<optgroup>`. */
export const GRUPOS_MATERIA = [
	{ rotulo: 'Componente Específico', materias: MATERIAS_CE },
	{ rotulo: 'Formação Geral', materias: MATERIAS_FG }
];

const POR_ID = new Map([...MATERIAS_CE, ...MATERIAS_FG].map((m) => [m.id, m]));

export function materiaExiste(id) {
	return POR_ID.has(id);
}

/**
 * Nome de exibição de uma matéria. Um id desconhecido volta como veio: o
 * histórico do aluno (localStorage) ainda pode ter os nomes antigos do AVA
 * ("TELECOMUNICACOES"), e mostrar isso é melhor que sumir com a linha.
 */
export function nomeMateria(id) {
	if (!id) return 'Sem matéria';
	return POR_ID.get(id)?.nome ?? String(id);
}

/** Inciso da Portaria ("XVIII") ou `null` para as de Formação Geral. */
export function incisoMateria(id) {
	return POR_ID.get(id)?.inciso ?? null;
}
