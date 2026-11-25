// Arquitetura de tema por curso (pacote orgânico).
// O app assume que o aluno entra vinculado ao seu curso — sem seletor de curso
// competindo no cabeçalho. Novos cursos entram aqui quando tiverem banco real
// de questões, ativando seu pacote visual via `data-curso` no <html>.

export const CURSO_ATUAL = 'engenharia-computacao';

/**
 * Catálogo de identidade por curso.
 * Cores semânticas (acerto verde, erro terracota, atenção âmbar) nunca mudam
 * entre cursos — só acento principal, marcos e atmosfera tipográfica.
 */
export const CURSOS = {
	'engenharia-computacao': {
		id: 'engenharia-computacao',
		nome: 'Engenharia da Computação',
		nomeCurto: 'Eng. da Computação',
		sigla: 'EC',
		ativo: true,
		corClaro: '#2347B8',
		corEscuro: '#6D93FF',
		marcoClaro: '#D97706',
		marcoEscuro: '#F5A623'
	},
	direito: {
		id: 'direito',
		nome: 'Direito',
		nomeCurto: 'Direito',
		sigla: 'DIR',
		ativo: false,
		corClaro: '#7E1D34',
		corEscuro: '#E27A92',
		marcoClaro: '#B7791F',
		marcoEscuro: '#E8B85C'
	},
	enfermagem: {
		id: 'enfermagem',
		nome: 'Enfermagem',
		nomeCurto: 'Enfermagem',
		sigla: 'ENF',
		ativo: false,
		corClaro: '#0F6B6E',
		corEscuro: '#56C9CC',
		marcoClaro: '#D96B4F',
		marcoEscuro: '#F3947A'
	}
};

export function cursoAtual(id = CURSO_ATUAL) {
	return CURSOS[id] ?? CURSOS[CURSO_ATUAL];
}

/** Aplica `data-curso` no <html> (seguro em SSR). */
export function aplicarCurso(id = CURSO_ATUAL) {
	if (typeof document === 'undefined') return;
	const c = cursoAtual(id);
	document.documentElement.dataset.curso = c.id;
}
