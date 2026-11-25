// Arquitetura de tema por curso (pacote orgânico).
// O app assume que o aluno entra vinculado ao seu curso — sem seletor de curso
// competindo no cabeçalho. Novos cursos entram aqui quando tiverem banco real
// de questões, ativando seu pacote visual via `data-curso` no <html>.
//
// Fonte única de verdade para CORES, SOMBRAS e TIPOGRAFIA por curso: `app.css`
// (regras `:root[data-curso='...']` e `.dark[data-curso='...']`). Este módulo
// guarda apenas metadados de identificação para não duplicar nem divergir hex.

export const CURSO_ATUAL = 'engenharia-computacao';

/**
 * Catálogo de cursos reconhecidos pela camada de tema (`data-curso`).
 * Cores semânticas (acerto verde, erro terracota, atenção âmbar) nunca mudam
 * entre cursos — só acento principal, marcos, sombras e tipografia de destaque.
 */
export const CURSOS = {
	'engenharia-computacao': {
		id: 'engenharia-computacao',
		nome: 'Engenharia de Computação',
		nomeCurto: 'Eng. de Computação',
		sigla: 'EC',
		ativo: true
	},
	direito: {
		id: 'direito',
		nome: 'Direito',
		nomeCurto: 'Direito',
		sigla: 'DIR',
		ativo: false
	},
	enfermagem: {
		id: 'enfermagem',
		nome: 'Enfermagem',
		nomeCurto: 'Enfermagem',
		sigla: 'ENF',
		ativo: false
	}
};

/**
 * Devolve os metadados do curso informado (ou do curso ativo por padrão).
 * @param {string} [id]
 */
export function cursoAtual(id = CURSO_ATUAL) {
	return CURSOS[id] ?? CURSOS[CURSO_ATUAL];
}

/**
 * Aplica `data-curso` no `<html>` (seguro em SSR/prerender).
 * @param {string} [id]
 */
export function aplicarCurso(id = CURSO_ATUAL) {
	if (typeof document === 'undefined') return;
	const c = cursoAtual(id);
	document.documentElement.dataset.curso = c.id;
}
