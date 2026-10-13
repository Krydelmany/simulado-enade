<script>
	import { onMount } from 'svelte';
	import { carregarBanco, contagens, ehGerada } from '$lib/banco.js';
	import { getXP, getParaRevisar } from '$lib/stats.js';
	import { resumoProgresso } from '$lib/resumo.js';
	import {
		ArrowRight,
		CaretRight,
		Infinity as InfinityIcon,
		Lightning,
		Stairs,
		Timer
	} from 'phosphor-svelte';

	// Meta do banco: prova completa de 2026 = 15 FG + 30 CE + 1 discursiva.
	const META = 160;

	let total = $state(0);
	let fg = $state(0);
	let ce = $state(0);
	let disc = $state(0);
	let geradas = $state(0);
	let edicoes = $state([]);
	let xp = $state(0);
	let pronto = $state(false);
	// progresso real do aluno — antes a home só mostrava XP, e XP não diz
	// nada sobre quanto a pessoa estudou
	let prog = $state(null);
	let paraRevisar = $state([]);

	// A barra é a informação mais honesta da home: mostra o quanto do banco
	// já existe. Capada em 100 para o caso do banco passar da meta.
	let pct = $derived(Math.min(100, Math.round((total / META) * 100)));

	// Ordem de leitura: treino (porta de entrada) → estudo → simulado (formato).
	const modos = [
		{
			href: '/treino/',
			icone: InfinityIcon,
			titulo: 'Treino livre',
			desc: 'Fila contínua de questões, sem fim.',
			cta: 'Começar'
		},
		{
			href: '/estudo/',
			icone: Stairs,
			titulo: 'Estudo',
			desc: 'Sessões de 10 por matéria: Fácil, Médio, Difícil ou ENADE.',
			cta: 'Começar'
		},
		{
			href: '/simulado/',
			icone: Timer,
			titulo: 'Simulado',
			desc: 'O formato da prova de 2026, passo a passo.',
			cta: 'Ver formato'
		}
	];

	onMount(async () => {
		try {
			const b = await carregarBanco();
			// `contagens` é a mesma função que o resto do app usa, então a home
			// não pode mais divergir do que o treino está mostrando
			const c = contagens(b);
			total = c.total;
			fg = c.fg;
			ce = c.ce;
			disc = c.discursivas;
			geradas = c.geradas;
			edicoes = [...new Set(b.filter((q) => !ehGerada(q)).map((q) => q.edicao))].sort();
			xp = getXP();
			prog = resumoProgresso();
			paraRevisar = getParaRevisar();
		} finally {
			// sempre fecha o esqueleto — sem "loading eterno" nem tela em branco
			pronto = true;
		}
	});
</script>

