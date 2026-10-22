<script>
	import { onMount } from 'svelte';
	import { carregarBanco, contagens, ehGerada } from '$lib/banco.js';
	import { getXP, getParaRevisar } from '$lib/stats.js';
	import { resumoProgresso } from '$lib/resumo.js';
	import { DATA_ENADE, diasAteEnade } from '$lib/enade.js';
	import { nomeMateria } from '$lib/materias.js';
	import {
		ArrowRight,
		CalendarBlank,
		CaretRight,
		Infinity as InfinityIcon,
		Lightning,
		Stairs,
		Timer
	} from 'phosphor-svelte';

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
	// null até montar: no prerender a contagem ficaria congelada no dia do build
	let dias = $state(null);

	let temProgresso = $derived(Boolean(prog?.temDados));

	// As 3 matérias de menor acerto, só com 3+ respostas: com 1 ou 2 o
	// percentual é sorte, e a lista mandaria o aluno estudar a coisa errada.
	let reforcar = $derived(
		(prog?.porMateria ?? [])
			.filter((m) => m.nome && m.acertosNumero + m.errosNumero >= 3)
			.sort((a, b) => a.precisaoNumero - b.precisaoNumero)
			.slice(0, 3)
	);

	// "29 de novembro", sem depender do fuso do servidor do build
	const DATA_EXTENSO = (() => {
		const [, m, d] = DATA_ENADE.split('-').map(Number);
		const MESES = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'];
		return `${d} de ${MESES[m - 1]}`;
	})();

	// Ordem de leitura: treino (porta de entrada) → estudo → simulado (formato).
	const modos = [
		{
			href: '/treino/',
			icone: InfinityIcon,
			titulo: 'Treino livre',
			desc: 'Uma questão depois da outra, sem fim, com correção na hora.',
			cta: 'Começar'
		},
		{
			href: '/estudo/',
			icone: Stairs,
			titulo: 'Estudo',
			desc: 'Sessões de 10 por matéria: Fácil, Médio, Difícil ou ENADE.',
			cta: 'Escolher sessão'
		},
		{
			href: '/simulado/',
			icone: Timer,
			titulo: 'Simulado',
			desc: 'A prova de 2026 inteira: 45 objetivas + 1 discursiva em 4 h.',
			cta: 'Fazer simulado'
		}
	];

	onMount(async () => {
		dias = diasAteEnade();
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
			// só o que ainda está no banco: uma questão que saiu (as anuladas)
			// continuava contada aqui, e a revisão abria com menos do que o botão
			// prometia
			const ids = new Set(b.map((q) => q.id));
			paraRevisar = getParaRevisar().filter((id) => ids.has(id));
		} finally {
			// sempre fecha o esqueleto — sem "loading eterno" nem tela em branco
			pronto = true;
		}
	});

	/** "2014, 2017, 2019 e 2023" */
	function listar(xs) {
		return xs.length > 1 ? `${xs.slice(0, -1).join(', ')} e ${xs.at(-1)}` : xs.join('');
	}
</script>

