// Conta e turma no Supabase — OPCIONAL. Sem `VITE_SUPABASE_URL` e
// `VITE_SUPABASE_ANON_KEY` no build, `nuvemLigada` é `false`, nada daqui faz
// rede e o site continua 100% local, como sempre foi.
//
// Como funciona (decisões D3 e D4 em docs/DECISOES.md):
// - o navegador fala direto com o Supabase; quem decide o que cada um pode ler
//   é a RLS do banco (`supabase/migrations/`), não este arquivo;
// - cada resposta registrada no `stats.js` entra numa FILA no localStorage
//   (`enade-nuvem-fila`) e sobe em lotes. Sem rede, ela espera; o id é gerado
//   aqui, então reenviar nunca duplica;
// - a fila só enche com alguém logado (`enade-nuvem-conta` = id do usuário).
//   Cada item guarda o dono: se outra pessoa entrar no mesmo aparelho, o que
//   era do anterior é descartado em vez de subir na conta errada;
// - o `@supabase/supabase-js` só é baixado quando precisa (quem nunca entrou
//   não paga o peso da biblioteca).
//
// Como o `stats.js`: NUNCA lançar para quem só registra resposta. As funções
// de tela (`entrarTurma`, `painel`…) lançam `Error` com mensagem pronta.

import { aoRegistrarResposta } from './stats.js';

// `?? {}`: fora do Vite (teste em Node puro) `import.meta.env` não existe
const ENV = import.meta.env ?? {};
const URL_SUPABASE = ENV.VITE_SUPABASE_URL;
const CHAVE_ANON = ENV.VITE_SUPABASE_ANON_KEY;

export const nuvemLigada = Boolean(URL_SUPABASE && CHAVE_ANON);

/** Prefixo de curso das questões; muda quando o banco tiver outra área. */
export const CURSO = 'engcomp';

const CHAVE_FILA = 'enade-nuvem-fila';
const CHAVE_CONTA = 'enade-nuvem-conta';
const CHAVE_AUTH = 'enade-nuvem-auth';

/** Teto da fila: ~3 semanas de estudo pesado offline. Passou, cai o mais velho. */
export const TETO_FILA = 3000;
const LOTE = 200;

// ---------------------------------------------------------------------------
// localStorage (mesma disciplina do stats.js: nunca lança)
// ---------------------------------------------------------------------------

function armazem() {
	if (typeof window === 'undefined') return null;
	try {
		return window.localStorage || null;
	} catch {
		return null;
	}
}

function ler(chave, padrao) {
	try {
		const v = armazem()?.getItem(chave);
		return v == null ? padrao : JSON.parse(v);
	} catch {
		return padrao;
	}
}

function gravar(chave, valor) {
	try {
		const ls = armazem();
		if (!ls) return false;
		if (valor == null) ls.removeItem(chave);
		else ls.setItem(chave, JSON.stringify(valor));
		return true;
	} catch {
		return false;
	}
}

// ---------------------------------------------------------------------------
// Cliente (carregado sob demanda)
// ---------------------------------------------------------------------------

let promessaCliente = null;

/** @returns {Promise<import('@supabase/supabase-js').SupabaseClient | null>} */
export function cliente() {
	if (!nuvemLigada || typeof window === 'undefined') return Promise.resolve(null);
	promessaCliente ??= import('@supabase/supabase-js').then(({ createClient }) => {
		const c = createClient(URL_SUPABASE, CHAVE_ANON, {
			auth: { storageKey: CHAVE_AUTH, persistSession: true, detectSessionInUrl: true, flowType: 'pkce' }
		});
		c.auth.onAuthStateChange((evento, sessao) => {
			const id = sessao?.user?.id ?? null;
			if (id) {
				lembrarConta(id);
				enviarFila();
			} else if (evento === 'SIGNED_OUT' || evento === 'INITIAL_SESSION') {
				// sem sessão guardada (expirou, limparam o site): a fila não teria
				// como subir, então não deixa ela crescer
				lembrarConta(null);
			}
		});
		return c;
	});
	return promessaCliente;
}

