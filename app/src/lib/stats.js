// Estado persistente do aluno, 100% em `localStorage` (site estático, sem backend).
//
// PORQUÊ sem `$app/environment`: o módulo é puro em relação ao SvelteKit — só
// checagens de ambiente em tempo de execução (`typeof window`). Assim a mesma
// lógica roda em Node (testes) sem precisar de stub de `$app/environment`, e no
// SSR as funções devolvem os valores padrão em vez de quebrar.
//
// Regra de ouro deste arquivo: NUNCA lançar. Storage cheio, bloqueado (aba
// privada) ou com JSON corrompido deve degradar silenciosamente para o padrão.

const CHAVE_XP = 'enade-xp';
const CHAVE_ERROS = 'enade-erros';
const CHAVE_SESSAO = 'enade-sessao';
const CHAVE_HISTORICO = 'enade-historico';
const CHAVE_REVISAR = 'enade-revisar';

/**
 * Tetos do histórico. O `localStorage` tem ~5 MB por origem; sem teto, um
 * aluno dedicado enche a cota e passa a perder escritas. Recortamos mantendo
 * o mais recente — os agregados por questão são o que importa a longo prazo.
 */
export const TETO_HISTORICO = {
	questoes: 400, // questões distintas guardadas (agregado, não o enunciado)
	dias: 60, // dias de contagem diária
	sessoes: 60, // últimas sessões completas
	bytes: 150_000 // trava final em bytes do JSON serializado
};

const UM_DIA_MS = 24 * 60 * 60 * 1000;

// ---------------------------------------------------------------------------
// Acesso ao storage
// ---------------------------------------------------------------------------

/** `localStorage` ou `null` (SSR, aba privada, política de cookies). */
function armazem() {
	if (typeof window === 'undefined') return null;
	try {
		return window.localStorage || null;
	} catch {
		return null;
	}
}

/** Lê e deserializa; qualquer problema (inclusive JSON inválido) devolve o padrão. */
function ler(chave, padrao) {
	const ls = armazem();
	if (!ls) return padrao;
	try {
		const v = ls.getItem(chave);
		return v === null ? padrao : JSON.parse(v);
	} catch {
		return padrao;
	}
}

/** Serializa e grava. Devolve `true`/`false` em vez de lançar (cota, bloqueio). */
function gravar(chave, valor) {
	const ls = armazem();
	if (!ls) return false;
	try {
		ls.setItem(chave, JSON.stringify(valor));
		return true;
	} catch {
		return false;
	}
}

function remover(chave) {
	const ls = armazem();
	if (!ls) return;
	try {
		ls.removeItem(chave);
	} catch {
		// ignora — remover falhando não é motivo para derrubar a página
	}
}

// ---------------------------------------------------------------------------
// Helpers numéricos/datas
// ---------------------------------------------------------------------------

function inteiro(n) {
	const v = Number(n);
	return Number.isFinite(v) ? Math.trunc(v) : 0;
}

/**
 * Formata um número para exibição (pt-BR): `1234` -> `"1.234"`.
 * Centralizado aqui para não espalhar `toLocaleString` pela UI. Se `Intl`
 * não existir (ambiente exótico), cai no `String()` simples.
 */
export function formatarNumero(n) {
	const v = Number(n);
	if (!Number.isFinite(v)) return '0';
	try {
		return new Intl.NumberFormat('pt-BR').format(v);
	} catch {
		return String(v);
	}
}

