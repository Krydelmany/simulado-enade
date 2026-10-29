<script>
	// Questionário diário de POO, passado pelo professor em 28/10/2026.
	// MODO PROVA: marcar não corrige; pode trocar e revisar; o gabarito só
	// aparece depois de "Entregar". A leitura é maior e mais espaçada de
	// propósito (TDAH/dislexia): uma tarefa por tela, sem cronômetro e sem
	// feedback imediato piscando.
	import { onMount } from 'svelte';
	import { fade, fly } from 'svelte/transition';
	import { ArrowLeft, ArrowRight, ArrowSquareOut, CheckCircle, XCircle } from 'phosphor-svelte';
	import { foco } from '$lib/foco.svelte.js';
	import { DUR } from '$lib/motion.js';
	import TextoRico from '$lib/TextoRico.svelte';

	const LETRAS = ['A', 'B', 'C', 'D', 'E'];

	let dados = $state(null);
	let questoes = $state([]);
	let carregando = $state(true);
	let erro = $state('');
	let comecou = $state(false);
	let revisando = $state(false);
	let i = $state(0);
	// uma letra (ou null) por questão; nada de "certa" até entregar
	let marcadas = $state([]);
	let fim = $state(false);

	let atual = $derived(questoes[i] ?? null);
	let ultima = $derived(i + 1 >= questoes.length);
	let marcada = $derived(atual ? (marcadas[i] ?? null) : null);
	let respondidas = $derived(marcadas.filter(Boolean).length);
	let emBranco = $derived(questoes.length - respondidas);
	let certas = $derived(
		questoes.reduce((n, q, k) => n + (marcadas[k] === q.gabarito ? 1 : 0), 0)
	);

	// O layout esconde a tab bar do celular e reserva o pb-32 enquanto o quiz
	// (ou a revisão) está em andamento (regra 14 do AGENTS).
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
		revisando = false;
		fim = false;
		i = 0;
		marcadas = Array(questoes.length).fill(null);
		window.scrollTo({ top: 0 });
	}

	function marcar(letra) {
		if (!atual) return;
		const novas = [...marcadas];
		// tocar de novo na mesma alternativa desmarca
		novas[i] = novas[i] === letra ? null : letra;
		marcadas = novas;
	}

	function ir(n) {
		i = Math.max(0, Math.min(questoes.length - 1, n));
		window.scrollTo({ top: 0 });
	}

	function anterior() {
		if (i > 0) ir(i - 1);
	}

	function proxima() {
		if (ultima) {
			revisando = true;
			window.scrollTo({ top: 0 });
			return;
		}
		ir(i + 1);
	}

	function editar(k) {
		i = k;
		revisando = false;
		window.scrollTo({ top: 0 });
	}

	function entregar() {
		fim = true;
		revisando = false;
		window.scrollTo({ top: 0 });
	}

	function refazer() {
		comecou = true;
		revisando = false;
		fim = false;
		i = 0;
		marcadas = Array(questoes.length).fill(null);
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
		<p class="springin nums mt-4 font-display text-6xl leading-none font-black tracking-tight">
			{certas}<span class="text-2xl font-bold text-bar-fg">/{questoes.length}</span>
		</p>
		<p class="mt-2 text-sm font-semibold text-bar-fg">
			{questoes.length ? Math.round((certas / questoes.length) * 100) : 0}% de acerto
			{#if emBranco > 0}· {emBranco} em branco{/if}
		</p>
		<p class="mt-3 text-xs text-bar-fg">{dados?.nota}</p>
	</section>

	<section class="mt-4 space-y-2" aria-label="Correção das questões">
		{#each questoes as q, k (q.id)}
			{@const resposta = marcadas[k]}
			<div class="flex items-start gap-3 rounded-2xl border border-line bg-card p-3">
				{#if resposta === q.gabarito}
					<CheckCircle size={20} weight="bold" class="mt-0.5 shrink-0 text-ok-fg" aria-hidden="true" />
				{:else}
					<XCircle size={20} weight="bold" class="mt-0.5 shrink-0 text-bad-fg" aria-hidden="true" />
				{/if}
				<div class="min-w-0 flex-1">
					<p class="text-sm font-bold text-pretty">{k + 1}. {q.tema}</p>
					<p class="mt-0.5 text-xs text-ink-soft">
						Sua resposta: <strong>{resposta ?? '—'}</strong> · Correta: <strong>{q.gabarito}</strong>
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
			{questoes.length} questões que o professor passou hoje. Responda no seu ritmo: sem cronômetro, e
			a correção aparece só no fim.
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
{:else if revisando}
	<div class="mx-auto max-w-2xl">
		<header class="flex items-center justify-between gap-3">
			<a href="/" class="inline-flex min-h-11 items-center gap-2 text-sm font-bold text-ink-soft hover:text-ink">
				<ArrowLeft size={17} weight="bold" aria-hidden="true" /> Sair
			</a>
			<p class="nums text-sm font-bold">{respondidas} de {questoes.length} respondidas</p>
		</header>

		<section class="mt-4 rounded-3xl border border-line bg-card p-4 sm:p-6" aria-labelledby="t-revisar">
			<h1 id="t-revisar" class="font-display text-title font-extrabold">Revisar respostas</h1>
			<p class="mt-2 text-[15px] leading-relaxed text-pretty text-ink-soft">
				Você ainda pode trocar qualquer resposta. A correção só aparece depois de entregar.
			</p>
			<ul class="mt-4 space-y-2">
				{#each questoes as q, k (q.id)}
					<li>
						<button
							type="button"
							onclick={() => editar(k)}
							class="flex min-h-12 w-full items-center gap-3 rounded-2xl border border-line bg-tile px-3 py-2 text-left transition-colors hover:border-accent"
						>
							<span class="nums w-6 shrink-0 text-center font-display text-sm font-black">{k + 1}</span>
							<span class="min-w-0 flex-1 text-sm font-semibold text-pretty">{q.tema}</span>
							<span class="nums w-7 shrink-0 text-center font-display text-lg font-extrabold {marcadas[k] ? 'text-accent-ink' : 'text-ink-soft'}">
								{marcadas[k] ?? '—'}
							</span>
							<span class="shrink-0 text-xs font-bold text-accent-ink">Trocar</span>
						</button>
					</li>
				{/each}
			</ul>
			{#if emBranco > 0}
				<p role="status" class="mt-3 rounded-2xl bg-warn-bg p-3 text-sm font-semibold text-warn-fg">
					{emBranco} {emBranco === 1 ? 'questão está em branco' : 'questões estão em branco'}. Toque nela para responder antes de entregar.
				</p>
			{/if}
			<button
				type="button"
				onclick={entregar}
				class="btn3d duo-accent mt-4 flex min-h-[52px] w-full items-center justify-center gap-2 rounded-[14px] px-6 font-display text-base font-bold"
			>
				Entregar e corrigir <ArrowRight size={18} weight="bold" aria-hidden="true" />
			</button>
			<button
				type="button"
				onclick={() => editar(questoes.length - 1)}
				class="mt-2 flex min-h-11 w-full items-center justify-center rounded-[14px] text-sm font-bold text-ink-soft hover:text-ink"
			>
				Voltar à última questão
			</button>
		</section>
	</div>
{:else if atual}
	<div class="mx-auto max-w-2xl">
		<header class="flex items-center justify-between gap-3">
			<a href="/" class="inline-flex min-h-11 items-center gap-2 text-sm font-bold text-ink-soft hover:text-ink">
				<ArrowLeft size={17} weight="bold" aria-hidden="true" /> Sair
			</a>
			<p class="nums text-sm font-bold">{i + 1} de {questoes.length}</p>
		</header>
		<div class="mt-2 h-2 overflow-hidden rounded-full bg-track" aria-hidden="true">
			<div class="h-full rounded-full bg-accent-bar transition-[width] duration-300" style="width: {((i + 1) / questoes.length) * 100}%"></div>
		</div>

		{#key atual.id}
			<div in:fly={{ y: 10, duration: DUR }} out:fade={{ duration: DUR }}>
				<section class="mt-4 rounded-3xl border border-line bg-card p-4 sm:p-6" aria-labelledby="t-questao">
			<h1 id="t-questao" class="font-display text-title font-extrabold text-pretty">{atual.tema}</h1>
			<div class="mt-3 max-w-[60ch] text-[17px] leading-8 text-pretty">
				<TextoRico texto={atual.enunciado} />
			</div>

			{#if atual.imagem}
				<figure class="mt-4 overflow-hidden rounded-2xl border border-line bg-white">
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

			<div class="mt-5 space-y-2.5" role="group" aria-label="Alternativas">
				{#each LETRAS as letra (letra)}
					{@const selecionada = marcada === letra}
					<button
						type="button"
						onclick={() => marcar(letra)}
						aria-pressed={selecionada}
						class="flex min-h-12 w-full items-start gap-3 rounded-2xl border-2 px-4 py-3.5 text-left text-[16px] leading-relaxed transition-colors {selecionada
							? 'border-accent bg-accent-soft'
							: 'border-line bg-card hover:border-accent'}"
					>
						<span
							class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-line font-display text-sm font-extrabold {selecionada
								? 'bg-accent text-white'
								: 'bg-tile text-ink-soft'}"
						>
							{letra}
						</span>
						<span class="min-w-0 flex-1 text-pretty">{atual.alternativas[letra]}</span>
					</button>
				{/each}
			</div>

			<p class="mt-3 text-sm leading-relaxed text-pretty text-ink-soft">
				A correção aparece só no fim. Você pode trocar a resposta ou voltar depois.
			</p>

			<div class="mt-4 flex flex-col gap-2 sm:flex-row">
				<button
					type="button"
					onclick={anterior}
					disabled={i === 0}
					class="min-h-[52px] rounded-[14px] border-2 border-line px-5 font-display text-base font-bold transition-transform active:scale-[0.98] disabled:opacity-40"
				>
					Anterior
				</button>
				<button
					type="button"
					onclick={proxima}
					class="btn3d duo-accent flex min-h-[52px] flex-1 items-center justify-center gap-2 rounded-[14px] px-6 font-display text-base font-bold transition-transform active:scale-[0.99]"
				>
					{ultima ? 'Revisar e entregar' : 'Próxima'} <ArrowRight size={18} weight="bold" aria-hidden="true" />
				</button>
			</div>
			<p class="mt-2 text-xs text-ink-soft" aria-live="polite">
				{respondidas} de {questoes.length} respondidas · sem cronômetro
			</p>
				</section>
			</div>
		{/key}
	</div>
{/if}