/** Id de quem está logado neste aparelho (síncrono, sem rede), ou `null`. */
export function contaLocal() {
	const v = ler(CHAVE_CONTA, null);
	return typeof v === 'string' ? v : null;
}

function lembrarConta(id) {
	const antes = contaLocal();
	gravar(CHAVE_CONTA, id);
	// trocou de pessoa (ou saiu): o que sobrou na fila não é de quem está aqui
	if (antes && antes !== id) gravar(CHAVE_FILA, filaDe(id));
}

// ---------------------------------------------------------------------------
// Fila de respostas
// ---------------------------------------------------------------------------

function filaCrua() {
	const v = ler(CHAVE_FILA, []);
	return Array.isArray(v) ? v.filter((x) => x && typeof x === 'object' && x.id && x.dono) : [];
}

function filaDe(dono) {
	return dono ? filaCrua().filter((x) => x.dono === dono) : [];
}

/** Quantas respostas deste usuário ainda não subiram. */
export function pendentes() {
	return filaDe(contaLocal()).length;
}

function resultadoDe(r) {
	if (r.anulada) return 'anulada';
	if (r.certa) return 'certa';
	if (r.parcial) return 'parcial';
	return 'errada';
}

function uuid() {
	if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
	// navegador antigo sem randomUUID: v4 com getRandomValues
	const b = globalThis.crypto.getRandomValues(new Uint8Array(16));
	b[6] = (b[6] & 0x0f) | 0x40;
	b[8] = (b[8] & 0x3f) | 0x80;
	const h = [...b].map((x) => x.toString(16).padStart(2, '0')).join('');
	return `${h.slice(0, 8)}-${h.slice(8, 12)}-${h.slice(12, 16)}-${h.slice(16, 20)}-${h.slice(20)}`;
}

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/**
 * Converte uma resposta do `stats.js` na linha da tabela `respostas`.
 * `oficial` e `parte` saem do id: oficial = `AAAA-FG|CE-…`, gerada = `GER-…`.
 * `simulado_id` liga a resposta à prova agendada pelo professor; um id torto
 * viraria erro 22P02 e o lote inteiro seria descartado, então só passa uuid.
 */
export function linhaDaResposta(r, dono) {
	const id = String(r.id);
	const parte = /^\d{4}-(FG|CE)-/.exec(id)?.[1] ?? (id.startsWith('GER-') ? 'CE' : null);
	const linha = {
		id: uuid(),
		dono,
		curso: CURSO,
		questao_id: id,
		oficial: /^\d{4}-/.test(id),
		parte,
		materia: typeof r.materia === 'string' && r.materia ? r.materia.slice(0, 60) : null,
		modo: ['treino', 'estudo', 'simulado'].includes(r.modo) ? r.modo : 'treino',
		resultado: resultadoDe(r),
		duracao_ms: Math.min(Math.max(Math.round(Number(r.duracaoMs) || 0), 0), 86_400_000),
		respondida_em: new Date(r.em || Date.now()).toISOString()
	};
	// só manda a coluna quando há vínculo: um banco ainda sem a migração de
	// simulados recusaria o lote inteiro por causa de uma coluna sempre nula
	if (UUID.test(String(r.simuladoId ?? ''))) linha.simulado_id = String(r.simuladoId);
	return linha;
}

/** Põe uma resposta na fila (sem ninguém logado, não faz nada). */
export function enfileirar(r) {
	const dono = contaLocal();
	if (!nuvemLigada || !dono || !r?.id) return;
	const fila = filaDe(dono);
	fila.push(linhaDaResposta(r, dono));
	gravar(CHAVE_FILA, fila.slice(-TETO_FILA));
	agendarEnvio();
}

let timer = null;
function agendarEnvio(ms = 4000) {
	if (typeof window === 'undefined') return;
	clearTimeout(timer);
	timer = setTimeout(enviarFila, ms);
}

