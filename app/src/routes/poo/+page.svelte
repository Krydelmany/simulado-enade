<script>
	// Questionário diário de POO, passado pelo professor em 28/10/2026.
	// É um teste fechado: 10 questões na ordem do PDF, correção na hora e
	// resultado no fim. O gabarito é preliminar (a Q5 foi conferida no ENADE
	// 2011; as demais foram resolvidas) — a tela avisa e o professor confirma.
	import { onMount } from 'svelte';
	import {
		ArrowLeft,
		ArrowRight,
		ArrowSquareOut,
		CheckCircle,
		XCircle
	} from 'phosphor-svelte';
	import { foco } from '$lib/foco.svelte.js';
	import TextoRico from '$lib/TextoRico.svelte';

	const LETRAS = ['A', 'B', 'C', 'D', 'E'];

	let dados = $state(null);
	let questoes = $state([]);
	let carregando = $state(true);
	let erro = $state('');
	let comecou = $state(false);
	let i = $state(0);
	let escolha = $state(null);
	let respostas = $state([]);
	let fim = $state(false);

	let atual = $derived(questoes[i] ?? null);
	let ultima = $derived(i + 1 >= questoes.length);
	let certas = $derived(respostas.filter((r) => r?.certa).length);
	let respondidas = $derived(respostas.filter(Boolean).length);
	let acertou = $derived(!!atual && !!escolha && escolha === atual.gabarito);

	// O layout esconde a tab bar do celular e reserva o pb-32 enquanto o quiz
	// está em andamento (regra 14 do AGENTS).
	$effect(() => {
		foco.quiz = comecou && !fim;
		return () => {
			foco.quiz = false;
		};
	});

	function valida(q) {
		return (
			q &&
			q.id &&
			q.tema &&
			q.enunciado &&
			['A', 'B', 'C', 'D', 'E'].every(
				(l) => typeof q.alternativas?.[l] === 'string' && q.alternativas[l].trim()
			) &&
			['A', 'B', 'C', 'D', 'E'].includes(q.gabarito)
		);
	}

	onMount(async () => {
		try {
			const r = await fetch('/banco/poo-2026-10-28.json');
			if (!r.ok) throw new Error('Não deu para carregar o questionário.');
			const d = await r.json();
			const qs = Array.isArray(d.questoes) ? d.questoes : [];
			if (!qs.length || !qs.every(valida)) throw new Error('O questionário está incompleto.');
			dados = d;
			questoes = qs;
		} catch (e) {
			erro = e.message;
		} finally {
			carregando = false;
		}
	});

	function dia(iso) {
		const d = new Date(`${String(iso).slice(0, 10)}T12:00:00`);
		return Number.isNaN(d.getTime()) ? '' : d.toLocaleDateString('pt-BR');
	}

	function comecar() {
		comecou = true;
		fim = false;
		i = 0;
		escolha = null;
		respostas = [];
		window.scrollTo({ top: 0 });
	}

	function responder(letra) {
		if (escolha || !atual) return;
		escolha = letra;
		const novas = [...respostas];
		novas[i] = { escolha: letra, certa: letra === atual.gabarito };
		respostas = novas;
	}

	function avancar() {
		if (!escolha) return;
		if (ultima) {
			fim = true;
			window.scrollTo({ top: 0 });
			return;
		}
		i += 1;
		escolha = null;
		window.scrollTo({ top: 0 });
	}

	function refazer() {
		comecou = true;
		fim = false;
		i = 0;
		escolha = null;
		respostas = [];
		window.scrollTo({ top: 0 });
	}
</script>

<svelte:head>
	<title>POO · questionário do professor · Simulado ENADE</title>
</svelte:head>

