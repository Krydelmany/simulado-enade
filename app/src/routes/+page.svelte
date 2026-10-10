<script>
	import { onMount } from 'svelte';
	import { carregarBanco } from '$lib/banco.js';
	import { getXP, getStreak, getHistorico } from '$lib/stats.js';
	import {
		CaretRight,
		Database,
		Flame,
		Infinity as InfinityIcon,
		Lightning,
		LockSimple,
		Stairs,
		Timer
	} from 'phosphor-svelte';

	const META = 160;
	let total = $state(0);
	let xp = $state(0);
	let dias = $state(0);
	let hist = $state([]);
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

	// motivo decorativo: cartão-resposta preenchido
	const cartao = [
		{ n: '01', ok: 'C' },
		{ n: '02', ok: 'D' },
		{ n: '03', ok: 'C' },
		{ n: '04', ok: 'B' },
		{ n: '05', ok: 'C' }
	];
	const letras = ['A', 'B', 'C', 'D', 'E'];

	onMount(async () => {
		total = (await carregarBanco()).length;
		xp = getXP();
		dias = getStreak().dias;
		hist = getHistorico();
		pronto = true;
	});
</script>

<div class="lg:grid lg:grid-cols-[1.05fr_0.95fr] lg:items-start lg:gap-10">
	<section class="pauta -mx-4 -mt-6 bg-bar px-4 pt-8 pb-7 text-white lg:mx-0 lg:rounded-3xl lg:p-8" style="border-radius: 0 0 26px 26px;">
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
					<div class="h-5 w-24 animate-pulse rounded-full bg-white/15"></div>
				</div>
			{:else}
				<div class="flex items-center gap-1.5">
					<Lightning size={17} weight="fill" class="text-accent" aria-hidden="true" />
					<dt class="sr-only">XP</dt>
					<dd class="nums">{xp} XP</dd>
				</div>
				<div class="flex items-center gap-1.5">
					<Flame size={17} weight="fill" class={dias > 0 ? 'flame-on text-accent' : 'opacity-50'} aria-hidden="true" />
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

	<aside class="mt-6 lg:mt-0" aria-hidden="true">
		<div class="rise rounded-3xl border border-line bg-card p-5 shadow-[0_10px_30px_-12px_rgba(20,33,61,0.25)]" style="animation-delay: 150ms">
			<div class="flex items-baseline justify-between gap-3">
				<p class="font-display text-sm font-extrabold tracking-[0.12em] uppercase">Cartão-resposta</p>
				<p class="nums text-xs font-bold text-ink-soft">2019 · FG</p>
			</div>
			<div class="mt-4 space-y-2.5">
				{#each cartao as q (q.n)}
					<div class="flex items-center gap-2">
						<span class="nums w-7 text-sm font-extrabold text-ink-soft">{q.n}</span>
						<span class="flex gap-1.5">
							{#each letras as l (l)}
								<span
									class="flex h-7 w-7 items-center justify-center rounded-full border-2 text-[11px] font-extrabold {l === q.ok
										? 'border-accent bg-accent text-white'
										: 'border-line text-ink-soft/60'}"
								>
									{l}
								</span>
							{/each}
						</span>
					</div>
				{/each}
			</div>
			<div class="mt-4 h-2 overflow-hidden rounded-full bg-track">
				<div class="h-full w-3/5 rounded-full bg-accent"></div>
			</div>
			<p class="nums mt-1.5 text-right text-xs font-bold text-ink-soft">6/10 nesta sessão</p>
		</div>
	</aside>
</div>

<h2 class="mt-8 font-display text-xl font-extrabold tracking-tight">Escolha seu modo</h2>
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

<section class="mt-3 flex items-center gap-4 rounded-3xl border border-line bg-card p-4 shadow-sm" aria-label="Sequência de estudos">
	<div class="min-w-0 flex-1">
		<p class="text-sm text-ink-soft">Sequência atual</p>
		<p class="nums font-display text-2xl font-extrabold">{pronto ? dias : '—'} {dias === 1 ? 'dia' : 'dias'}</p>
		<div class="mt-2 flex gap-1.5" aria-hidden="true">
			{#each hist as on, k (k)}
				<span class="h-2 flex-1 rounded-full {on ? 'bg-accent' : 'bg-track'}"></span>
			{/each}
		</div>
	</div>
	<span class="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-accent-soft" aria-hidden="true">
		<Flame size={30} weight="fill" class="text-accent {dias > 0 && pronto ? 'flame-on' : ''}" aria-hidden="true" />
	</span>
</section>

<p class="mt-5 text-sm leading-relaxed text-ink-soft">
	Formação Geral e Componente Específico, objetivas com gabarito oficial e discursivas com
	padrão de resposta para autoavaliação.
</p>