let enviando = null;

/** Sobe a fila em lotes. Devolve quantas subiram; erro de rede só adia. */
export function enviarFila() {
	if (enviando) return enviando;
	enviando = (async () => {
		const dono = contaLocal();
		if (!dono || (typeof navigator !== 'undefined' && navigator.onLine === false)) return 0;
		const c = await cliente();
		if (!c) return 0;
		let enviadas = 0;
		for (;;) {
			const lote = filaDe(dono).slice(0, LOTE);
			if (!lote.length) break;
			const linhas = lote.map(({ dono: _, ...l }) => l);
			const { error } = await c
				.from('respostas')
				.upsert(linhas, { onConflict: 'id', ignoreDuplicates: true });
			if (error) {
				// linha torta (check, not null, tipo): descarta o lote para não travar
				// a fila. Qualquer outro erro (rede, sessão vencida) só adia.
				if (!['23514', '23502', '22P02'].includes(error.code)) break;
			}
			const subiram = new Set(lote.map((x) => x.id));
			gravar(CHAVE_FILA, filaCrua().filter((x) => !subiram.has(x.id)));
			if (!error) enviadas += lote.length;
		}
		return enviadas;
	})()
		.catch(() => 0)
		.finally(() => {
			enviando = null;
		});
	return enviando;
}

/**
 * Liga a sincronização. Chamar uma vez no layout. Só baixa a biblioteca se
 * alguém já entrou neste aparelho, ou se a URL é a volta do login (`?code=`).
 */
export function iniciarNuvem() {
	if (!nuvemLigada || typeof window === 'undefined') return () => {};
	const cancelar = aoRegistrarResposta(enfileirar);
	const voltaDoLogin = new URLSearchParams(location.search).has('code');
	if (contaLocal() || voltaDoLogin) cliente();
	const online = () => enviarFila();
	const sumiu = () => document.visibilityState === 'hidden' && enviarFila();
	addEventListener('online', online);
	document.addEventListener('visibilitychange', sumiu);
	if (contaLocal()) agendarEnvio(1500);
	return () => {
		cancelar();
		removeEventListener('online', online);
		document.removeEventListener('visibilitychange', sumiu);
	};
}

// ---------------------------------------------------------------------------
// Conta
// ---------------------------------------------------------------------------

function falhou(error, padrao = 'Não deu para falar com o servidor. Tente de novo.') {
	const m = String(error?.message || '');
	const mensagens = {
		sem_login: 'Entre na sua conta primeiro.',
		sem_consentimento: 'Para entrar na turma, marque que concorda com o compartilhamento.',
		codigo_invalido: 'Esse código de turma não existe. Confira com o professor.',
		sem_permissao: 'Só o professor da turma pode fazer isso.',
		muitos_reportes: 'Muitos reportes em pouco tempo. Tente de novo daqui a pouco.'
	};
	for (const [k, v] of Object.entries(mensagens)) if (m.includes(k)) return new Error(v);
	// só antes da migração 4 (D15): o índice único de apelido ainda existe
	if (/membros_apelido_unico/.test(m)) return new Error('Alguém da turma já entrou com esse mesmo nome. Acrescente um sobrenome.');
	if (/apelido|membros_apelido/.test(m)) return new Error('O nome precisa ter pelo menos 2 letras.');
	if (/membros_ra/.test(m)) return new Error('RA inválido: use só números e letras (3 a 20).');
	return new Error(padrao);
}

async function obrigatorio() {
	const c = await cliente();
	if (!c) throw new Error('A conta ainda não está disponível neste site.');
	return c;
}

