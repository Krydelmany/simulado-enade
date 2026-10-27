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

/** "Matemática e Estatística" → "matematica e estatistica". */
function normalizarArea(nome) {
	return String(nome || '')
		.normalize('NFD')
		.replace(/\p{Diacritic}/gu, '')
		.toLowerCase()
		.replace(/[^a-z0-9]+/g, ' ')
		.trim();
}

// Nomes de área que vêm de fora (o site do professor usa os seus) → id.
const POR_AREA = new Map();
for (const m of [...MATERIAS_CE, ...MATERIAS_FG]) {
	for (const chave of [m.id, m.nome, m.oficial, ...(m.ava ?? [])]) {
		const n = normalizarArea(chave);
		if (n && !POR_AREA.has(n)) POR_AREA.set(n, m.id);
	}
}
const CHAVES_AREA = [...POR_AREA.keys()];

/**
 * Id da matéria a partir do nome de área que vem do site do professor (o
 * simulado em papel). Casa pelo id, nome, nome oficial e nome do AVA; se não
 * houver igual, aceita o começo de um nome maior ("Matemática Discreta" ×
 * "Matemática Discreta e Grafos"). Sem par, devolve `null`: a tela mostra o
 * nome como veio, em vez de chutar a matéria errada.
 */
export function materiaPorArea(nome) {
	const n = normalizarArea(nome);
	if (!n) return null;
	const exato = POR_AREA.get(n);
	if (exato) return exato;
	let melhor = null;
	for (const chave of CHAVES_AREA) {
		if (chave.length < 8) continue;
		if (chave.startsWith(`${n} `) || n.startsWith(`${chave} `)) {
			// o mais específico vence: "Matemática Discreta" casa com
			// "matemática discreta e grafos", não com "matemática"
			if (!melhor || chave.length > melhor.length) melhor = chave;
		}
	}
	return melhor ? POR_AREA.get(melhor) : null;
}
