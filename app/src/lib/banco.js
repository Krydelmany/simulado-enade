// Banco de questões: carregamento, cache e utilidades de classificação.
//
// Sem `$app/environment`: guardas em tempo de execução (`typeof window`) —
// assim a lógica roda igual em Node (testes) e no SSR.
//
// PORQUÊ cache + paralelismo: no 3G/4G do celular, 8 `await` em fila somam a
// latência de 8 idas ao servidor; em `Promise.all` é uma só. E a cache de
// sessão evita repetir tudo na navegação entre páginas (no SPA o módulo é
// recarregado, a rede não precisa ser).

/**
 * Versão do banco embutida no código. **Bumpe a cada deploy que adicione/
 * altere JSON em `static/banco`** — é o que invalida a cache sem depender da
 * rede (um deploy novo sempre traz uma versão nova).
 */
export const VERSAO_BANCO = '87f41c0da48c';

/** Arquivos do banco (um por edição+parte). Exportado para o preload. */
export const ARQUIVOS_BANCO = [
	'enade2019-fg.json',
	'enade2019-ce.json',
	'enade2023-fg.json',
	'enade2023-ce.json',
	'enade2014-fg.json',
	'enade2014-ce.json',
	'enade2017-fg.json',
	'enade2017-ce.json',
	'geradas.json'
];

const CHAVE_CACHE = 'enade-banco';
const TTL_CACHE_MS = 6 * 60 * 60 * 1000; // 6 h: cobre o dia de estudo, não atrapalha deploy

/**
 * URL de um arquivo do banco, com a versão na query.
 *
 * O `vercel.json` serve `/banco/*` com `stale-while-revalidate`: logo depois
 * de um deploy, o navegador entrega o JSON ANTIGO na hora e só busca o novo
 * em segundo plano. Sem a versão na URL, o app gravava esse JSON velho na
 * cache de sessão já com a versão NOVA — e o aluno via a questão antiga por
 * até 6 h (aconteceu com o deploy das 160 questões: 2023-FG-Q09 continuou
 * sem as afirmações). Com `?v=`, cada deploy pede um endereço que nenhuma
 * cache tem.
 */
export function urlBanco(arquivo) {
	return `/banco/${arquivo}?v=${VERSAO_BANCO}`;
}

/** Tamanho mínimo de uma sessão por nível (as telas pedem 10 questões). */
export const NIVEL_MINIMO = 10;

/**
 * Níveis do modo Estudo. Os três primeiros são as questões GERADAS para
 * revisão (`fonte: 'gerada'`), separadas por dificuldade; o quarto é a prova
 * oficial do INEP inteira, sem nível — a dificuldade de uma questão do ENADE
 * é a da prova, não uma escada.
 *
 * O valor de `dificuldade` no JSON segue o vocabulário que o banco já usava
 * ("Média", feminino: é a questão que é média); a tela mostra o nível.
 */
export const NIVEL_ENADE = 4;
const ROTULO_NIVEL = { 1: 'Fácil', 2: 'Média', 3: 'Difícil' };

/** Questão escrita para revisão (não é do INEP). Sem `fonte` = oficial. */
export function ehGerada(q) {
	return q?.fonte === 'gerada';
}

function session() {
	if (typeof window === 'undefined') return null;
	try {
		return window.sessionStorage || null;
	} catch {
		return null;
	}
}

function lerCache() {
	const s = session();
	if (!s) return null;
	try {
		const raw = s.getItem(CHAVE_CACHE);
		if (!raw) return null;
		const c = JSON.parse(raw);
		// A versão vem do código, não da rede: deploy novo = cache descartada.
		if (!c || c.versao !== VERSAO_BANCO || !Array.isArray(c.questoes)) return null;
		if (Date.now() - c.em > TTL_CACHE_MS) return null;
		return c.questoes;
	} catch {
		return null;
	}
}

function gravarCache(questoes) {
	const s = session();
	if (!s) return false;
	try {
		s.setItem(CHAVE_CACHE, JSON.stringify({ versao: VERSAO_BANCO, em: Date.now(), questoes }));
		return true;
	} catch {
		// cota do sessionStorage — segue sem cache
		return false;
	}
}