/** Usuário logado (`{id, email, nome}`) ou `null`. */
export async function usuarioAtual() {
	const c = await cliente();
	if (!c) return null;
	const { data } = await c.auth.getSession();
	const u = data.session?.user;
	if (!u) return null;
	lembrarConta(u.id);
	// o nome que vale é o do perfil (a pessoa pode ter corrigido); o do Google
	// é só o ponto de partida. Quem entrou por link de e-mail não tem nenhum.
	const { data: p } = await c.from('perfis').select('nome').eq('id', u.id);
	return {
		id: u.id,
		email: u.email ?? '',
		nome: p?.[0]?.nome || u.user_metadata?.full_name || u.user_metadata?.name || ''
	};
}

/** Muda o nome que o professor vê (o banco só deixa editar o próprio). */
export async function salvarNome(nome) {
	const limpo = String(nome || '').trim().replace(/\s+/g, ' ');
	if (limpo.length < 2 || limpo.length > 120) throw new Error('O nome precisa ter de 2 a 120 caracteres.');
	const c = await obrigatorio();
	const { data: s } = await c.auth.getSession();
	const eu = s.session?.user?.id;
	if (!eu) throw new Error('Entre na sua conta primeiro.');
	const { error } = await c.from('perfis').update({ nome: limpo }).eq('id', eu);
	if (error) throw falhou(error, 'Não deu para salvar o nome. Tente de novo.');
	return limpo;
}

function voltarPara(caminho) {
	return new URL(caminho, location.origin).href;
}

export async function entrarComGoogle(volta = location.pathname + location.search) {
	const c = await obrigatorio();
	const { error } = await c.auth.signInWithOAuth({
		provider: 'google',
		options: { redirectTo: voltarPara(volta) }
	});
	if (error) throw falhou(error);
}

/** Link mágico por e-mail (para quem não usa Google). */
export async function entrarComEmail(email, volta = location.pathname + location.search) {
	const c = await obrigatorio();
	const { error } = await c.auth.signInWithOtp({
		email: String(email).trim(),
		options: { emailRedirectTo: voltarPara(volta) }
	});
	if (error) throw falhou(error, 'Não deu para enviar o link. Confira o e-mail.');
}

export async function sair() {
	await enviarFila();
	const c = await cliente();
	await c?.auth.signOut();
	lembrarConta(null);
	gravar(CHAVE_FILA, null);
}

/** LGPD: apaga a conta e tudo que está no servidor. O progresso do aparelho fica. */
export async function apagarConta() {
	const c = await obrigatorio();
	const { error } = await c.rpc('apagar_minha_conta');
	if (error) throw falhou(error);
	await c.auth.signOut();
	lembrarConta(null);
	gravar(CHAVE_FILA, null);
}

// ---------------------------------------------------------------------------
// Turma
// ---------------------------------------------------------------------------

/** Matrículas do usuário: `[{papel, apelido, ra, no_ranking, turma: {...}}]`. */
export async function minhasTurmas() {
	const c = await obrigatorio();
	const { data: s } = await c.auth.getSession();
	const eu = s.session?.user?.id;
	if (!eu) return [];
	// O filtro por usuário é OBRIGATÓRIO: a RLS deixa o professor ler as
	// matrículas da turma toda (é o que o painel usa). Sem ele, a lista do
	// professor trazia a mesma turma uma vez por aluno, e a tela da conta
	// travava no carregamento (chave repetida no {#each}).
	const { data, error } = await c
		.from('membros')
		.select('papel, apelido, ra, no_ranking, entrou_em, turma:turmas(id, nome, instituicao, curso, data_prova, codigo, ranking_ativo)')
		.eq('usuario_id', eu)
		.order('entrou_em');
	if (error) throw falhou(error);
	return (data ?? []).filter((m) => m.turma?.id);
}

export async function entrarTurma({ codigo, apelido, ra = null, noRanking = true, consentiu = false }) {
	const c = await obrigatorio();
	const { data, error } = await c.rpc('entrar_turma', {
		p_codigo: String(codigo || ''),
		p_apelido: String(apelido || ''),
		p_ra: ra ? String(ra) : null,
		p_no_ranking: !!noRanking,
		p_consentiu: !!consentiu
	});
	if (error) throw falhou(error);
	return data?.[0] ?? null;
}