<div class="lg:grid lg:grid-cols-[1.05fr_0.95fr] lg:items-start lg:gap-10">
	<!-- 1. Hero: só o essencial (o que é + o que fazer). Os números moram no card. -->
	<section
		class="blueprint -mx-4 -mt-6 bg-bar px-4 pt-8 pb-8 text-white lg:mx-0 lg:rounded-3xl lg:p-9"
		style="border-radius: 0 0 26px 26px;"
	>
		<div class="mx-auto w-full max-w-3xl lg:max-w-none">
			<p
				class="rise inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-3 py-1 font-code text-label font-bold text-bar-fg"
			>
				ENADE 2026 · ENG. DE COMPUTAÇÃO
			</p>
			<h1 class="rise mt-4 font-display text-hero font-black text-balance" style="animation-delay: 60ms">
				Treine no formato da prova.
			</h1>
			<p
				class="rise mt-4 max-w-[44ch] text-[15px] leading-relaxed text-pretty text-bar-fg"
				style="animation-delay: 120ms"
			>
				Questões oficiais do INEP com correção na hora. Escolha um modo e comece.
			</p>
			<div class="rise mt-6 flex flex-col gap-3 sm:flex-row" style="animation-delay: 180ms">
				<a
					href="/treino/"
					class="btn3d duo-accent inline-flex min-h-[52px] items-center justify-center gap-2 rounded-[14px] px-6 font-display text-base font-bold"
				>
					Começar agora
					<ArrowRight size={18} weight="bold" aria-hidden="true" />
				</a>
				<a
					href="/simulado/"
					class="inline-flex min-h-[52px] items-center justify-center rounded-[14px] border-2 border-white/20 px-6 font-display text-base font-bold transition-colors hover:bg-white/10"
				>
					Ver o formato
				</a>
			</div>
		</div>
	</section>

	<!-- 2. Estado do banco: a peça central e a mais concreta da home. -->
	<aside class="mt-6 lg:mt-0" aria-label="Estado do banco de questões">
		<div
			class="rise rounded-3xl border border-line bg-card p-5 shadow-[0_10px_30px_-12px_rgba(20,33,61,0.25)] sm:p-6"
			style="animation-delay: 150ms"
		>
			<div class="flex items-start justify-between gap-3">
				<div class="min-w-0">
					<p class="font-code text-label font-bold text-ink-soft uppercase">Banco de questões</p>
					<p class="mt-1 text-xs text-ink-soft">Provas já processadas</p>
				</div>
				<span
					class="nums inline-flex shrink-0 items-center gap-1.5 rounded-full bg-accent-soft px-3 py-1 text-sm font-extrabold text-accent-ink"
				>
					<Lightning size={15} weight="fill" aria-hidden="true" />
					{pronto ? xp : 0} XP
				</span>
			</div>

			{#if !pronto}
				<div class="mt-5 space-y-3" role="status" aria-label="Carregando o estado do banco">
					<div class="h-11 w-32 animate-pulse rounded-lg bg-skel"></div>
					<div class="h-3 w-full animate-pulse rounded-full bg-skel"></div>
					<div class="grid grid-cols-3 gap-2">
						<div class="h-[70px] animate-pulse rounded-2xl bg-skel"></div>
						<div class="h-[70px] animate-pulse rounded-2xl bg-skel"></div>
						<div class="h-[70px] animate-pulse rounded-2xl bg-skel"></div>
					</div>
				</div>
			{:else}
				<p class="mt-5 flex items-baseline gap-1.5 font-display">
					<span class="nums text-5xl leading-none font-black">{total}</span>
					<span class="nums text-lg font-bold text-ink-soft">/ {META}</span>
				</p>
				<p class="mt-1 text-sm text-ink-soft">questões prontas para treinar</p>

				<div
					class="mt-4 h-3 overflow-hidden rounded-full border border-line bg-track"
					role="progressbar"
					aria-label="Questões no banco"
					aria-valuemin="0"
					aria-valuemax={META}
					aria-valuenow={total}
				>
					<div
						class="h-full rounded-full bg-accent-bar transition-[width] duration-700"
						style="width: {pct}%"
					></div>
				</div>

				<dl class="mt-4 grid grid-cols-3 gap-2 text-center">
					<div class="rounded-2xl bg-tile p-3">
						<dd class="nums text-xl font-extrabold">{fg}</dd>
						<dt class="mt-0.5 text-[11px] font-semibold text-ink-soft">FG objetivas</dt>
					</div>
					<div class="rounded-2xl bg-tile p-3">
						<dd class="nums text-xl font-extrabold">{ce}</dd>
						<dt class="mt-0.5 text-[11px] font-semibold text-ink-soft">CE objetivas</dt>
					</div>
					<div class="rounded-2xl bg-tile p-3">
						<dd class="nums text-xl font-extrabold">{disc}</dd>
						<dt class="mt-0.5 text-[11px] font-semibold text-ink-soft">Discursivas</dt>
					</div>
				</dl>

				{#if total === 0}
					<p
						class="mt-4 rounded-2xl border border-dashed border-warn-line bg-warn-bg p-3 text-xs leading-relaxed text-warn-fg"
					>
						O banco não carregou. Verifique a conexão e toque em
						<button type="button" class="font-bold underline" onclick={() => location.reload()}>recarregue a página</button
						>.
					</p>
				{:else if edicoes.length}
					<p class="mt-4 text-xs leading-relaxed text-pretty text-ink-soft">
						Edições no banco: {edicoes.join(' · ')}. Cada questão aprovada entra aqui.
						{#if geradas}
							Mais {geradas} questões de revisão por matéria, em três níveis, no modo Estudo.
						{/if}
					</p>
				{/if}

				<!--
					Progresso do aluno. Sem isto a home só dizia "0 XP": o
					acumulado é bonito mas não responde a pergunta que importa,
					que é "eu estudei alguma coisa?". Só aparece quando há dados
					— aluno novo não deve ver um painel zerado.
				-->
				{#if prog && prog.temDados}
					<div class="mt-5 border-t border-line pt-5">
						<p class="font-code text-label font-bold text-ink-soft uppercase">Seu progresso</p>
						<dl class="mt-3 grid grid-cols-3 gap-2 text-center">
							<div class="rounded-2xl bg-panel p-3">
								<dd class="nums text-xl font-extrabold">{prog.respondidasNumero}</dd>
								<dt class="mt-0.5 text-[11px] font-semibold text-ink-soft">Respondidas</dt>
							</div>
							<div class="rounded-2xl bg-panel p-3">
								<dd class="nums text-xl font-extrabold text-ok-fg">{prog.precisao}</dd>
								<dt class="mt-0.5 text-[11px] font-semibold text-ink-soft">Precisão</dt>
							</div>
							<div class="rounded-2xl bg-panel p-3">
								<dd class="nums text-xl font-extrabold">{prog.totalErrosNumero}</dd>
								<dt class="mt-0.5 text-[11px] font-semibold text-ink-soft">Para revisar</dt>
							</div>
						</dl>

						{#if prog.ultimoTreinoRelativo}
							<p class="mt-3 text-xs text-ink-soft">
								Último estudo: {prog.ultimoTreinoRelativo}
							</p>
						{/if}

						{#if paraRevisar.length}
							<a
								href="/treino/?modo=revisao"
								class="btn3d mt-3 flex min-h-11 w-full items-center justify-center rounded-2xl border-2 border-accent px-4 text-sm font-bold text-accent-ink"
							>
								Revisar {paraRevisar.length} {paraRevisar.length > 1 ? 'questões' : 'questão'}
							</a>
						{/if}
					</div>
				{/if}
			{/if}
		</div>
	</aside>
</div>

<!-- 3. Modos: três caminhos claros, sem nenhum botão morto. -->
<div class="mt-9 lg:mt-12">
	<div class="flex items-end justify-between gap-3">
		<h2 class="font-display text-title font-extrabold">Escolha seu modo</h2>
		<p class="hidden text-xs font-semibold text-ink-soft sm:block">Três formas de estudar</p>
	</div>

	<nav
		class="mt-4 space-y-3 lg:grid lg:grid-cols-3 lg:gap-4 lg:space-y-0"
		aria-label="Modos de estudo"
	>
		{#each modos as m, k (m.href)}
			<a
				href={m.href}
				class="rise group flex items-center gap-4 rounded-3xl border border-line bg-card p-4 shadow-sm transition-all hover:-translate-y-0.5 hover:border-ink/25 active:scale-[0.99] lg:flex-col lg:items-start lg:gap-5 lg:p-6"
				style="animation-delay: {k * 70}ms"
			>
				<span
					class="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-accent-soft"
					aria-hidden="true"
				>
					<m.icone size={28} weight="bold" class="text-accent-ink" aria-hidden="true" />
				</span>
				<span class="min-w-0 flex-1 lg:flex-none">
					<span class="block font-display text-heading font-bold">{m.titulo}</span>
					<span class="mt-0.5 block text-sm leading-relaxed text-ink-soft">{m.desc}</span>
				</span>
				<span
					class="hidden shrink-0 items-center gap-1.5 text-sm font-bold text-accent-ink lg:mt-auto lg:inline-flex"
				>
					{m.cta}
					<CaretRight size={16} weight="bold" aria-hidden="true" />
				</span>
				<CaretRight
					size={22}
					weight="bold"
					class="shrink-0 text-ink-soft opacity-60 transition-transform group-hover:translate-x-1 group-hover:text-accent-ink group-hover:opacity-100 lg:hidden"
					aria-hidden="true"
				/>
			</a>
		{/each}
	</nav>

	<p class="mt-5 text-sm leading-relaxed text-pretty text-ink-soft">
		Formação Geral e Componente Específico: objetivas com gabarito oficial e discursivas com padrão
		de resposta para autoavaliação.
	</p>
</div>
