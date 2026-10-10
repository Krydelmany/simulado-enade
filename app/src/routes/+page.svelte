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

	onMount(async () => {
		total = (await carregarBanco()).length;
		xp = getXP();
		dias = getStreak().dias;
		hist = getHistorico();
		pronto = true;
	});
</script>

<section class="-mx-4 -mt-6 bg-bar px-4 pt-6 pb-6 text-white" style="border-radius: 0 0 26px 26px;">
	<div class="mx-auto max-w-3xl">
		<div class="flex items-start justify-between gap-3">
			<h1 class="font-display text-[32px] leading-[1.05] font-extrabold tracking-tight">
				Simulado<br />ENADE
			</h1>
			<div class="flex shrink-0 items-center gap-2">
				<p class="nums flex items-center gap-1.5 rounded-full bg-accent-soft px-3.5 py-2 text-sm font-extrabold text-accent-ink">
					<Lightning size={16} weight="fill" aria-hidden="true" />{pronto ? xp : '—'} XP
				</p>
				<p class="nums flex items-center gap-1.5 rounded-full bg-white/10 px-3.5 py-2 text-sm font-extrabold" title="Dias seguidos">
					<Flame size={16} weight="fill" class={dias > 0 ? 'flame-on text-accent' : ''} aria-hidden="true" />{pronto ? dias : '—'}
				</p>
			</div>
		</div>
		<div class="mt-4 rounded-2xl bg-white/10 p-4">
			<div class="flex items-baseline justify-between gap-3 text-sm">
				<p class="flex items-center gap-1.5 font-semibold"><Database size={15} weight="bold" aria-hidden="true" /> Banco de questões</p>
				<p class="nums font-bold">{pronto ? `${total} / ${META}` : '…'}</p>
			</div>
			<div class="mt-2 h-2.5 overflow-hidden rounded-full bg-white/15" role="progressbar" aria-label="Questões no banco" aria-valuemin="0" aria-valuemax={META} aria-valuenow={total}>
				<div class="h-full rounded-full bg-accent transition-[width] duration-700" style="width: {(total / META) * 100}%"></div>
			</div>
		</div>
	</div>
</section>

<h2 class="mt-6 font-display text-xl font-extrabold tracking-tight">Escolha seu modo</h2>
<nav class="mt-3 space-y-3" aria-label="Modos de estudo">
	{#each modos as m, k (m.href)}
		<a
			href={m.href}
			class="rise flex items-center gap-4 rounded-3xl border border-line bg-card p-4 shadow-sm transition-transform hover:-translate-y-0.5 active:scale-[0.99]"
			style="animation-delay: {k * 70}ms"
		>
			<span class="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-accent-soft" aria-hidden="true">
				<m.icone size={28} weight="bold" class="text-accent-ink" aria-hidden="true" />
			</span>
			<span class="min-w-0 flex-1">
				<span class="block font-display text-lg font-bold tracking-tight">{m.titulo}</span>
				<span class="block truncate text-sm text-ink-soft">{m.desc}</span>
			</span>
			{#if m.bloqueado}
				<LockSimple size={22} weight="bold" class="shrink-0 text-ink-soft opacity-60" aria-hidden="true" />
			{:else}
				<CaretRight size={22} weight="bold" class="shrink-0 text-ink-soft opacity-60" aria-hidden="true" />
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
