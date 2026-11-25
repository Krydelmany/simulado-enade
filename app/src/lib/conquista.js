// Bilhete efêmero "acabei de concluir esta etapa", do resumo para a trilha da
// home. Mora em sessionStorage e some ao ser lido: não é progresso (esse é do
// `stats.js`, intocado), é só o gatilho da animação de volta.

const CHAVE = 'enade-conquista';
// aba esquecida aberta não comemora uma sessão de ontem
const VALIDADE_MS = 30 * 60 * 1000;

function sessao() {
	if (typeof window === 'undefined') return null;
	try {
		return window.sessionStorage || null;
	} catch {
		return null;
	}
}

/**
 * Anota a etapa da trilha recém-concluída.
 * @param {{etapa: string, certas: number, total: number}} c `etapa` é o `href` dela na home
 */
export function anotarConquista({ etapa, certas, total }) {
	try {
		sessao()?.setItem(CHAVE, JSON.stringify({ etapa, certas, total, em: Date.now() }));
	} catch {
		// storage bloqueado ou cheio: a home só não anima
	}
}

/**
 * Lê e apaga o bilhete. `null` se não há, se venceu ou se veio estragado.
 * @returns {{etapa: string, certas: number, total: number} | null}
 */
export function consumirConquista() {
	const s = sessao();
	if (!s) return null;
	try {
		const bruto = s.getItem(CHAVE);
		s.removeItem(CHAVE); // antes do parse: bilhete estragado também some
		const c = JSON.parse(bruto ?? 'null');
		if (!c || typeof c.etapa !== 'string' || !(Date.now() - c.em < VALIDADE_MS)) return null;
		return { etapa: c.etapa, certas: Number(c.certas) || 0, total: Number(c.total) || 0 };
	} catch {
		return null;
	}
}
