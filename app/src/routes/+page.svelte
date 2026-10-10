<script>
	import { onMount } from 'svelte';
	import { carregarBanco } from '$lib/banco.js';
	import { getXP, getStreak } from '$lib/stats.js';
	import {
		ArrowRight,
		Database,
		Flame,
		Infinity as InfinityIcon,
		Lightning,
		Notebook,
		Timer
	} from 'phosphor-svelte';

	let total = $state(0);
	let xp = $state(0);
	let dias = $state(0);
	let pronto = $state(false);

	const modos = [
		{
			href: '/treino/',
			icone: InfinityIcon,
			titulo: 'Treino livre',
			desc: 'Fila contínua sem total fixo. Para quando quiser e vê o resumo.'
		},
		{
			href: '/estudo/',
			icone: Notebook,
			titulo: 'Estudo · 10 questões',
			desc: 'Sessão curta com níveis: fundamentos, intermediário e avançado.'
		},
		{
			href: '/simulado/',
			icone: Timer,
			titulo: 'Simulado real',
			desc: 'O formato da prova: 46 questões em 4 horas, peso oficial.'
		}
	];

	onMount(async () => {
		total = (await carregarBanco()).length;
		xp = getXP();
		dias = getStreak().dias;
		pronto = true;
	});
</script>

<section class="dotgrid -mx-4 -mt-6 px-4 pt-10 pb-8">
	<p class="rise inline-flex items-center gap-2 rounded-full border border-line bg-card/80 px-3 py-1 text-xs font-bold tracking-wide text-ink-soft">
		ENADE 2026 · ENGENHARIA DE COMPUTAÇÃO
	</p>
	<h1
		class="rise mt-3 max-w-[16ch] text-4xl font-extrabold tracking-tight text-balance sm:text-5xl"
		style="animation-delay: 60ms"
	>
		Treine no formato da prova.
	</h1>
	<p class="rise mt-3 max-w-[52ch] text-[15px] leading-relaxed text-ink-soft" style="animation-delay: 120ms">
		Questões oficiais do INEP com correção na hora. Escolha um modo e comece.
	</p>
	<dl class="rise mt-5 flex flex-wrap gap-x-6 gap-y-2 text-sm font-semibold" style="animation-delay: 180ms">
		{#if !pronto}
			<div class="flex gap-4" role="status" aria-label="Carregando estatísticas">
				<div class="h-5 w-20 animate-pulse rounded-full bg-skel"></div>
				<div class="h-5 w-24 animate-pulse rounded-full bg-skel"></div>
				<div class="h-5 w-24 animate-pulse rounded-full bg-skel"></div>
			</div>
		{:else}
			<div class="flex items-center gap-1.5">
				<Lightning size={17} weight="bold" class="text-accent" aria-hidden="true" />
				<dt class="sr-only">XP</dt>
				<dd class="nums">{xp} XP</dd>
			</div>
			<div class="flex items-center gap-1.5">
				<Flame size={17} weight="bold" class={dias > 0 ? 'flame-on text-accent' : 'text-ink-soft opacity-50'} aria-hidden="true" />
				<dt class="sr-only">Dias seguidos</dt>
				<dd class="nums">{dias} {dias === 1 ? 'dia seguido' : 'dias seguidos'}</dd>
			</div>
			<div class="flex items-center gap-1.5">
				<Database size={17} weight="bold" class="text-accent" aria-hidden="true" />
				<dt class="sr-only">Questões no banco</dt>
				<dd class="nums">{total} questões</dd>
			</div>
		{/if}
	</dl>
</section>

<nav class="divide-y divide-line border-y border-line" aria-label="Modos de estudo">
	{#each modos as m, k (m.href)}
		<a
			href={m.href}
			class="rise group flex items-center gap-4 bg-card/70 py-4 transition-colors hover:bg-card active:bg-accent-soft"
			style="animation-delay: {220 + k * 70}ms"
		>
			<span class="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-bar" aria-hidden="true">
				<m.icone size={24} weight="bold" color="#fff" aria-hidden="true" />
			</span>
			<span class="min-w-0 flex-1">
				<span class="block text-[17px] font-bold tracking-tight">{m.titulo}</span>
				<span class="block truncate text-sm text-ink-soft sm:whitespace-normal">{m.desc}</span>
			</span>
			<ArrowRight
				size={20}
				weight="bold"
				aria-hidden="true"
				class="shrink-0 text-ink-soft opacity-60 transition-transform group-hover:translate-x-1 group-hover:text-accent group-hover:opacity-100"
			/>
		</a>
	{/each}
</nav>

<p class="mt-5 text-sm leading-relaxed text-ink-soft">
	Formação Geral e Componente Específico, objetivas com gabarito oficial e discursivas com
	padrão de resposta para autoavaliação.
</p>
