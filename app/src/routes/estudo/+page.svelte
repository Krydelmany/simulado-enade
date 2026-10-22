<script>
	import { onMount } from 'svelte';
	import { fly } from 'svelte/transition';
	import Questao from '$lib/Questao.svelte';
	import SessaoTopo from '$lib/SessaoTopo.svelte';
	import BarraAcao from '$lib/BarraAcao.svelte';
	import Contador from '$lib/Contador.svelte';
	import DicaGestos from '$lib/DicaGestos.svelte';
	import { DUR } from '$lib/motion.js';
	import { deslizarQuestoes } from '$lib/gestos.js';
	import { ligarCamadas } from '$lib/camadas.svelte.js';
	import { carregarBancoDetalhado, embaralhar, doNivel, NIVEL_ENADE } from '$lib/banco.js';
	import { remontarSessao } from '$lib/sessao.js';
	import { GRUPOS_MATERIA, materiaExiste, nomeMateria } from '$lib/materias.js';
	import {
	somarXP,
	getXP,
	getErros,
	registrarErro,
	removerErro,
	getRevisar,
	marcarRevisar,
	desmarcarRevisar,
	contarParaRevisar,
	registrarResposta,
	registrarSessao
} from '$lib/stats.js';
	import { ArrowLeft, ArrowsClockwise, Info, Lightning, Play, SealCheck, Tag, Target, Timer, Trophy } from 'phosphor-svelte';

	const TOTAL = 10;
	// 1–3: questões geradas para revisão, em escada de dificuldade.
	// 4: a prova oficial do INEP, sem nível — ver NIVEL_ENADE em banco.js.
	const NIVEIS = {
		1: { nome: 'Fácil', desc: 'Conceito direto, contexto simples.' },
		2: { nome: 'Médio', desc: 'Aplicação com um passo a mais de raciocínio.' },
		3: { nome: 'Difícil', desc: 'Situação-problema no modelo do ENADE.' },
		[NIVEL_ENADE]: { nome: 'ENADE oficial', desc: 'Questões das provas do INEP, objetivas e discursivas.' }
	};
	const ESCADA = [1, 2, 3];
	// sessão de estudo pausada — chave própria para não colidir com a sessão do treino
	const CHAVE = 'enade-sessao-estudo';

	let banco = $state([]);
	let nivel = $state(null);
	// filtro opcional: 'todas' ou o id de uma matéria (materias.json)
	let materiaFiltro = $state('todas');
	let sessao = $state([]);
	let i = $state(0);
	// respostas[i] guarda a resposta da questão i (para voltar e reexibir o veredito)
	let respostas = $state([]);
	let log = $state([]);
	let fim = $state(false);
	let inicio = $state(Date.now());
	let xp = $state(0);
	let xpGanho = $state(0);
	let xpPing = $state(0);
	let ultimoToque = $state(0);
	let xpValor = $state(10);
	let carregou = $state(false);
	let falhou = $state(false);
	// estudo pausado que não deu para remontar porque o banco veio pela metade
	let sessaoGuardada = $state(false);
	let vazioNivel = $state(null);
	let escolhaE = $state(false);
	let salvaE = $state(null);
	let confirmaSaida = $state(false);
	let zoomAberto = $state(false);
	// o banco chegou inteiro? (decide se a sessão pausada pode ser remontada)
	let bancoInteiro = $state(false);
	// sentido da última troca de questão: a nova entra deslizando por ele
	let direcao = $state(0);

	// O seletor de níveis é a base da rota; o quiz é uma camada por cima.
	// Antes, o voltar do sistema no meio do quiz saía do estudo e caía na
	// home. Quiz → fim troca no mesmo nível, então o voltar no fim leva ao
	// seletor (a sessão já foi registrada e não há o que retomar).
	ligarCamadas(
		() =>
			nivel === null
				? []
				: fim
					? ['fim']
					: ['quiz', confirmaSaida && 'saida', zoomAberto && 'zoom'].filter(Boolean),
		(n) => {
			if (n === 'quiz') sairAgora();
			else if (n === 'fim') nivel = null;
			else if (n === 'saida') confirmaSaida = false;
			else if (n === 'zoom') zoomAberto = false;
		}
	);

	// a questão nova abria no meio da rolagem da anterior
	function topo() {
		window.scrollTo({ top: 0 });
	}
	let refSaida = $state(null);

	// contadores derivados do log — navegar para frente/voltar nunca conta duas vezes
	let feitas = $derived(log.filter((r) => !r.pulada).length);
	let certas = $derived(log.filter((r) => r.certa).length);
	let parciais = $derived(log.filter((r) => r.parcial).length);
	let ultima = $derived(i + 1 >= sessao.length);
	let podeAvancar = $derived(!!respostas[i]);
	// quantas questões cada nível tem de verdade, já com o filtro de matéria
	// (para não prometer 10 e entregar 3)
	let contagens = $derived.by(() => {
		const c = {};
		for (const n of [...ESCADA, NIVEL_ENADE]) c[n] = doFiltro(n).length;
		return c;
	});
	// só entram no select as matérias que têm alguma questão no banco
	let gruposFiltro = $derived.by(() => {
		const n = new Map();
		for (const q of banco) if (q.materia) n.set(q.materia, (n.get(q.materia) || 0) + 1);
		return GRUPOS_MATERIA.map((g) => ({
			rotulo: g.rotulo,
			materias: g.materias.filter((m) => n.get(m.id))
		})).filter((g) => g.materias.length);
	});
	let salvaEfeitas = $derived(salvaE ? (salvaE.log || []).filter((r) => !r.pulada).length : 0);
	let salvaECertas = $derived(salvaE ? (salvaE.log || []).filter((r) => r.certa).length : 0);

	onMount(async () => {
		try {
			({ questoes: banco, completo: bancoInteiro } = await carregarBancoDetalhado());
			xp = getXP();
		} catch {
			falhou = true;
		} finally {
			carregou = true;
		}
		oferecerContinuar();
	});

	// Também roda ao sair do quiz: antes o seletor não oferecia "Continuar?",
	// e começar outro nível ali chamava `limparSessao()` e apagava a sessão
	// salva.
	function oferecerContinuar() {
		salvaE = null;
		escolhaE = false;
		const s = lerSessao();
		if (s?.ids?.length) {
			// v1 = antes da escada de geradas: a sessão era só de questões
			// oficiais, então hoje ela é do nível ENADE (o número antigo 1–3
			// mostraria "Fácil" em cima de uma questão do INEP)
			if (s.v === 1) s.nivel = NIVEL_ENADE;
			const achadas = s.ids.map((id) => banco.find((q) => q.id === id));
			// Banco pela metade: a questão que falta pode estar no JSON que não
			// chegou. Antes a sessão voltava encurtada em silêncio, e a primeira
			// resposta regravava a versão curta por cima da inteira.
			if (!bancoInteiro && !achadas.every(Boolean)) {
				sessaoGuardada = true;
				return;
			}
			// banco inteiro: o que falta saiu do banco — remonta reindexando o
			// que é guardado por posição (ver `remontarSessao`)
			const r = remontarSessao(s.ids, banco, s);
			if (r.fila.length) {
				salvaE = { ...s, sessao: r.fila, respostas: r.respostas, log: r.log, i: r.i, removidas: r.removidas };
				escolhaE = true;
			}
		}
	}

	$effect(() => {
		if (confirmaSaida && refSaida) refSaida.focus();
	});

	function doFiltro(n) {
		return banco.filter(
			(q) => doNivel(q, n) && (materiaFiltro === 'todas' || q.materia === materiaFiltro)
		);
	}

	function comecar(n) {
		const pool = embaralhar(doFiltro(n));
		if (!pool.length) {
			vazioNivel = n;
			return;
		}
		vazioNivel = null;
		direcao = 0;
		nivel = n;
		sessao = pool.slice(0, TOTAL);
		i = 0;
		respostas = [];
		log = [];
		fim = false;
		xpGanho = 0;
		xpPing = 0;
		inicio = Date.now();
		limparSessao();
		persistir();
	}

	function registrar(idx, dados) {
		log = [...log.filter((r) => r.idx !== idx), { idx, ...dados }];
	}

	function aoResponder(r) {
		const q = sessao[i];
		// histórico persistente — ver nota equivalente em `treino/+page.svelte`
		registrarResposta({
			modo: 'estudo',
			id: r.id,
			certa: !!r.certa,
			parcial: !!r.parcial,
			anulada: !!r.anulada,
			materia: q?.materia,
			tema: q?.tema,
			duracaoMs: Date.now() - (ultimoToque || inicio)
		});
		ultimoToque = Date.now();
		// guarda também `respondida: true` para o Questao reexibir o veredito ao voltar
		respostas[i] = { ...r, respondida: true };
		registrar(i, {
			id: r.id,
			materia: q?.materia || '?',
			certa: !!r.certa,
			parcial: !!r.parcial,
			anulada: !!r.anulada,
			pulada: false
		});
		if (r.anulada) {
			// ponto para todos: conta como acerto, mas não rende XP (não houve mérito)
		} else if (r.certa) {
			somarXP(10);
			xp = getXP();
			xpGanho += 10;
			xpPing++;
			xpValor = 10;
			removerErro(r.id);
		} else if (r.parcial) {
			somarXP(5);
			xp = getXP();
			xpGanho += 5;
			xpPing++;
			xpValor = 5;
		} else {
			registrarErro(r.id);
		}
		persistir();
	}

	function aoPular(id) {
		const q = sessao[i];
		respostas[i] = { id, pulada: true };
		registrar(i, {
			id,
			materia: q?.materia || '?',
			certa: false,
			parcial: false,
			anulada: false,
			pulada: true
		});
		avancar();
	}

	// Bucket próprio: "marcar para rever" e "errar" são fatos diferentes — ver
	// o mesmo comentário em `treino/+page.svelte`.
	function aoRevisar(id, marcado) {
		// reaproveita a lista de erros do stats, que alimenta o modo "Revisar erros"
		if (marcado) marcarRevisar(id);
		else desmarcarRevisar(id);
	}

	function avancar() {
		xpPing = 0;
		direcao = 1;
		topo();
		if (ultima) {
			fim = true;
			limparSessao(); // sessão terminou: não há mais o que retomar
			registrarSessao({
				modo: 'estudo',
				nivel,
				respondidas: feitas,
				certas,
				duracaoMs: Date.now() - inicio
			});
			return;
		}
		i++;
		persistir();
	}

	function voltar() {
		if (i === 0) return;
		xpPing = 0;
		direcao = -1;
		topo();
		i--;
		persistir();
	}

	function sair() {
		// antes descartava 10 questões em silêncio; agora salva e avisa
		if (feitas === 0) {
			nivel = null;
			// só pulou: a sessão pode ter sido gravada mesmo assim
			oferecerContinuar();
			return;
		}
		confirmaSaida = true;
	}

	function sairAgora() {
		persistir();
		confirmaSaida = false;
		nivel = null;
		oferecerContinuar();
	}

	function continuar() {
		if (!salvaE) return;
		direcao = 0;
		nivel = salvaE.nivel;
		materiaFiltro = materiaExiste(salvaE.materia) ? salvaE.materia : 'todas';
		sessao = salvaE.sessao;
		i = Math.min(salvaE.i ?? 0, sessao.length - 1);
		respostas = Array.isArray(salvaE.respostas) ? salvaE.respostas : [];
		log = salvaE.log || [];
		inicio = salvaE.inicio || Date.now();
		xpGanho = salvaE.xpGanho || 0;
		fim = false;
		xpPing = 0;
		escolhaE = false;
	}

	function descartar() {
		limparSessao();
		escolhaE = false;
		salvaE = null;
		nivel = null;
	}

	function persistir() {
		// não salva sessão vazia (evita oferecer "continuar" de 0 respostas)
		if (!sessao.length || fim || !log.length) return;
		try {
			localStorage.setItem(
				CHAVE,
				JSON.stringify({
					v: 2,
					nivel,
					materia: materiaFiltro,
					i,
					respostas,
					log,
					inicio,
					xpGanho,
					ids: sessao.map((q) => q.id)
				})
			);
		} catch {
			// armazenamento bloqueado/cheio — segue sem salvar
		}
	}

	function lerSessao() {
		try {
			const v = localStorage.getItem(CHAVE);
			return v ? JSON.parse(v) : null;
		} catch {
			return null;
		}
	}

	function limparSessao() {
		try {
			localStorage.removeItem(CHAVE);
		} catch {
			// ignora
		}
	}

	function ehCampo(t) {
		return (
			t instanceof HTMLElement &&
			(t.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(t.tagName))
		);
	}

	function aoTecla(e) {
		if (e.metaKey || e.ctrlKey || e.altKey) return;
		if (ehCampo(e.target)) return;
		if (e.key === 'Escape') {
			if (confirmaSaida) {
				confirmaSaida = false;
				return;
			}
			if (zoomAberto) return; // deixa o Esc fechar o zoom da figura
			if (nivel !== null && !fim) sair();
			return;
		}
		if (confirmaSaida || nivel === null || fim || escolhaE || zoomAberto) return;
		if (e.key === 'ArrowLeft') {
			e.preventDefault();
			voltar();
			return;
		}
		if (e.key === 'ArrowRight' || e.key === 'Enter') {
			// com foco num botão/link, deixa a ativação nativa cuidar (evita avançar 2x)
			if (e.key === 'Enter' && e.target instanceof HTMLElement && ['BUTTON', 'A'].includes(e.target.tagName))
				return;
			if (!podeAvancar) return;
			e.preventDefault();
			avancar();
		}
	}

	function mmss() {
		const s = Math.floor((Date.now() - inicio) / 1000);
		return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;
	}

	function porMateria() {
		const mapa = new Map();
		for (const r of log) {
			if (r.pulada || !r.materia) continue;
			if (!mapa.has(r.materia)) mapa.set(r.materia, { n: 0, ok: 0 });
			const m = mapa.get(r.materia);
			m.n++;
			if (r.certa) m.ok++;
		}
		return [...mapa.entries()].sort((a, b) => b[1].n - a[1].n).slice(0, 3);
	}

	function bolinha(k) {
		if (k === i) return 'bg-accent';
		const r = respostas[k];
		if (r?.pulada) return 'bg-track';
		if (r?.certa) return 'bg-ok-solid';
		if (r) return 'bg-bad-solid';
		return 'bg-line';
	}
