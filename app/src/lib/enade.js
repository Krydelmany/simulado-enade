/**
 * Data da prova da turma (ENADE 2026). Mudou a edição, mude aqui: a home
 * mostra a contagem até ela e some com o aviso depois da data.
 */
export const DATA_ENADE = '2026-11-29';

/**
 * Dias inteiros de hoje (fuso do aparelho) até `DATA_ENADE`. Negativo depois
 * da prova. Só chamar no cliente: no prerender a data ficaria congelada no
 * dia do build.
 * @param {Date} [hoje]
 * @returns {number}
 */
export function diasAteEnade(hoje = new Date()) {
	const [a, m, d] = DATA_ENADE.split('-').map(Number);
	const prova = new Date(a, m - 1, d);
	const base = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate());
	return Math.round((prova - base) / 86400000);
}