{#if carregando}
	<div class="space-y-3" role="status" aria-label="Carregando o questionário">
		<div class="h-48 animate-pulse rounded-3xl bg-skel"></div>
		<div class="h-24 animate-pulse rounded-3xl bg-skel"></div>
	</div>
{:else if erro}
	<section class="rounded-3xl border border-line bg-card p-5 sm:p-6" role="alert">
		<h1 class="font-display text-title font-extrabold">Questionário POO</h1>
		<p class="mt-2 text-[15px] leading-relaxed text-pretty text-ink-soft">{erro}</p>
		<a href="/" class="mt-4 inline-flex min-h-11 items-center gap-2 font-bold text-accent-ink">
			Voltar ao início <ArrowRight size={17} weight="bold" aria-hidden="true" />
		</a>
	</section>
{:else if fim}
	<section class="blueprint faixa px-4 pt-7 pb-8 text-white sm:p-8">
		<p class="text-sm font-semibold text-bar-fg">POO · questionário do professor</p>
		<h1 class="mt-1 font-display text-3xl font-extrabold tracking-tight">Resultado</h1>
		<p class="nums mt-4 font-display text-6xl leading-none font-black tracking-tight">
			{certas}<span class="text-2xl font-bold text-bar-fg">/{questoes.length}</span>
		</p>
		<p class="mt-2 text-sm font-semibold text-bar-fg">
			{questoes.length ? Math.round((certas / questoes.length) * 100) : 0}% de acerto
			{#if respondidas < questoes.length}· {questoes.length - respondidas} em branco{/if}
		</p>
		<p class="mt-3 text-xs text-bar-fg">{dados?.nota}</p>
	</section>

	<section class="mt-4 space-y-2" aria-label="Correção das questões">
		{#each questoes as q, k (q.id)}
			{@const r = respostas[k]}
			<div class="flex items-start gap-3 rounded-2xl border border-line bg-card p-3">
				{#if r?.certa}
					<CheckCircle size={20} weight="bold" class="mt-0.5 shrink-0 text-ok-fg" aria-hidden="true" />
				{:else}
					<XCircle size={20} weight="bold" class="mt-0.5 shrink-0 text-bad-fg" aria-hidden="true" />
				{/if}
				<div class="min-w-0 flex-1">
					<p class="text-sm font-bold text-pretty">{k + 1}. {q.tema}</p>
					<p class="mt-0.5 text-xs text-ink-soft">
						Sua resposta: <strong>{r?.escolha ?? '—'}</strong> · Correta: <strong>{q.gabarito}</strong>
					</p>
				</div>
			</div>
		{/each}
	</section>

	<div class="mt-4 flex flex-col gap-2 sm:flex-row">
		<button
			type="button"
			onclick={refazer}
			class="btn3d duo-accent flex min-h-[52px] flex-1 items-center justify-center rounded-[14px] px-6 font-display text-base font-bold"
		>
			Refazer o questionário
		</button>
		<a
			href="/"
			class="flex min-h-[52px] flex-1 items-center justify-center rounded-[14px] border-2 border-line px-6 font-display text-base font-bold"
		>
			Voltar ao início
		</a>
	</div>
	<p class="mt-3 text-xs leading-relaxed text-pretty text-ink-soft">
		{dados?.fonte} {dados?.nota}
	</p>
{:else if !comecou}
	<section class="blueprint faixa px-4 pt-7 pb-8 text-white sm:p-8">
		<a href="/" class="inline-flex min-h-11 items-center gap-2 text-sm font-bold text-bar-fg hover:text-white">
			<ArrowLeft size={17} weight="bold" aria-hidden="true" /> Início
		</a>
		<div class="mt-3 flex flex-wrap items-center gap-2">
			<span class="rounded-full bg-accent px-2.5 py-1 text-xs font-extrabold text-white">Novo</span>
			<span class="text-xs font-semibold text-bar-fg">Lançado hoje · {dia(dados?.lancado_em)}</span>
		</div>
		<h1 class="mt-2 font-display text-3xl font-extrabold tracking-tight text-pretty">{dados?.titulo}</h1>
		<p class="mt-2 max-w-[46ch] text-sm leading-relaxed text-pretty text-bar-fg">
			{questoes.length} questões que o professor passou hoje, na ordem do questionário. Sem cronômetro;
			a correção aparece depois de cada resposta.
		</p>
		<p class="mt-2 text-xs text-bar-fg">{dados?.fonte}</p>
		<button
			type="button"
			onclick={comecar}
			class="btn3d duo-accent mt-5 flex min-h-[52px] items-center justify-center gap-2 rounded-[14px] px-6 font-display text-base font-bold"
		>
			Começar <ArrowRight size={18} weight="bold" aria-hidden="true" />
		</button>
		<p class="mt-3 text-xs leading-relaxed text-pretty text-bar-fg">{dados?.nota}</p>
	</section>
{:else if atual}
	<div class="mx-auto max-w-2xl">
		<header class="flex items-center justify-between gap-3">
			<a href="/" class="inline-flex min-h-11 items-center gap-2 text-sm font-bold text-ink-soft hover:text-ink">
				<ArrowLeft size={17} weight="bold" aria-hidden="true" /> Sair
			</a>
			<p class="nums text-sm font-bold">{i + 1} de {questoes.length}</p>
		</header>
		<div class="mt-2 h-2 overflow-hidden rounded-full bg-track" aria-hidden="true">
			<div class="h-full rounded-full bg-accent-bar" style="width: {((i + 1) / questoes.length) * 100}%"></div>
		</div>

		<section class="mt-4 rounded-3xl border border-line bg-card p-4 sm:p-6" aria-labelledby="t-questao">
			<p class="text-label font-bold text-ink-soft">POO · questão {i + 1} de {questoes.length}</p>
			<h1 id="t-questao" class="mt-1 font-display text-title font-extrabold text-pretty">{atual.tema}</h1>
			<div class="mt-3 text-[15px] leading-relaxed text-pretty">
				<TextoRico texto={atual.enunciado} />
			</div>

			{#if atual.imagem}
				<figure class="mt-3 overflow-hidden rounded-2xl border border-line bg-white">
					<a href={atual.imagem.src} target="_blank" rel="noopener" class="block">
						<img
							src={atual.imagem.src}
							alt={atual.imagem.alt}
							loading="lazy"
							class="mx-auto h-auto max-h-[54vh] w-auto max-w-full"
						/>
					</a>
					<figcaption class="flex items-start gap-2 px-3 py-2 text-xs text-ink-soft">
						<ArrowSquareOut size={14} weight="bold" class="mt-0.5 shrink-0" aria-hidden="true" />
						<span>Abrir a figura em tamanho maior{#if atual.imagem.legenda} · {atual.imagem.legenda}{/if}</span>
					</figcaption>
				</figure>
			{/if}

			<div class="mt-4 space-y-2" role="group" aria-label="Alternativas">
				{#each LETRAS as letra (letra)}
					{@const marcada = escolha === letra}
					{@const correta = !!escolha && letra === atual.gabarito}
					{@const errada = !!escolha && marcada && letra !== atual.gabarito}
					<button
						type="button"
						disabled={!!escolha}
						onclick={() => responder(letra)}
						aria-pressed={marcada}
						class="flex min-h-11 w-full items-start gap-3 rounded-2xl border-2 px-3 py-3 text-left text-[15px] leading-relaxed transition-colors {correta
							? 'border-ok-fg/40 bg-ok-bg'
							: errada
								? 'border-bad-fg/40 bg-bad-bg'
								: marcada
									? 'border-accent bg-accent-soft'
									: 'border-line bg-card hover:border-accent'}"
					>
						<span
							class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-line font-display text-sm font-extrabold {correta
								? 'bg-ok-fg text-white'
								: errada
									? 'bg-bad-fg text-white'
									: marcada
										? 'bg-accent text-white'
										: 'bg-tile text-ink-soft'}"
						>
							{letra}
						</span>
						<span class="min-w-0 flex-1 text-pretty">{atual.alternativas[letra]}</span>
						{#if correta}
							<CheckCircle size={20} weight="bold" class="mt-0.5 shrink-0 text-ok-fg" aria-hidden="true" />
						{:else if errada}
							<XCircle size={20} weight="bold" class="mt-0.5 shrink-0 text-bad-fg" aria-hidden="true" />
						{/if}
					</button>
				{/each}
			</div>

			{#if escolha}
				<p
					role="status"
					class="mt-3 rounded-2xl p-3 text-sm font-semibold {acertou ? 'bg-ok-bg text-ok-fg' : 'bg-bad-bg text-bad-fg'}"
				>
					{acertou ? 'Resposta correta.' : `Resposta incorreta. A correta é ${atual.gabarito}.`}
				</p>
			{/if}

			<button
				type="button"
				onclick={avancar}
				disabled={!escolha}
				class="btn3d duo-accent mt-4 flex min-h-[52px] w-full items-center justify-center gap-2 rounded-[14px] px-6 font-display text-base font-bold disabled:opacity-50"
			>
				{ultima ? 'Ver resultado' : 'Próxima'} <ArrowRight size={18} weight="bold" aria-hidden="true" />
			</button>
			<p class="mt-2 text-xs text-ink-soft">
				{respondidas} de {questoes.length} respondidas · gabarito preliminar
			</p>
		</section>
	</div>
{/if}