<div class="lg:grid lg:grid-cols-[1.1fr_0.9fr] lg:items-start lg:gap-6">
	<!-- 1. Hero: quando é a prova + o que fazer. Uma ação principal. -->
	<section class="blueprint faixa px-4 pt-7 pb-8 text-white sm:p-8 lg:p-10">
		<p
			class="rise inline-flex min-h-8 items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-sm font-semibold text-bar-fg"
		>
			<CalendarBlank size={16} weight="bold" aria-hidden="true" />
			{#if dias !== null && dias > 1}
				<span>Faltam <span class="nums font-bold text-white">{dias} dias</span> para o ENADE</span>
			{:else if dias === 1}
				<span>O ENADE é <span class="font-bold text-white">amanhã</span></span>
			{:else if dias === 0}
				<span>O ENADE é <span class="font-bold text-white">hoje</span>. Boa prova!</span>
			{:else}
				<span>ENADE em {DATA_EXTENSO}</span>
			{/if}
		</p>
		<h1 class="rise mt-5 font-display text-hero font-black text-balance" style="animation-delay: 60ms">
			Treine no formato da prova.
		</h1>
		<p
			class="rise mt-4 max-w-[44ch] text-base leading-relaxed text-pretty text-bar-fg"
			style="animation-delay: 120ms"
		>
			Questões oficiais do INEP de Engenharia de Computação, com correção na hora.
		</p>
		<div class="rise mt-7 flex flex-col gap-3 sm:flex-row" style="animation-delay: 180ms">
			<a
				href="/treino/"
				class="btn3d duo-accent inline-flex min-h-[52px] items-center justify-center gap-2 rounded-[14px] px-6 font-display text-base font-bold"
			>
				{temProgresso ? 'Continuar treinando' : 'Começar agora'}
				<ArrowRight size={18} weight="bold" aria-hidden="true" />
			</a>
			<a
				href="/simulado/"
				class="inline-flex min-h-[52px] items-center justify-center rounded-[14px] border-2 border-white/25 px-6 font-display text-base font-bold transition-colors hover:bg-white/10"
			>
				Fazer o simulado
			</a>
		</div>
	</section>

	<!--
		2. Ao lado do hero: o progresso de quem já estudou; para quem chega
		agora, o que tem no banco. Antes este cartão era "Banco de questões:
		156/156" com uma barra cheia — um número de quando o banco ainda
		estava sendo montado, que não dizia nada para o aluno.
	-->
	<aside class="mt-6 lg:mt-0" aria-label={temProgresso ? 'Seu progresso' : 'O que tem no banco'}>
		<div
			class="rise rounded-3xl border border-line bg-card p-5 shadow-[0_10px_30px_-12px_rgba(20,33,61,0.25)] sm:p-6"
			style="animation-delay: 150ms"
		>
			{#if !pronto}
				<div class="space-y-3" role="status" aria-label="Carregando">
					<div class="h-6 w-40 animate-pulse rounded-lg bg-skel"></div>
					<div class="grid grid-cols-3 gap-2">
						<div class="h-[76px] animate-pulse rounded-2xl bg-skel"></div>
						<div class="h-[76px] animate-pulse rounded-2xl bg-skel"></div>
						<div class="h-[76px] animate-pulse rounded-2xl bg-skel"></div>
					</div>
				</div>
			{:else if total === 0}
				<p
					class="rounded-2xl border border-dashed border-warn-line bg-warn-bg p-3 text-sm leading-relaxed text-warn-fg"
					role="alert"
				>
					As questões não carregaram. Confira a internet e
					<button type="button" class="font-bold underline" onclick={() => location.reload()}>recarregue a página</button
					>.
				</p>
			{:else if temProgresso}
				<div class="flex items-center justify-between gap-3">
					<h2 class="font-display text-heading font-bold">Seu progresso</h2>
					{#if xp > 0}
						<span
							class="nums inline-flex shrink-0 items-center gap-1.5 rounded-full bg-accent-soft px-3 py-1 text-sm font-extrabold text-accent-ink"
						>
							<Lightning size={15} weight="fill" aria-hidden="true" />
							{xp} XP
						</span>
					{/if}
				</div>
				{#if prog.ultimoTreinoRelativo}
					<p class="mt-0.5 text-sm text-ink-soft">Último estudo: {prog.ultimoTreinoRelativo}</p>
				{/if}
				<dl class="mt-4 grid grid-cols-3 gap-2 text-center">
					<div class="rounded-2xl bg-tile px-2 py-3">
						<dd class="nums font-display text-2xl font-extrabold">{prog.respondidasNumero}</dd>
						<dt class="mt-0.5 text-xs font-semibold text-ink-soft">Respondidas</dt>
					</div>
					<div class="rounded-2xl bg-tile px-2 py-3">
						<dd class="nums font-display text-2xl font-extrabold">{prog.precisao}</dd>
						<dt class="mt-0.5 text-xs font-semibold text-ink-soft">Acerto</dt>
					</div>
					<div class="rounded-2xl bg-tile px-2 py-3">
						<dd class="nums font-display text-2xl font-extrabold">{paraRevisar.length}</dd>
						<dt class="mt-0.5 text-xs font-semibold text-ink-soft">Para revisar</dt>
					</div>
				</dl>
				{#if reforcar.length}
					<h3 class="mt-5 text-label font-bold text-ink-soft">Matérias para reforçar</h3>
					<ul class="mt-2 space-y-2.5">
						{#each reforcar as m (m.nome)}
							<li>
								<div class="flex items-baseline justify-between gap-3 text-sm">
									<span class="min-w-0 truncate font-semibold">{nomeMateria(m.nome)}</span>
									<span class="nums shrink-0 font-bold">{m.precisao}</span>
								</div>
								<div class="mt-1 h-1.5 overflow-hidden rounded-full bg-track" aria-hidden="true">
									<div class="h-full rounded-full bg-accent-bar" style="width: {Math.round(m.precisaoNumero * 100)}%"></div>
								</div>
							</li>
						{/each}
					</ul>
				{/if}
				{#if paraRevisar.length}
					<a
						href="/treino/?modo=revisao"
						class="btn3d mt-5 flex min-h-11 w-full items-center justify-center gap-2 rounded-2xl border-2 border-accent bg-card px-4 text-sm font-bold text-accent-ink"
					>
						Revisar {paraRevisar.length} {paraRevisar.length > 1 ? 'questões' : 'questão'}
						<ArrowRight size={16} weight="bold" aria-hidden="true" />
					</a>
				{/if}
			{:else}
				<h2 class="font-display text-heading font-bold">O que tem aqui</h2>
				<p class="mt-0.5 text-sm text-ink-soft">
					{total} questões oficiais das provas de {listar(edicoes)}.
				</p>
				<dl class="mt-4 grid grid-cols-3 gap-2 text-center">
					<div class="rounded-2xl bg-tile px-2 py-3">
						<dd class="nums font-display text-2xl font-extrabold">{fg}</dd>
						<dt class="mt-0.5 text-xs font-semibold text-ink-soft">Formação Geral</dt>
					</div>
					<div class="rounded-2xl bg-tile px-2 py-3">
						<dd class="nums font-display text-2xl font-extrabold">{ce}</dd>
						<dt class="mt-0.5 text-xs font-semibold text-ink-soft">Específicas</dt>
					</div>
					<div class="rounded-2xl bg-tile px-2 py-3">
						<dd class="nums font-display text-2xl font-extrabold">{disc}</dd>
						<dt class="mt-0.5 text-xs font-semibold text-ink-soft">Discursivas</dt>
					</div>
				</dl>
				{#if geradas}
					<p class="mt-4 text-sm leading-relaxed text-pretty text-ink-soft">
						E mais {geradas} questões de revisão por matéria, em três níveis, no modo Estudo.
					</p>
				{/if}
			{/if}
		</div>
	</aside>
</div>

<!-- 3. Modos: três caminhos claros, sem nenhum botão morto. -->
<section class="mt-10 lg:mt-12" aria-labelledby="titulo-modos">
	<h2 id="titulo-modos" class="font-display text-title font-extrabold">Como você quer estudar?</h2>

	<nav class="mt-4 grid gap-3 lg:grid-cols-3 lg:gap-4" aria-label="Modos de estudo">
		{#each modos as m, k (m.href)}
			<a
				href={m.href}
				class="rise group flex items-center gap-4 rounded-3xl border border-line bg-card p-4 transition-colors hover:border-accent active:scale-[0.99] lg:flex-col lg:items-start lg:p-6"
				style="animation-delay: {k * 70}ms"
			>
				<span
					class="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-accent-soft"
					aria-hidden="true"
				>
					<m.icone size={28} weight="bold" class="text-accent-ink" aria-hidden="true" />
				</span>
				<span class="min-w-0 flex-1">
					<span class="block font-display text-heading font-bold">{m.titulo}</span>
					<span class="mt-0.5 block text-sm leading-relaxed text-ink-soft">{m.desc}</span>
				</span>
				<span class="hidden shrink-0 items-center gap-1.5 text-sm font-bold text-accent-ink lg:inline-flex">
					{m.cta}
					<CaretRight size={16} weight="bold" aria-hidden="true" />
				</span>
				<CaretRight
					size={22}
					weight="bold"
					class="shrink-0 text-ink-soft transition-transform group-hover:translate-x-1 group-hover:text-accent-ink lg:hidden"
					aria-hidden="true"
				/>
			</a>
		{/each}
	</nav>

	{#if pronto && total && temProgresso}
		<p class="mt-5 text-sm leading-relaxed text-pretty text-ink-soft">
			No banco: {total} questões oficiais das provas de {listar(edicoes)} ({fg} de Formação Geral,
			{ce} específicas e {disc} discursivas){#if geradas}, mais {geradas} de revisão no modo Estudo{/if}.
		</p>
	{/if}
</section>
