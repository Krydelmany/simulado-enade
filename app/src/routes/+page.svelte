<script>
	import { onMount } from 'svelte';
	import { carregarBanco } from '$lib/banco.js';
	import { getXP } from '$lib/stats.js';
	import {
		CaretRight,
		Database,
		Infinity as InfinityIcon,
		Lightning,
		LockSimple,
		Stairs,
		Timer
	} from 'phosphor-svelte';

	const META = 160;
	let total = $state(0);
	let fg = $state(0);
	let ce = $state(0);
	let disc = $state(0);
	let edicoes = $state([]);
	let xp = $state(0);
	let pronto = $state(false);

	const modos = [
		{
			href: '/treino/',
			icone: InfinityIcon,
			titulo: 'Treino livre',
			desc: 'Fila contínua de questões',
			bloqueado: false
		},
		{
			href: '/estudo/',
			icone: Stairs,
			titulo: 'Estudo',
			desc: 'Sessões de 10 em N1, N2 e N3',
			bloqueado: false
		},
		{
			href: '/simulado/',
			icone: Timer,
			titulo: 'Simulado',
			desc: 'Prova completa cronometrada',
			bloqueado: true
		}
	];

	onMount(async () => {
		const b = await carregarBanco();
		total = b.length;
		fg = b.filter((q) => q.parte === 'FG' && q.tipo === 'objetiva').length;
		ce = b.filter((q) => q.parte !== 'FG' && q.tipo === 'objetiva').length;
		disc = b.filter((q) => q.tipo === 'discursiva').length;
		edicoes = [...new Set(b.map((q) => q.edicao))].sort();
		xp = getXP();
		pronto = true;
	});
</script>