/**
 * Carrega todos os JSONs do banco (pasta `static/banco`) EM PARALELO.
 * Nunca lança: arquivo que falha (offline, 404, deploy no meio) vira `[]`.
 * Só grava a cache quando os 9 arquivos vieram — cache parcial seria pior que
 * nenhuma, porque o TTL a manteria por 6 h.
 *
 * @returns {Promise<object[]>} as questões que chegaram (pode ser parcial).
 */
export async function carregarBanco() {
	return (await carregarBancoDetalhado()).questoes;
}

/**
 * Como `carregarBanco`, dizendo também se o banco veio INTEIRO.
 *
 * Quem decide algo pela AUSÊNCIA de uma questão precisa disso: com um JSON
 * faltando, "o id não está no banco" não quer dizer que a questão deixou de
 * existir. O simulado apagava a prova salva do aluno (até a já entregue) ao
 * abrir sem internet numa aba nova.
 *
 * @returns {Promise<{questoes: object[], completo: boolean}>}
 */
export async function carregarBancoDetalhado() {
	if (typeof fetch !== 'function') return { questoes: [], completo: false };
	const cache = lerCache();
	// a cache só existe quando os 9 arquivos chegaram
	if (cache) return { questoes: cache, completo: true };

	const resultados = await Promise.all(
		ARQUIVOS_BANCO.map(async (arquivo) => {
			try {
				const r = await fetch(urlBanco(arquivo));
				if (!r.ok) return { questoes: [], ok: false };
				const lote = await r.json();
				return { questoes: Array.isArray(lote) ? lote : [], ok: true };
			} catch {
				// arquivo ainda não existe / offline — ignora este lote
				return { questoes: [], ok: false };
			}
		})
	);

	const questoes = [];
	let completo = true;
	for (const r of resultados) {
		questoes.push(...r.questoes);
		if (!r.ok) completo = false;
	}
	if (completo && questoes.length) gravarCache(questoes);
	return { questoes, completo };
}

/**
 * Dispara o download do banco cedo, antes do JS pedir: injeta um
 * `<link rel="preload" as="fetch" crossorigin>` por arquivo. Deve rodar no
 * cliente e idealmente ANTES de `carregarBanco()`.
 *
 * Como chamar (não mexe em `app.html`, que está fora deste escopo):
 *  - opção A (melhor): colar no `<head>` de `app.html`, estático, antes de
 *    `%sveltekit.head%`:
 *      {ARQUIVOS_BANCO.map(a => `<link rel="preload" as="fetch" crossorigin href="${urlBanco(a)}">`)}
 *    (com a MESMA url do fetch, versão incluída — senão o preload baixa à toa)
 *  - opção B: chamar `precarregar()` no início do `onMount` do layout/home.
 *
 * @returns {string[]} as URLs enfileiradas (útil para teste/telemetria).
 */
export function precarregar() {
	const urls = ARQUIVOS_BANCO.map(urlBanco);
	if (typeof document === 'undefined') return urls;
	for (const href of urls) {
		try {
			if (document.querySelector(`link[data-enade-preload="${href}"]`)) continue;
			const link = document.createElement('link');
			link.rel = 'preload';
			link.as = 'fetch';
			link.crossOrigin = 'anonymous'; // exigido pelo preload de fetch
			link.href = href;
			link.dataset.enadePreload = href;
			document.head.appendChild(link);
		} catch {
			// DOM indisponível/estranho — sem preload, o fetch normal resolve
		}
	}
	return urls;
}

export function embaralhar(lista) {
	const a = [...(Array.isArray(lista) ? lista : [])];
	for (let i = a.length - 1; i > 0; i--) {
		const j = Math.floor(Math.random() * (i + 1));
		[a[i], a[j]] = [a[j], a[i]];
	}
	return a;
}

/**
 * A questão pertence ao nível? 1–3 = geradas daquela dificuldade; 4 = oficiais.
 * Questão oficial nunca entra em 1–3, mesmo tendo `dificuldade` no JSON: o
 * campo ficou como registro da revisão, não como nível de estudo.
 */
export function doNivel(q, nivel) {
	if (Number(nivel) === NIVEL_ENADE) return !ehGerada(q);
	return ehGerada(q) && q.dificuldade === ROTULO_NIVEL[nivel];
}