export async function sairDaTurma(turmaId) {
	const c = await obrigatorio();
	// a RLS só deixa apagar a própria matrícula
	const { error } = await c.from('membros').delete().eq('turma_id', turmaId);
	if (error) throw falhou(error);
}

/** Ranking da turma; `desde` (Date) limita o período (ex.: esta semana). */
export async function ranking(turmaId, desde = null) {
	const c = await obrigatorio();
	const { data, error } = await c.rpc('ranking_turma', {
		p_turma: turmaId,
		p_desde: desde ? desde.toISOString() : null
	});
	if (error) throw falhou(error);
	return data ?? [];
}

/** Tudo que o painel do professor mostra, numa ida só. */
export async function painel(turmaId) {
	const c = await obrigatorio();
	const [alunos, materias, questoes, semanas] = await Promise.all([
		c.rpc('painel_alunos', { p_turma: turmaId }),
		c.rpc('painel_materias', { p_turma: turmaId }),
		c.rpc('painel_questoes', { p_turma: turmaId, p_minimo: 3, p_limite: 20 }),
		c.rpc('painel_semanas', { p_turma: turmaId })
	]);
	const erro = [alunos, materias, questoes, semanas].find((r) => r.error)?.error;
	if (erro) throw falhou(erro);
	return {
		alunos: alunos.data ?? [],
		materias: materias.data ?? [],
		questoes: questoes.data ?? [],
		semanas: semanas.data ?? []
	};
}

// ---------------------------------------------------------------------------
// Simulado agendado pelo professor (D12)
// ---------------------------------------------------------------------------

/**
 * Simulados da turma: `[{id, titulo, questoes, objetivas, abre_em, fecha_em}]`.
 * Antes de abrir, `questoes` vem `null` para o aluno (o banco esconde).
 */
export async function simuladosDaTurma(turmaId) {
	const c = await obrigatorio();
	const { data, error } = await c.rpc('simulados_turma', { p_turma: turmaId });
	if (error) throw falhou(error);
	return data ?? [];
}

/**
 * Simulados de todas as turmas de quem está logado, com a turma junto.
 * Sem ninguém logado neste aparelho, devolve `[]` sem baixar a biblioteca.
 */
export async function meusSimulados() {
	if (!nuvemLigada || !contaLocal()) return [];
	const turmas = await minhasTurmas();
	const listas = await Promise.all(
		turmas.map(async (m) =>
			(await simuladosDaTurma(m.turma.id)).map((s) => ({ ...s, turma: m.turma, papel: m.papel }))
		)
	);
	return listas.flat();
}

/** O professor agenda: `questoes` é a lista sorteada pelo `montarProva`. */
export async function criarSimulado({ turmaId, titulo, questoes, objetivas, abreEm, fechaEm }) {
	const c = await obrigatorio();
	const { data, error } = await c.rpc('criar_simulado', {
		p_turma: turmaId,
		p_titulo: String(titulo || '').trim(),
		p_questoes: questoes,
		p_objetivas: objetivas,
		p_abre: new Date(abreEm).toISOString(),
		p_fecha: new Date(fechaEm).toISOString()
	});
	if (error) throw falhou(error, 'Não deu para agendar. Confira o título e as datas.');
	return data?.[0] ?? null;
}

export async function apagarSimulado(simuladoId) {
	const c = await obrigatorio();
	const { error } = await c.rpc('apagar_simulado', { p_simulado: simuladoId });
	if (error) throw falhou(error);
}

/** Resultado de um simulado para o painel: por aluno e por questão. */
export async function resultadoSimulado(simuladoId) {
	const c = await obrigatorio();
	const [alunos, questoes] = await Promise.all([
		c.rpc('painel_simulado', { p_simulado: simuladoId }),
		c.rpc('painel_simulado_questoes', { p_simulado: simuladoId })
	]);
	const erro = alunos.error || questoes.error;
	if (erro) throw falhou(erro);
	return { alunos: alunos.data ?? [], questoes: questoes.data ?? [] };
}

