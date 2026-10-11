import { browser } from '$app/environment';

/** Carrega todos os JSONs do banco (pasta static/banco). */
export async function carregarBanco() {
	const arquivos = ['enade2019-fg.json'];
	const questoes = [];
	for (const arq of arquivos) {
		try {
			const r = await fetch(`/banco/${arq}`);
			if (!r.ok) continue;
			const lote = await r.json();
			questoes.push(...lote);
		} catch {
			// arquivo ainda não existe — ignora
		}
	}
	return questoes;
}

export function embaralhar(lista) {
	const a = [...lista];
	for (let i = a.length - 1; i > 0; i--) {
		const j = Math.floor(Math.random() * (i + 1));
		[a[i], a[j]] = [a[j], a[i]];
	}
	return a;
}

/** Nível de estudo -> dificuldade. Sem dificuldade definida cai em todos (até a revisão). */
export function doNivel(q, nivel) {
	const mapa = { 1: 'Fácil', 2: 'Média', 3: 'Difícil' };
	if (!q.dificuldade) return true;
	return q.dificuldade === mapa[nivel];
}

export function rotuloQuestao(q) {
	const n = q.tipo === 'discursiva' ? `D${q.numero}` : `Q${q.numero}`;
	return `REF ${q.edicao}-${q.parte}-${n}`;
}