/**
 * Quantas questões o banco oferece para um nível. A UI usa para avisar em vez
 * de montar sessão vazia/curta em silêncio.
 *
 * No banco inteiro cada nível de geradas tem 60 (3 por matéria × 20) e o
 * ENADE tem 156 — todos ≥ 10. Com o filtro de matéria do Estudo, um nível
 * fica com 3: é aí que o aviso de sessão curta aparece.
 *
 * @returns {{ok: boolean, total: number, minimo: number, nivel: number, rotulo: string|null}}
 */
export function nivelDisponivel(banco, nivel, minimo = NIVEL_MINIMO) {
	const lista = Array.isArray(banco) ? banco : [];
	const total = lista.filter((q) => doNivel(q, nivel)).length;
	const rotulo = Number(nivel) === NIVEL_ENADE ? 'ENADE' : (ROTULO_NIVEL[nivel] ?? null);
	return { ok: total >= minimo, total, minimo, nivel, rotulo };
}

/**
 * Contagens prontas para a home (evita a UI varrer o banco e reimplementar).
 * `fg`/`ce` seguem a convenção da home: OBJETIVAS por parte (batem com a
 * grade "FG objetivas / CE objetivas / Discursivas", que não soma o total
 * porque a discursiva aparece nos dois eixos). `fgTotal`/`ceTotal` dão o
 * número completo por parte quando precisar.
 *
 * Tudo aqui é da prova OFICIAL — é o que a meta da home (156) mede. As geradas vêm
 * à parte em `geradas`/`geradasPorDificuldade`, para a home não anunciar
 * "336 / 156 questões da prova".
 */
export function contagens(banco) {
	const todas = Array.isArray(banco) ? banco : [];
	const lista = todas.filter((q) => !ehGerada(q));
	const geradas = todas.filter(ehGerada);
	const c = {
		total: lista.length,
		geradas: geradas.length,
		geradasPorDificuldade: {},
		objetivas: 0,
		discursivas: 0,
		fg: 0,
		ce: 0,
		fgTotal: 0,
		ceTotal: 0,
		porEdicao: {},
		porDificuldade: {}
	};
	for (const q of lista) {
		const discursiva = q.tipo === 'discursiva';
		if (discursiva) c.discursivas++;
		else c.objetivas++;

		if (q.parte === 'FG') {
			c.fgTotal++;
			if (!discursiva) c.fg++;
		} else {
			c.ceTotal++;
			if (!discursiva) c.ce++;
		}

		const edicao = String(q.edicao ?? '?');
		c.porEdicao[edicao] = (c.porEdicao[edicao] || 0) + 1;

		const dif = q.dificuldade || 'Sem nível';
		c.porDificuldade[dif] = (c.porDificuldade[dif] || 0) + 1;
	}
	for (const q of geradas) {
		const dif = q.dificuldade || 'Sem nível';
		c.geradasPorDificuldade[dif] = (c.geradasPorDificuldade[dif] || 0) + 1;
	}
	return c;
}

/**
 * Chave estável de uma questão para histórico/erros. O `id` do banco já é
 * único entre edições (`2019-CE-Q09` ≠ `2023-CE-Q09`), então ele manda; o
 * fallback monta a mesma forma a partir dos campos, para questões antigas ou
 * importadas à mão.
 */
export function chaveQuestao(q) {
	if (!q) return '';
	if (q.id) return String(q.id);
	const prefixo = q.tipo === 'discursiva' ? 'D' : 'Q';
	return `${q.edicao ?? ''}-${q.parte ?? ''}-${prefixo}${q.numero ?? ''}`;
}

/** Alias explícito de `chaveQuestao` (mesma função). */
export const idEstavel = chaveQuestao;

export function rotuloQuestao(q) {
	if (!q) return '';
	// gerada não tem edição nem parte de prova: o id já diz tudo (GER-XVIII-F1)
	if (ehGerada(q)) return `REF ${q.id}`;
	// `numero` pode vir número em algum JSON — normaliza antes de montar o rótulo.
	const numero = String(q.numero ?? '');
	const n = q.tipo === 'discursiva' ? `D${numero}` : `Q${numero}`;
	return `REF ${q.edicao}-${q.parte}-${n}`;
}