</script>

<svelte:window onkeydown={aoTecla} />

<div class="mx-auto w-full max-w-3xl" style="padding-bottom: calc(1rem + env(safe-area-inset-bottom));">
{#if !carregou}
	<div class="space-y-3" role="status" aria-label="Carregando questões">
		<div class="h-40 animate-pulse rounded-3xl bg-skel"></div>
		<div class="h-14 animate-pulse rounded-2xl bg-skel"></div>
		<div class="h-14 animate-pulse rounded-2xl bg-skel"></div>
	</div>
{:else if falhou || !banco.length}
	<div class="rounded-3xl bg-card p-6 text-center shadow-sm" role="alert">
		<p class="font-display text-lg font-bold">Não deu para carregar as questões</p>
		<p class="mt-1 text-sm text-ink-soft">Verifique sua conexão e tente de novo.</p>
		<button type="button" onclick={() => location.reload()} class="btn3d duo-accent mt-4 w-full rounded-2xl p-3.5 font-bold">
			Tentar de novo
		</button>
	</div>
{:else if sessaoGuardada}
	<!-- sem a escolha de nível: começar uma sessão nova apagaria a guardada -->
	<div class="rounded-3xl bg-card p-6 text-center shadow-sm" role="alert">
		<p class="font-display text-lg font-bold">Parte das questões não carregou</p>
		<p class="mt-1 text-sm text-ink-soft">
			Sua sessão de estudo pausada continua guardada neste aparelho. Verifique a conexão e tente de novo para continuar.
		</p>
		<button type="button" onclick={() => location.reload()} class="btn3d duo-accent mt-4 w-full rounded-2xl p-3.5 font-bold">
			Tentar de novo
		</button>
	</div>
{:else if escolhaE && salvaE}
	<div class="rise rounded-3xl bg-card p-6 text-center shadow-[0_10px_30px_-12px_rgba(20,33,61,0.25)]">
		<p class="font-code text-[11px] font-bold tracking-[0.14em] text-ink-soft uppercase">Sessão de estudo pausada</p>
		<h2 class="mt-1 font-display text-2xl font-extrabold tracking-tight">Continuar de onde parou?</h2>
		<p class="nums mt-2 text-sm text-ink-soft">
			{NIVEIS[salvaE.nivel]?.nome ?? 'Sessão'}{materiaExiste(salvaE.materia) ? ` · ${nomeMateria(salvaE.materia)}` : ''} · questão {salvaE.i + 1} de {salvaE.sessao.length} · {salvaECertas}/{salvaEfeitas} certas
		</p>
		{#if salvaE.removidas}
			<p class="nums mt-1 text-xs font-semibold text-ink-soft">
				{salvaE.removidas} {salvaE.removidas === 1 ? 'questão saiu' : 'questões saíram'} do banco desde a pausa.
			</p>
		{/if}
		<button type="button" onclick={continuar} class="btn3d duo-accent mt-4 flex w-full items-center justify-center gap-2 rounded-[14px] p-3.5 font-display text-lg font-bold">
			<Play size={20} weight="fill" aria-hidden="true" /> Continuar sessão
		</button>
		<button type="button" onclick={descartar} class="mt-2 w-full rounded-[14px] border-2 border-line bg-card p-3.5 font-display text-lg font-bold">
			Começar outra
		</button>
	</div>
{:else if nivel === null}
	<div class="mb-4">
		<h1 class="font-display text-2xl font-extrabold tracking-tight">Sessão de estudo</h1>
		<p class="mt-1 text-sm text-ink-soft">Até 10 questões por sessão. Escolha a matéria e o nível.</p>
	</div>
	<label class="mb-4 flex items-center gap-2 rounded-2xl border border-line bg-card px-3">
		<Tag size={17} weight="bold" class="shrink-0 text-ink-soft" aria-hidden="true" />
		<span class="sr-only">Filtrar por matéria</span>
		<select
			bind:value={materiaFiltro}
			onchange={() => (vazioNivel = null)}
			class="w-full bg-transparent py-3 text-sm font-semibold text-ink"
		>
			<option value="todas">Todas as matérias</option>
			{#each gruposFiltro as g (g.rotulo)}
				<optgroup label={g.rotulo}>
					{#each g.materias as m (m.id)}
						<option value={m.id}>{m.nome}</option>
					{/each}
				</optgroup>
			{/each}
		</select>
	</label>
	{#if vazioNivel}
		<div class="mb-3 flex items-start gap-2 rounded-2xl bg-warn-bg p-3 text-sm font-semibold text-warn-fg" role="alert">
			<Info size={18} weight="bold" class="mt-0.5 shrink-0" aria-hidden="true" />
			<span>
				{NIVEIS[vazioNivel].nome} ainda não tem questões{materiaFiltro !== 'todas' ? ` de ${nomeMateria(materiaFiltro)}` : ''}.
				Tente outro nível, outra matéria ou o
				<a href="/treino/" class="font-bold underline">treino livre</a>.
			</span>
		</div>
	{/if}
	<p class="mb-2 font-code text-[11px] font-bold tracking-[0.14em] text-ink-soft uppercase">Revisão por nível</p>
	<div class="space-y-3">
		{#each ESCADA as n, k (n)}
			<button
				type="button"
				onclick={() => comecar(n)}
				class="rise flex w-full items-center gap-4 rounded-3xl bg-card p-5 text-left shadow-[0_10px_30px_-12px_rgba(20,33,61,0.25)] transition-transform hover:-translate-y-0.5 active:scale-[0.99]"
				style="animation-delay: {k * 70}ms"
			>
				<span class="nums flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-bar font-display text-xl font-extrabold text-white" aria-hidden="true">
					{n}
				</span>
				<span class="min-w-0 flex-1">
					<span class="block font-display text-[17px] font-bold tracking-tight">{NIVEIS[n].nome}</span>
					<span class="block text-sm text-ink-soft">{NIVEIS[n].desc}</span>
					<span class="nums block text-xs font-semibold text-ink-soft">{contagens[n]} {contagens[n] === 1 ? 'questão' : 'questões'} disponíveis</span>
				</span>
				<span class="flex shrink-0 gap-1" aria-hidden="true">
					{#each ESCADA as d (d)}
						<span class="h-2 w-2 rounded-full {d <= n ? 'bg-accent' : 'bg-track'}"></span>
					{/each}
				</span>
			</button>
		{/each}
	</div>
	<p class="mt-6 mb-2 font-code text-[11px] font-bold tracking-[0.14em] text-ink-soft uppercase">Prova oficial</p>
	<button
		type="button"
		onclick={() => comecar(NIVEL_ENADE)}
		class="rise flex w-full items-center gap-4 rounded-3xl bg-card p-5 text-left shadow-[0_10px_30px_-12px_rgba(20,33,61,0.25)] transition-transform hover:-translate-y-0.5 active:scale-[0.99]"
		style="animation-delay: 210ms"
	>
		<span class="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-accent-soft" aria-hidden="true">
			<SealCheck size={26} weight="bold" class="text-accent-ink" />
		</span>
		<span class="min-w-0 flex-1">
			<span class="block font-display text-[17px] font-bold tracking-tight">{NIVEIS[NIVEL_ENADE].nome}</span>
			<span class="block text-sm text-ink-soft">{NIVEIS[NIVEL_ENADE].desc}</span>
			<span class="nums block text-xs font-semibold text-ink-soft">{contagens[NIVEL_ENADE]} {contagens[NIVEL_ENADE] === 1 ? 'questão' : 'questões'} disponíveis</span>
		</span>
	</button>
{:else if fim}
	<div class="blueprint -mx-4 -mt-6 bg-bar px-4 pt-8 pb-10 text-center text-white" style="border-radius: 0 0 26px 26px;">
		<p class="text-sm font-medium text-bar-fg">Estudo · {NIVEIS[nivel].nome}{materiaFiltro !== 'todas' ? ` · ${nomeMateria(materiaFiltro)}` : ''}</p>
		<h2 class="mt-1 font-display text-3xl font-extrabold tracking-tight">Sessão concluída</h2>
		<p class="springin mx-auto mt-4 flex h-24 w-24 items-center justify-center rounded-full bg-accent-soft">
			<Trophy size={44} weight="fill" class="text-accent" aria-hidden="true" />
		</p>
		<p class="nums mt-3 font-display text-6xl font-extrabold tracking-tight">
			<Contador valor={certas} />/{sessao.length}
		</p>
		<p class="mt-1 text-sm text-bar-fg">acertos nesta sessão</p>
		{#if parciais > 0}
			<p class="nums mt-1 text-xs font-semibold text-bar-fg">{parciais} {parciais === 1 ? 'parcial' : 'parciais'} · meio ponto</p>
		{/if}
	</div>
	<div class="mx-auto -mt-0 grid max-w-xs grid-cols-3 gap-2 pt-4 text-center">
		<div class="rounded-2xl bg-card p-3 shadow-sm">
			<p class="nums flex items-center justify-center gap-1 text-xl font-extrabold"><Target size={17} weight="bold" class="text-accent" aria-hidden="true" />{feitas ? Math.round((certas / feitas) * 100) : 0}%</p>
			<p class="text-[11px] font-semibold text-ink-soft">Precisão</p>
		</div>
		<div class="rounded-2xl bg-card p-3 shadow-sm">
			<p class="nums flex items-center justify-center gap-1 text-xl font-extrabold"><Timer size={17} weight="bold" class="text-accent" aria-hidden="true" />{mmss()}</p>
			<p class="text-[11px] font-semibold text-ink-soft">Tempo</p>
		</div>
		<div class="rounded-2xl bg-card p-3 shadow-sm">
			<p class="nums flex items-center justify-center gap-1 text-xl font-extrabold"><Lightning size={17} weight="fill" class="text-accent" aria-hidden="true" />+{xpGanho}</p>
			<p class="text-[11px] font-semibold text-ink-soft">XP ganho</p>
		</div>
	</div>
	{#if porMateria().length}
		<div class="mt-3 rounded-3xl bg-card p-5 shadow-sm">
			<p class="font-display text-lg font-bold">Desempenho por matéria</p>
			<div class="mt-3 space-y-3">
				{#each porMateria() as [m, d] (m)}
					<div>
						<div class="flex items-baseline justify-between gap-3 text-sm">
							<p class="truncate font-semibold">{nomeMateria(m)}</p>
							<p class="nums shrink-0 font-bold">{d.ok}/{d.n}</p>
						</div>
						<div class="mt-1 h-2 overflow-hidden rounded-full bg-track">
							<div class="h-full rounded-full bg-accent" style="width: {(d.ok / d.n) * 100}%"></div>
						</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}
	<div class="mt-4 space-y-2">
		<button type="button" onclick={() => (nivel = null)} class="btn3d duo-accent flex w-full items-center justify-center gap-2 rounded-[14px] p-3.5 font-display text-lg font-bold">
			<ArrowsClockwise size={20} weight="bold" aria-hidden="true" /> Outra sessão
		</button>
		{#if contarParaRevisar(banco)}
			<a href="/treino/?modo=revisao" class="flex w-full items-center justify-center rounded-[14px] border-2 border-line bg-card p-3.5 font-display text-lg font-bold">
				Revisar erros e marcadas ({contarParaRevisar(banco)})
			</a>
		{/if}
	</div>
{:else}
	<SessaoTopo
		titulo={`Questão ${i + 1} de ${sessao.length}`}
		detalhe={NIVEIS[nivel].nome}
		progresso={sessao.length ? (i + 1) / sessao.length : 0}
		{xp}
		aoFechar={sair}
	/>
	{#if sessao.length < TOTAL}
		<p class="mt-4 flex items-start gap-2 rounded-2xl bg-warn-bg p-3 text-xs font-semibold text-warn-fg" role="status">
			<Info size={16} weight="bold" class="mt-0.5 shrink-0" aria-hidden="true" />
			<span>Só há {sessao.length} {sessao.length === 1 ? 'questão' : 'questões'} neste nível{materiaFiltro !== 'todas' ? ' nesta matéria' : ''} — a sessão é mais curta que o normal.</span>
		</p>
	{/if}
	<div class="mt-4">
		{#if sessao[i]}
			<DicaGestos
				id="questoes"
				texto="Deslize a questão para os lados para passar ou voltar. Da borda da tela para o meio, você volta à tela anterior."
			/>
			<!-- na última questão o gesto NÃO encerra (registrarSessao é
			     irreversível): só cede, e o caminho é o "Ver resultado" -->
			<div
				{@attach deslizarQuestoes(() => ({
					anterior: i > 0,
					proxima: podeAvancar && !ultima,
					onAnterior: voltar,
					onProxima: avancar
				}))}
			>
				{#key sessao[i].id + '-' + i}
					<div in:fly={{ x: 32 * direcao, duration: direcao ? DUR : 0 }}>
						<Questao
							q={sessao[i]}
							onResponder={aoResponder}
							onPular={aoPular}
							onRevisar={aoRevisar}
							revisarInicial={getRevisar().includes(sessao[i].id)}
							inicial={respostas[i]?.pulada ? null : (respostas[i] ?? null)}
							bind:zoomAberto
						/>
					</div>
				{/key}
			</div>
			<BarraAcao
				rotulo={ultima ? 'Ver resultado' : 'Próxima'}
				mostrarXP={xpPing > 0}
				xpValor={xpValor}
				desabilitado={!podeAvancar}
				aviso="Responda (ou pule) para continuar."
				onClick={avancar}
			>
				<nav class="flex items-center gap-2" aria-label="Navegação da sessão">
					<button
						type="button"
						onclick={voltar}
						disabled={i === 0}
						aria-label="Questão anterior"
						class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-line bg-card text-ink transition-transform active:scale-95 disabled:opacity-40"
					>
						<ArrowLeft size={20} weight="bold" aria-hidden="true" />
					</button>
					<p class="nums flex-1 text-center text-sm font-bold text-ink-soft" role="status" aria-live="polite">
						Questão {i + 1} de {sessao.length}
					</p>
					<span class="h-11 w-11 shrink-0" aria-hidden="true"></span>
				</nav>
				{#if sessao.length <= 12}
					<div class="mt-1.5 flex justify-center gap-1" aria-hidden="true">
						{#each sessao as _q, k (k)}
							<span class="h-1.5 w-2.5 rounded-full {bolinha(k)}"></span>
						{/each}
					</div>
				{/if}
			</BarraAcao>
		{/if}
	</div>
{/if}

	{#if confirmaSaida}
		<div class="fixed inset-0 z-50 flex items-end justify-center p-4 sm:items-center">
			<button
				type="button"
				onclick={() => (confirmaSaida = false)}
				aria-label="Fechar e continuar estudando"
				class="absolute inset-0 cursor-default bg-black/50"
			></button>
			<div
				role="dialog"
				aria-modal="true"
				aria-labelledby="estudo-saida-titulo"
				class="relative w-full max-w-sm rounded-3xl bg-card p-5 shadow"
			>
				<h2 id="estudo-saida-titulo" class="font-display text-xl font-extrabold tracking-tight">Sair da sessão?</h2>
				<p class="mt-1 text-sm text-ink-soft">
					Seu progresso ({feitas} respondidas) fica salvo para continuar depois.
				</p>
				<div class="mt-4 space-y-2">
					<button
						type="button"
						bind:this={refSaida}
						onclick={sairAgora}
						class="btn3d duo-accent w-full rounded-[14px] p-3.5 font-display text-base font-bold"
					>
						Sair e salvar
					</button>
					<button
						type="button"
						onclick={() => (confirmaSaida = false)}
						class="w-full rounded-[14px] border-2 border-line bg-card p-3 font-display text-base font-bold"
					>
						Continuar estudando
					</button>
				</div>
			</div>
		</div>
	{/if}
</div>