// ---------------------------------------------------------------------------
// Reporte de erro em questão (D13) — funciona sem conta
// ---------------------------------------------------------------------------

/** Motivos aceitos pelo banco, na ordem em que a tela mostra. */
export const MOTIVOS_REPORTE = [
	['gabarito', 'O gabarito está errado'],
	['enunciado', 'O enunciado ou uma alternativa tem erro'],
	['resolucao', 'A resolução está errada'],
	['imagem', 'A imagem não aparece ou está cortada'],
	['outro', 'Outro problema']
];

export async function reportarQuestao({ questaoId, motivo, detalhe = '' }) {
	const c = await obrigatorio();
	const { error } = await c.rpc('reportar_questao', {
		p_questao: String(questaoId),
		p_motivo: motivo,
		p_detalhe: String(detalhe || '').slice(0, 1000)
	});
	if (error) throw falhou(error, 'Não deu para enviar agora. Tente de novo.');
}

// ---------------------------------------------------------------------------
// Visitas ao site (D14) — contagem própria até o P5 (analytics)
// ---------------------------------------------------------------------------

// uuid sorteado neste navegador: conta pessoas em vez de cliques. Não tem
// ligação com a conta, e quem limpa o site ganha outro.
const CHAVE_APARELHO = 'enade-aparelho';

function aparelho() {
	let id = ler(CHAVE_APARELHO, null);
	if (typeof id !== 'string' || !UUID.test(id)) {
		id = uuid();
		gravar(CHAVE_APARELHO, id);
	}
	return id;
}

let ultimaVisita = '';
let primeiraVisita = true;

/**
 * Conta a abertura de uma página. Fogo e esquece: sem rede, sem a migração
 * de visitas ou com "não rastrear" ligado, não faz nada e nunca lança.
 * Usa `fetch` direto (não o `supabase-js`): quem só visita não baixa a
 * biblioteca.
 * @param {URL} url
 */
export function registrarVisita(url) {
	if (!nuvemLigada || typeof window === 'undefined') return;
	try {
		if (navigator.doNotTrack === '1' || navigator.globalPrivacyControl) return;
		const caminho = url.pathname;
		if (!/^\/[a-z0-9/-]{0,60}$/.test(caminho)) return;
		// o layout pode avisar duas vezes a mesma navegação
		const chave = caminho + url.search;
		if (chave === ultimaVisita) return;
		ultimaVisita = chave;
		// de onde veio vale só na chegada: depois, o `referrer` continua sendo
		// o do primeiro clique e toda página pareceria vir do WhatsApp
		let origem = null;
		if (primeiraVisita && document.referrer) {
			const r = new URL(document.referrer);
			if (r.host !== location.host) origem = r.hostname.replace(/^www\./, '').toLowerCase().slice(0, 100);
		}
		primeiraVisita = false;
		const cabecalhos = { apikey: CHAVE_ANON, 'Content-Type': 'application/json' };
		// chave antiga (JWT `anon`) também precisa ir no Authorization; a nova
		// (`sb_publishable_…`) não é JWT e vai só no `apikey`
		if (CHAVE_ANON.startsWith('eyJ')) cabecalhos.Authorization = `Bearer ${CHAVE_ANON}`;
		fetch(`${URL_SUPABASE}/rest/v1/rpc/registrar_visita`, {
			method: 'POST',
			headers: cabecalhos,
			body: JSON.stringify({
				p_aparelho: aparelho(),
				p_caminho: caminho,
				p_convite: url.searchParams.has('turma'),
				p_origem: origem && /^[a-z0-9.-]{1,100}$/.test(origem) ? origem : null,
				p_logado: Boolean(contaLocal()),
				p_tela: matchMedia('(pointer: coarse)').matches ? 'celular' : 'computador'
			})
		}).catch(() => {});
	} catch {
		// visita é extra: nada aqui pode atrapalhar a página
	}
}