/** Data local no formato `YYYY-MM-DD` (chave dos dias do histórico). */
function diaLocal(ms) {
	const d = new Date(ms);
	const p = (n) => String(n).padStart(2, '0');
	return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

// ---------------------------------------------------------------------------
// XP e erros (contratos antigos — assinaturas preservadas)
// ---------------------------------------------------------------------------

export function getXP() {
	const v = ler(CHAVE_XP, 0);
	return typeof v === 'number' && Number.isFinite(v) ? v : 0;
}

export function somarXP(n) {
	const total = getXP() + (Number(n) || 0);
	gravar(CHAVE_XP, total);
	return total;
}

/**
 * @deprecated Legado. O *streak* foi removido de propósito do produto; esta
 * função fica só para não quebrar imports antigos e não é usada em lugar
 * nenhum (grep confirmado). Não ressuscitar o recurso por causa dela.
 */
export function getStreak() {
	return ler('enade-streak', { dias: 0, ultimo: '' });
}

export function registrarErro(id) {
	if (!id) return;
	const erros = ler(CHAVE_ERROS, []);
	if (!Array.isArray(erros)) {
		gravar(CHAVE_ERROS, [id]);
		return;
	}
	if (!erros.includes(id)) {
		erros.push(id);
		gravar(CHAVE_ERROS, erros);
	}
}

export function removerErro(id) {
	const erros = ler(CHAVE_ERROS, []);
	gravar(
		CHAVE_ERROS,
		(Array.isArray(erros) ? erros : []).filter((e) => e !== id)
	);
}

export function getErros() {
	const erros = ler(CHAVE_ERROS, []);
	return Array.isArray(erros) ? erros.slice() : [];
}

// ---------------------------------------------------------------------------
// Marcações de "revisar depois" — bucket SEPARADO da lista de erros.
//
// São coisas diferentes: erro é "voce errou esta questão", marcação é "quero
// voltar nesta". Confundir os dois faz o aluno desmarcar uma questão que ele
// errou e ela sumir da revisão de erros — ou acertar uma marcada e ela
// sumir da lista de revisões. Guardar no mesmo balde torna os dois recursos
// impossíveis de usar ao mesmo tempo.
// ---------------------------------------------------------------------------

/** @returns {string[]} ids marcados para revisão. */
export function getRevisar() {
	const v = ler(CHAVE_REVISAR, []);
	return Array.isArray(v) ? v.slice() : [];
}

export function marcarRevisar(id) {
	if (!id) return;
	const v = ler(CHAVE_REVISAR, []);
	const lista = Array.isArray(v) ? v : [];
	if (!lista.includes(id)) gravar(CHAVE_REVISAR, [...lista, id]);
}

export function desmarcarRevisar(id) {
	gravar(
		CHAVE_REVISAR,
		getRevisar().filter((x) => x !== id)
	);
}

/** Liga/desliga e devolve o novo estado. */
export function alternarRevisar(id) {
	if (!id) return false;
	if (getRevisar().includes(id)) {
		desmarcarRevisar(id);
		return false;
	}
	marcarRevisar(id);
	return true;
}

/** Ids a revisar = erros ainda não corrigidos + marcações do aluno. */
export function getParaRevisar() {
	const erros = new Set(getErros());
	for (const id of getRevisar()) erros.add(id);
	return [...erros];
}

/**
 * Quantas questões a revisão do treino abre de fato: só os ids a revisar
 * que ainda estão no banco. Uma questão que saiu do banco (as anuladas, um id
 * de gerada renumerado) continua no aparelho do aluno, e o botão "Revisar"
 * mostrava um número maior do que a revisão abria — ou aparecia e levava a
 * uma revisão vazia.
 *
 * @param {Array<{id: string}>} banco
 * @returns {number}
 */
export function contarParaRevisar(banco) {
	const ids = new Set(getParaRevisar());
	return (Array.isArray(banco) ? banco : []).filter((q) => ids.has(q.id)).length;
}

// ---------------------------------------------------------------------------
// Sessão de treino pausada (contrato antigo)
// ---------------------------------------------------------------------------

/** Sessão de treino pausada (para continuar depois). */
export function salvarSessao(s) {
	gravar(CHAVE_SESSAO, s);
}

export function carregarSessao() {
	return ler(CHAVE_SESSAO, null);
}

export function limparSessao() {
	remover(CHAVE_SESSAO);
}

// ---------------------------------------------------------------------------
// Histórico de respostas (novo)
// ---------------------------------------------------------------------------

function estadoVazio() {
	return {
		v: 1,
		totais: { respondidas: 0, certas: 0, parciais: 0 },
		questoes: {},
		dias: {},
		sessoes: []
	};
}

/**
 * Valida/normaliza o que veio do storage. Um JSON válido pode ter a forma
 * errada (número, array, campo faltando); sem isso, um `estado.questoes`
 * `undefined` derrubaria a UI. Tudo o que não casa vira o padrão.
 */
function normalizarEstado(v) {
	const e = estadoVazio();
	if (!v || typeof v !== 'object' || Array.isArray(v)) return e;

	if (v.totais && typeof v.totais === 'object') {
		e.totais.respondidas = inteiro(v.totais.respondidas);
		e.totais.certas = inteiro(v.totais.certas);
		e.totais.parciais = inteiro(v.totais.parciais);
	}

	if (v.questoes && typeof v.questoes === 'object' && !Array.isArray(v.questoes)) {
		for (const [id, q] of Object.entries(v.questoes)) {
			if (!q || typeof q !== 'object') continue;
			e.questoes[id] = {
				id: typeof q.id === 'string' ? q.id : id,
				respostas: inteiro(q.respostas),
				acertos: inteiro(q.acertos),
				erros: inteiro(q.erros),
				parciais: inteiro(q.parciais),
				materia: typeof q.materia === 'string' ? q.materia : undefined,
				tema: typeof q.tema === 'string' ? q.tema : undefined,
				ultimaEm: inteiro(q.ultimaEm)
			};
		}
	}

	if (v.dias && typeof v.dias === 'object' && !Array.isArray(v.dias)) {
		for (const [dia, x] of Object.entries(v.dias)) {
			if (!/^\d{4}-\d{2}-\d{2}$/.test(dia) || !x || typeof x !== 'object') continue;
			e.dias[dia] = {
				respondidas: inteiro(x.respondidas),
				certas: inteiro(x.certas),
				parciais: inteiro(x.parciais)
			};
		}
	}

	if (Array.isArray(v.sessoes)) {
		for (const s of v.sessoes) {
			if (!s || typeof s !== 'object') continue;
			e.sessoes.push({
				em: inteiro(s.em),
				modo: typeof s.modo === 'string' ? s.modo : null,
				nivel: Number.isFinite(Number(s.nivel)) ? Number(s.nivel) : null,
				respondidas: inteiro(s.respondidas),
				certas: inteiro(s.certas),
				duracaoMs: inteiro(s.duracaoMs)
			});
		}
	}

	return e;
}

function lerEstado() {
	return normalizarEstado(ler(CHAVE_HISTORICO, null));
}

function tamanhoBytes(e) {
	try {
		return JSON.stringify(e).length;
	} catch {
		return 0;
	}
}

/** Aplica os tetos, do menos para o mais drástico. Muta `e` e devolve `e`. */
function recortar(e) {
	// Sessões: só as últimas interessam para "últimos 7 dias".
	if (e.sessoes.length > TETO_HISTORICO.sessoes) {
		e.sessoes = e.sessoes.slice(-TETO_HISTORICO.sessoes);
	}

	// Dias: a chave ISO ordena lexicograficamente = cronologicamente.
	const dias = Object.keys(e.dias).sort();
	if (dias.length > TETO_HISTORICO.dias) {
		const manter = new Set(dias.slice(-TETO_HISTORICO.dias));
		for (const d of dias) if (!manter.has(d)) delete e.dias[d];
	}

	// Questões: mantém as respondidas mais recentemente.
	const ids = Object.keys(e.questoes);
	if (ids.length > TETO_HISTORICO.questoes) {
		ids.sort((a, b) => (e.questoes[a].ultimaEm || 0) - (e.questoes[b].ultimaEm || 0));
		for (const id of ids.slice(0, ids.length - TETO_HISTORICO.questoes)) delete e.questoes[id];
	}

	// Trava final: se ainda estourou (cota real menor que o esperado), corta
	// pela metade as partes "de detalhe" repetidamente.
	let voltas = 0;
	while (tamanhoBytes(e) > TETO_HISTORICO.bytes && voltas < 8) {
		voltas++;
		e.sessoes = e.sessoes.slice(-Math.max(1, Math.floor(e.sessoes.length / 2)));
		const chaves = Object.keys(e.dias).sort();
		const manter = new Set(chaves.slice(-Math.max(1, Math.floor(chaves.length / 2))));
		for (const d of chaves) if (!manter.has(d)) delete e.dias[d];
		const qids = Object.keys(e.questoes);
		if (qids.length > 1) {
			qids.sort((a, b) => (e.questoes[a].ultimaEm || 0) - (e.questoes[b].ultimaEm || 0));
			for (const id of qids.slice(0, Math.floor(qids.length / 2))) delete e.questoes[id];
		}
	}
	return e;
}

/**
 * Grava com degradação: se a cota estourar mesmo após o recorte, sacrifica o
 * detalhe (sessões/dias) e preserva os agregados por questão + totais.
 */
function gravarEstado(e) {
	recortar(e);
	if (gravar(CHAVE_HISTORICO, e)) return true;
	const magro = { v: e.v, totais: e.totais, questoes: e.questoes, dias: {}, sessoes: [] };
	return gravar(CHAVE_HISTORICO, magro);
}

// Quem quiser saber de cada resposta (hoje: a fila da nuvem, `nuvem.js`) se
// inscreve aqui. O `stats.js` continua sem saber que existe servidor.
const ouvintes = new Set();

/**
 * Inscreve `fn` para receber cada resposta registrada. Devolve o cancelamento.
 * Um ouvinte que lança não derruba o registro (regra de ouro deste arquivo).
 * @param {(r: {id: string, certa: boolean, parcial: boolean, anulada: boolean, materia?: string, modo?: string, duracaoMs: number, em: number}) => void} fn
 */
export function aoRegistrarResposta(fn) {
	ouvintes.add(fn);
	return () => ouvintes.delete(fn);
}

/**
 * Registra UMA resposta. Guarda só o agregado por questão (`id` + contadores),
 * nunca o enunciado — o texto já vive no JSON do banco e duplicá-lo estouraria
 * o storage rápido.
 *
 * `modo` (`'treino'`, `'estudo'`, `'simulado'`) e `simuladoId` (prova agendada
 * pelo professor) só vão para os ouvintes: o agregado local não os guarda.
 *
 * `parcial` (discursiva autoavaliada) e `anulada` contam como "respondida" mas
 * não como acerto nem erro — mesma semântica das telas de treino/estudo.
 *
 * @returns {object|null} o agregado atualizado da questão, ou `null` sem `id`.
 */
export function registrarResposta({
	id,
	certa = false,
	parcial = false,
	anulada = false,
	materia,
	tema,
	modo,
	simuladoId = null,
	duracaoMs = 0
} = {}) {
	if (!id) return null;
	const e = lerEstado();
	const agora = Date.now();

	// Totais de vida inteira: nunca são recortados, então sobrevivem ao teto.
	e.totais.respondidas += 1;
	if (certa) e.totais.certas += 1;
	else if (parcial) e.totais.parciais += 1;

	// Contagem diária (alimenta "hoje" e "últimos 7 dias").
	const dia = diaLocal(agora);
	const d = e.dias[dia] || (e.dias[dia] = { respondidas: 0, certas: 0, parciais: 0 });
	d.respondidas += 1;
	if (certa) d.certas += 1;
	else if (parcial) d.parciais += 1;

	// Agregado da questão.
	const q = e.questoes[id] || (e.questoes[id] = { id, respostas: 0, acertos: 0, erros: 0, parciais: 0 });
	q.respostas += 1;
	if (certa) q.acertos += 1;
	else if (parcial) q.parciais += 1;
	else if (!anulada) q.erros += 1;
	if (typeof materia === 'string' && materia) q.materia = materia;
	if (typeof tema === 'string' && tema) q.tema = tema;
	if (inteiro(duracaoMs)) q.duracaoMs = inteiro(duracaoMs);
	q.ultimaEm = agora;

	gravarEstado(e);
	for (const fn of ouvintes) {
		try {
			fn({ id, certa, parcial, anulada, materia, modo, simuladoId, duracaoMs: inteiro(duracaoMs), em: agora });
		} catch {
			// a nuvem é extra: falhar lá não pode perder a resposta aqui
		}
	}
	return q;
}

/**
 * Registra uma SESSÃO concluída (para "hoje: 12 respondidas" e histórico).
 * @param {{modo?: string, nivel?: number, respondidas?: number, certas?: number, duracaoMs?: number}} s
 */
export function registrarSessao({ modo, nivel, respondidas = 0, certas = 0, duracaoMs = 0 } = {}) {
	const e = lerEstado();
	e.sessoes.push({
		em: Date.now(),
		modo: typeof modo === 'string' ? modo : null,
		nivel: Number.isFinite(Number(nivel)) ? Number(nivel) : null,
		respondidas: inteiro(respondidas),
		certas: inteiro(certas),
		duracaoMs: inteiro(duracaoMs)
	});
	gravarEstado(e);
}

/**
 * Leitura bruta do histórico, pronta para inspeção (não para desenhar).
 * @returns {{questoes: object[], sessoes: object[], dias: object[], totalQuestoes: number, totalSessoes: number}}
 */
export function historico() {
	const e = lerEstado();
	const questoes = Object.values(e.questoes).sort((a, b) => (b.ultimaEm || 0) - (a.ultimaEm || 0));
	const sessoes = [...e.sessoes].sort((a, b) => b.em - a.em);
	const dias = Object.keys(e.dias)
		.sort()
		.map((dia) => ({ dia, ...e.dias[dia] }));
	return { questoes, sessoes, dias, totalQuestoes: questoes.length, totalSessoes: sessoes.length };
}

/**
 * Agregados numéricos para a UI (a formatação pt-BR fica em `resumo.js`).
 * Tudo derivado de `localStorage`, nada mutado.
 */
export function resumo() {
	const e = lerEstado();
	const agora = Date.now();

	const agrupar = (campo) => {
		const mapa = new Map();
		for (const q of Object.values(e.questoes)) {
			const chave = q[campo] || 'Sem matéria';
			if (!mapa.has(chave)) mapa.set(chave, { respondidas: 0, acertos: 0, erros: 0 });
			const m = mapa.get(chave);
			m.respondidas += q.respostas;
			m.acertos += q.acertos;
			m.erros += q.erros;
		}
		return [...mapa.entries()]
			.map(([nome, m]) => ({
				nome,
				respondidas: m.respondidas,
				acertos: m.acertos,
				erros: m.erros,
				precisao: m.acertos + m.erros > 0 ? m.acertos / (m.acertos + m.erros) : 0
			}))
			.sort((a, b) => b.respondidas - a.respondidas || a.precisao - b.precisao);
	};

	// Últimos 7 dias locais, incluindo os dias sem resposta (barras zeradas).
	const dias = [];
	for (let k = 6; k >= 0; k--) {
		const iso = diaLocal(agora - k * UM_DIA_MS);
		const x = e.dias[iso] || { respondidas: 0, certas: 0, parciais: 0 };
		dias.push({ dia: iso, respondidas: x.respondidas, certas: x.certas, parciais: x.parciais });
	}
	const soma = (lista) =>
		lista.reduce(
			(acc, d) => ({ respondidas: acc.respondidas + d.respondidas, certas: acc.certas + d.certas }),
			{ respondidas: 0, certas: 0 }
		);
	const o7 = soma(dias);
	const hojeIso = diaLocal(agora);
	const hojeBruto = e.dias[hojeIso] || { respondidas: 0, certas: 0, parciais: 0 };

	const respondidas = e.totais.respondidas;
	const certas = e.totais.certas;

	const ultimaQuestao = Object.values(e.questoes).reduce((m, q) => Math.max(m, q.ultimaEm || 0), 0);
	const ultimaSessao = e.sessoes.reduce((m, s) => Math.max(m, s.em || 0), 0);
	const ultimoTreino = Math.max(ultimaQuestao, ultimaSessao) || null;

	return {
		xp: getXP(),
		respondidas,
		certas,
		parciais: e.totais.parciais,
		precisao: respondidas > 0 ? certas / respondidas : 0,
		porMateria: agrupar('materia'),
		porTema: agrupar('tema'),
		errosAtivos: getErros(),
		ultimoTreino,
		sessaoPausada: carregarSessao(),
		hoje: { dia: hojeIso, ...hojeBruto },
		ultimos7: {
			respondidas: o7.respondidas,
			certas: o7.certas,
			precisao: o7.respondidas > 0 ? o7.certas / o7.respondidas : 0
		},
		dias
	};
}

/**
 * Limpa o progresso de estudo: histórico de respostas e lista de erros.
 * XP e a sessão pausada são MANTIDOS de propósito (XP é conquista, não
 * "progresso a resetar"); remova as chaves na mão se precisar de reset total.
 */
export function limparProgresso() {
	remover(CHAVE_HISTORICO);
	remover(CHAVE_ERROS);
}