<div class="lg:grid lg:grid-cols-[1.05fr_0.95fr] lg:items-start lg:gap-10">
	<section class="blueprint -mx-4 -mt-6 bg-bar px-4 pt-8 pb-7 text-white lg:mx-0 lg:rounded-3xl lg:p-8" style="border-radius: 0 0 26px 26px;">
		<div class="mx-auto w-full max-w-3xl lg:max-w-none">
			<p class="rise inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-bold tracking-wide">
				ENADE 2026 · ENGENHARIA DE COMPUTAÇÃO
			</p>
			<h1
				class="rise mt-3 font-display text-[42px] leading-[0.95] font-black tracking-tight text-balance sm:text-5xl"
				style="animation-delay: 60ms"
			>
				Treine no formato da prova.
			</h1>
			<p class="rise mt-3 max-w-[46ch] text-[15px] leading-relaxed text-bar-fg" style="animation-delay: 120ms">
				Questões oficiais do INEP com correção na hora. Escolha um modo e comece.
			</p>
			<dl class="rise mt-5 flex flex-wrap gap-x-6 gap-y-2 text-sm font-semibold" style="animation-delay: 180ms">
				{#if !pronto}
					<div class="flex gap-4" role="status" aria-label="Carregando estatísticas">
						<div class="h-5 w-20 animate-pulse rounded-full bg-white/15"></div>
						<div class="h-5 w-24 animate-pulse rounded-full bg-white/15"></div>
					</div>
				{:else}
					<div class="flex items-center gap-1.5">
						<Lightning size={17} weight="fill" class="text-accent" aria-hidden="true" />
						<dt class="sr-only">XP</dt>
						<dd class="nums">{xp} XP</dd>
					</div>
					<div class="flex items-center gap-1.5">
						<Database size={17} weight="bold" class="text-accent" aria-hidden="true" />
						<dt class="sr-only">Questões no banco</dt>
						<dd class="nums">{total} questões</dd>
					</div>
				{/if}
			</dl>
			<div class="rise mt-5 hidden gap-3 lg:flex" style="animation-delay: 240ms">
				<a href="/treino/" class="btn3d duo-accent rounded-[14px] px-6 py-3 font-display text-base font-bold">
					Começar agora
				</a>
				<a href="/simulado/" class="rounded-[14px] border-2 border-white/25 px-6 py-3 font-display text-base font-bold transition-colors hover:bg-white/10">
					Ver o formato
				</a>
			</div>
		</div>
	</section>

	<aside class="mt-6 lg:mt-0" aria-label="Estado do banco de questões">
		<div class="rise rounded-3xl border border-line bg-card p-5 shadow-[0_10px_30px_-12px_rgba(20,33,61,0.25)]" style="animation-delay: 150ms">
			<div class="flex items-baseline justify-between gap-3">
				<p class="font-display text-sm font-extrabold tracking-[0.12em] uppercase">Banco de questões</p>
				<p class="nums text-sm font-bold text-ink-soft">{pronto ? `${total} / ${META}` : '…'}</p>
			</div>
			<div class="mt-3 h-2.5 overflow-hidden rounded-full bg-track" role="progressbar" aria-label="Questões no banco" aria-valuemin="0" aria-valuemax={META} aria-valuenow={total}>
				<div class="h-full rounded-full bg-accent transition-[width] duration-700" style="width: {(total / META) * 100}%"></div>
			</div>
			<dl class="mt-4 grid grid-cols-3 gap-2 text-center">
				<div class="rounded-2xl bg-tile p-3">
					<dd class="nums text-xl font-extrabold">{pronto ? fg : '—'}</dd>
					<dt class="text-[11px] font-semibold text-ink-soft">FG objetivas</dt>
				</div>
				<div class="rounded-2xl bg-tile p-3">
					<dd class="nums text-xl font-extrabold">{pronto ? ce : '—'}</dd>
					<dt class="text-[11px] font-semibold text-ink-soft">CE objetivas</dt>
				</div>
				<div class="rounded-2xl bg-tile p-3">
					<dd class="nums text-xl font-extrabold">{pronto ? disc : '—'}</dd>
					<dt class="text-[11px] font-semibold text-ink-soft">Discursivas</dt>
				</div>
			</dl>
			<p class="mt-3 text-xs text-ink-soft">
				{pronto && edicoes.length ? `Edições no banco: ${edicoes.join(' · ')}.` : 'Carregando…'}
				Cada questão aprovada entra aqui.
			</p>
		</div>
	</aside>
</div>

<p class="mt-6 overflow-hidden font-code text-[11px] tracking-[0.2em] whitespace-nowrap text-ink-soft/60 select-none" aria-hidden="true">
	01010011 01001001 01001101 01010111 01000001 01010010 01000101 00100000 01000101 01001110 01000001 01000100 01000101
</p>

<h2 class="mt-5 font-display text-xl font-extrabold tracking-tight">Escolha seu modo</h2>
<nav class="mt-3 space-y-3 lg:grid lg:grid-cols-3 lg:gap-4 lg:space-y-0" aria-label="Modos de estudo">
	{#each modos as m, k (m.href)}
		<a
			href={m.href}
			class="rise group flex items-center gap-4 rounded-3xl border border-line bg-card p-4 shadow-sm transition-all hover:-translate-y-0.5 active:scale-[0.99] lg:flex-col lg:items-start lg:p-6"
			style="animation-delay: {k * 70}ms"
		>
			<span class="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-accent-soft" aria-hidden="true">
				<m.icone size={28} weight="bold" class="text-accent-ink" aria-hidden="true" />
			</span>
			<span class="min-w-0 flex-1 lg:flex-none">
				<span class="block font-display text-lg font-bold tracking-tight">{m.titulo}</span>
				<span class="block text-sm text-ink-soft">{m.desc}</span>
			</span>
			{#if m.bloqueado}
				<LockSimple size={22} weight="bold" class="shrink-0 text-ink-soft opacity-60 lg:hidden" aria-hidden="true" />
			{:else}
				<CaretRight size={22} weight="bold" class="shrink-0 text-ink-soft opacity-60 transition-transform group-hover:translate-x-1 group-hover:text-accent group-hover:opacity-100 lg:hidden" aria-hidden="true" />
			{/if}
			{#if m.bloqueado}
				<span class="mt-1 hidden items-center gap-1.5 text-xs font-bold text-ink-soft lg:inline-flex">
					<LockSimple size={14} weight="bold" aria-hidden="true" /> Em breve
				</span>
			{:else}
				<span class="mt-1 hidden items-center gap-1.5 text-sm font-bold text-accent-ink lg:inline-flex">
					Começar <CaretRight size={16} weight="bold" aria-hidden="true" />
				</span>
			{/if}
		</a>
	{/each}
</nav>

<p class="mt-5 text-sm leading-relaxed text-ink-soft">
	Formação Geral e Componente Específico, objetivas com gabarito oficial e discursivas com
	padrão de resposta para autoavaliação.
</p>
