<script>
	import { onMount } from 'svelte';
	import { carregarBanco, contagens, ehGerada } from '$lib/banco.js';
	import { getXP, getParaRevisar } from '$lib/stats.js';
	import { resumoProgresso } from '$lib/resumo.js';
	import { DATA_ENADE, diasAteEnade } from '$lib/enade.js';
	import { nomeMateria } from '$lib/materias.js';
	import { cursoAtual } from '$lib/curso.js';
	import { nuvemLigada, contaLocal } from '$lib/nuvem.js';
	import {
		ArrowRight,
		BookOpen,
		CalendarBlank,
		CaretRight,
		Check,
		Code,
		FlagCheckered,
		Infinity as InfinityIcon,
		Lightning,
		NotePencil,
		Stairs,
		Timer,
		UsersThree
	} from 'phosphor-svelte';

	const curso = cursoAtual();

	let total = $state(0);
	let fg = $state(0);
	let ce = $state(0);
	let disc = $state(0);
	let geradas = $state(0);
	let edicoes = $state([]);
	let xp = $state(0);
	let pronto = $state(false);
	let prog = $state(null);
	let paraRevisar = $state([]);
	let dias = $state(null);
	let convidarTurma = $state(false);

	let temProgresso = $derived(Boolean(prog?.temDados));
	let pctAcerto = $derived(Math.round((prog?.precisaoNumero ?? 0) * 100));

	// As 3 matérias de menor acerto, só com 3+ respostas
	let reforcar = $derived(
		(prog?.porMateria ?? [])
			.filter((m) => m.nome && m.acertosNumero + m.errosNumero >= 3)
			.sort((a, b) => a.precisaoNumero - b.precisaoNumero)
			.slice(0, 3)
	);

	// "29 de novembro", sem depender do fuso do servidor do build
	const DATA_EXTENSO = (() => {
		const [, m, d] = DATA_ENADE.split('-').map(Number);
		const MESES = [
			'janeiro',
			'fevereiro',
			'março',
			'abril',
			'maio',
			'junho',
			'julho',
			'agosto',
			'setembro',
			'outubro',
			'novembro',
			'dezembro'
		];
		return `${d} de ${MESES[m - 1]}`;
	})();

	// Trilha viva de estudo mapeada sobre os modos e o progresso real do banco
	// (sempre exatamente um nó ativo por vez, conforme o avanço real do aluno)
	let etapasTrilha = $derived.by(() => {
		const respondidas = prog?.respondidasNumero ?? 0;
		return [
			{
				passo: '01',
				href: '/estudo/',
				icone: Stairs,
				titulo: 'Estudo por níveis',
				desc: 'Sessões curtas de 10 questões por matéria — comece no Fácil, avance ao Difícil ou vá direto nas oficiais.',
				selo: geradas ? `${geradas} guiadas · ${total} oficiais` : 'Sessões de 10',
				cta: 'Escolher nível',
				estado: !temProgresso ? 'atual' : 'feito'
			},
			{
				passo: '02',
				href: '/treino/',
				icone: InfinityIcon,
				titulo: 'Treino livre contínuo',
				desc: 'Fila embaralhada com o banco inteiro, filtro por matéria e correção imediata com passo a passo.',
				selo: temProgresso ? `${respondidas} respondidas · ${prog.precisao}` : 'Correção na hora',
				cta: temProgresso ? 'Continuar treino' : 'Começar treino',
				estado: !temProgresso ? 'aberto' : respondidas < 45 ? 'atual' : 'feito'
			},
			{
				passo: '03',
				href: '/treino/?modo=discursivas',
				icone: NotePencil,
				titulo: 'Discursivas do Componente Específico',
				desc: 'Pratique no papel e compare cada ponto com o padrão oficial de resposta do INEP.',
				selo: disc ? `${disc} questões oficiais` : 'Padrão INEP',
				cta: 'Praticar escrita',
				estado: respondidas >= 45 ? 'atual' : 'aberto'
			},
			{
				passo: '04',
				href: '/simulado/',
				icone: Timer,
				titulo: 'Simulado ENADE 2026',
				desc: 'A prova completa no formato da Portaria INEP nº 161: 15 FG, 30 CE e 1 discursiva em 4 horas.',
				selo: 'Meta · 46 questões · 4 h',
				cta: 'Abrir simulado',
				estado: 'marco'
			}
		];
	});

	onMount(async () => {
		dias = diasAteEnade();
		convidarTurma = nuvemLigada && !contaLocal();
		try {
			const b = await carregarBanco();
			const c = contagens(b);
			total = c.total;
			fg = c.fg;
			ce = c.ce;
			disc = c.discursivas;
			geradas = c.geradas;
			edicoes = [...new Set(b.filter((q) => !ehGerada(q)).map((q) => q.edicao))].sort();
			xp = getXP();
			prog = resumoProgresso();
			const ids = new Set(b.map((q) => q.id));
			paraRevisar = getParaRevisar().filter((id) => ids.has(id));
		} finally {
			pronto = true;
		}
	});

	function listar(xs) {
		return xs.length > 1 ? `${xs.slice(0, -1).join(', ')} e ${xs.at(-1)}` : xs.join('');
	}
</script>

<!-- 1. Hero aberto e calmo + Cartão de ritmo/banco ao lado -->
<div class="grid gap-6 lg:grid-cols-[1.15fr_0.85fr] lg:items-start">
	<section class="folha curso-halo rise rounded-3xl p-6 sm:p-8 lg:p-9">
		<div class="flex flex-wrap items-center gap-2">
			<p
				class="inline-flex min-h-8 items-center gap-1.5 rounded-full border border-milestone-border bg-milestone-soft px-3 py-1 text-xs font-bold text-milestone-ink"
			>
				<CalendarBlank size={14} weight="bold" aria-hidden="true" />
				{#if dias !== null && dias > 1}
					<span>Faltam <span class="nums font-extrabold">{dias} dias</span> para o ENADE</span>
				{:else if dias === 1}
					<span>O ENADE é <strong>amanhã</strong></span>
				{:else if dias === 0}
					<span>O ENADE é <strong>hoje</strong>. Boa prova!</span>
				{:else}
					<span>ENADE em {DATA_EXTENSO}</span>
				{/if}
			</p>
			<span class="rounded-full bg-tile px-3 py-1 text-xs font-semibold text-ink-soft">
				{curso.nome}
			</span>
		</div>

		<h1 class="mt-5 font-display text-hero font-extrabold text-balance text-ink">
			{#if temProgresso}
				Continue no seu ritmo.
			{:else}
				Estude no formato real da prova.
			{/if}
		</h1>

		<p class="mt-3.5 max-w-[46ch] text-[15px] leading-relaxed text-pretty text-ink-soft sm:text-base">
			Prática guiada com questões oficiais do INEP, verificação passo a passo e simulado cronometrado para o ENADE 2026.
		</p>

		<div class="mt-7 flex flex-col gap-2.5 sm:flex-row sm:items-center">
			<a
				href="/treino/"
				class="btn-primario inline-flex min-h-12 items-center justify-center gap-2 rounded-full px-6 font-display text-[15px] font-bold"
			>
				{temProgresso ? 'Continuar treinando' : 'Começar a praticar'}
				<ArrowRight size={17} weight="bold" aria-hidden="true" />
			</a>
			<a
				href="/simulado/"
				class="btn-suave inline-flex min-h-12 items-center justify-center gap-2 rounded-full px-6 font-display text-[15px] font-bold"
			>
				Fazer simulado real
			</a>
		</div>
	</section>

	<aside class="space-y-4" aria-label={temProgresso ? 'Seu progresso' : 'O que tem no banco'}>
		{#if convidarTurma}
			<a
				href="/conta/"
				class="superficie rise group flex items-center gap-3.5 rounded-3xl border-accent-border p-4 transition-colors hover:bg-accent-soft/60"
			>
				<span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-accent-soft text-accent-ink" aria-hidden="true">
					<UsersThree size={20} weight="bold" />
				</span>
				<span class="min-w-0 flex-1">
					<span class="block font-display text-[15px] font-bold text-ink">Tem turma? Entre com o código</span>
					<span class="block text-xs leading-snug text-ink-soft">Seu professor acompanha seu avanço e você participa do ranking.</span>
				</span>
				<CaretRight size={18} weight="bold" class="shrink-0 text-accent-ink transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
			</a>
		{/if}

		<div class="superficie rise rounded-3xl p-5 sm:p-6" style="animation-delay: 60ms">
			{#if !pronto}
				<div class="space-y-3" role="status" aria-label="Carregando">
					<div class="h-5 w-36 animate-pulse rounded-lg bg-skel"></div>
					<div class="grid grid-cols-3 gap-2">
						<div class="h-[74px] animate-pulse rounded-2xl bg-skel"></div>
						<div class="h-[74px] animate-pulse rounded-2xl bg-skel"></div>
						<div class="h-[74px] animate-pulse rounded-2xl bg-skel"></div>
					</div>
				</div>
			{:else if total === 0}
				<p
					class="rounded-2xl border border-dashed border-warn-line bg-warn-bg p-3.5 text-sm leading-relaxed text-warn-fg"
					role="alert"
				>
					As questões não carregaram. Confira a internet e
					<button type="button" class="font-bold underline" onclick={() => location.reload()}>recarregue a página</button>.
				</p>
			{:else if temProgresso}
				<div class="flex items-center justify-between gap-3">
					<div>
						<h2 class="font-display text-heading font-bold text-ink">Seu progresso</h2>
						{#if prog.ultimoTreinoRelativo}
							<p class="mt-0.5 text-xs text-ink-soft">Último estudo: {prog.ultimoTreinoRelativo}</p>
						{/if}
					</div>
					{#if xp > 0}
						<span
							class="nums inline-flex shrink-0 items-center gap-1 rounded-full border border-milestone-border bg-milestone-soft px-3 py-1 text-xs font-extrabold text-milestone-ink"
						>
							<Lightning size={14} weight="fill" aria-hidden="true" />
							{xp} XP
						</span>
					{/if}
				</div>

				<dl class="mt-4 grid grid-cols-3 gap-2 text-center">
					<div class="rounded-2xl bg-panel px-2 py-3">
						<dd class="nums font-display text-2xl font-extrabold text-ink">{prog.respondidasNumero}</dd>
						<dt class="mt-0.5 text-xs font-medium text-ink-soft">Respondidas</dt>
					</div>
					<div class="rounded-2xl bg-panel px-2 py-3">
						<dd class="nums font-display text-2xl font-extrabold text-ok-fg">{pctAcerto}%</dd>
						<dt class="mt-0.5 text-xs font-medium text-ink-soft">Acerto</dt>
					</div>
					<div class="rounded-2xl bg-panel px-2 py-3">
						<dd class="nums font-display text-2xl font-extrabold text-ink">{paraRevisar.length}</dd>
						<dt class="mt-0.5 text-xs font-medium text-ink-soft">Para revisar</dt>
					</div>
				</dl>

				{#if reforcar.length}
					<div class="mt-5">
						<h3 class="text-label font-bold text-ink-soft">Onde reforçar primeiro</h3>
						<ul class="mt-2.5 space-y-2.5">
							{#each reforcar as m (m.nome)}
								<li>
									<a href="/treino/?materia={m.nome}" class="group block rounded-xl p-1.5 -mx-1.5 transition-colors hover:bg-panel">
										<div class="flex items-baseline justify-between gap-3 text-sm">
											<span class="min-w-0 truncate font-semibold text-ink group-hover:text-accent-ink">{nomeMateria(m.nome)}</span>
											<span class="nums shrink-0 text-xs font-bold text-ink-soft">{m.precisao}</span>
										</div>
										<div class="mt-1.5 h-1.5 overflow-hidden rounded-full bg-track" aria-hidden="true">
											<div
												class="h-full rounded-full bg-accent-bar transition-[width] duration-300"
												style="width: {Math.round(m.precisaoNumero * 100)}%"
											></div>
										</div>
									</a>
								</li>
							{/each}
						</ul>
					</div>
				{/if}

				{#if paraRevisar.length}
					<a
						href="/treino/?modo=revisao"
						class="btn-suave mt-5 flex min-h-11 w-full items-center justify-center gap-2 rounded-full px-4 text-sm font-bold text-accent-ink"
					>
						Revisar {paraRevisar.length} {paraRevisar.length > 1 ? 'questões' : 'questão'}
						<ArrowRight size={15} weight="bold" aria-hidden="true" />
					</a>
				{/if}
			{:else}
				<div class="flex items-center justify-between gap-2">
					<h2 class="font-display text-heading font-bold text-ink">Banco de questões</h2>
					<span class="rounded-full bg-accent-soft px-2.5 py-0.5 text-xs font-bold text-accent-ink">INEP oficial</span>
				</div>
				<p class="mt-1 text-sm text-ink-soft">
					{total} questões das provas de {listar(edicoes)}.
				</p>
				<dl class="mt-4 grid grid-cols-3 gap-2 text-center">
					<div class="rounded-2xl bg-panel px-2 py-3">
						<dd class="nums font-display text-2xl font-extrabold text-ink">{fg}</dd>
						<dt class="mt-0.5 text-xs font-medium text-ink-soft">Formação Geral</dt>
					</div>
					<div class="rounded-2xl bg-panel px-2 py-3">
						<dd class="nums font-display text-2xl font-extrabold text-ink">{ce}</dd>
						<dt class="mt-0.5 text-xs font-medium text-ink-soft">Específicas</dt>
					</div>
					<div class="rounded-2xl bg-panel px-2 py-3">
						<dd class="nums font-display text-2xl font-extrabold text-ink">{disc}</dd>
						<dt class="mt-0.5 text-xs font-medium text-ink-soft">Discursivas</dt>
					</div>
				</dl>
				{#if geradas}
					<p class="mt-4 text-xs leading-relaxed text-pretty text-ink-soft">
						Mais <strong class="font-semibold text-ink">{geradas} questões guiadas</strong> por nível de dificuldade no modo Estudo.
					</p>
				{/if}
			{/if}
		</div>
	</aside>
</div>

<!-- 2. Trilha viva de estudo (caminho visual intuitivo mapeado nos modos reais) -->
<section class="mt-10 lg:mt-12" aria-labelledby="titulo-trilha">
	<div class="flex flex-wrap items-end justify-between gap-2">
		<div>
			<h2 id="titulo-trilha" class="font-display text-title font-extrabold text-ink">Sua trilha de estudo</h2>
			<p class="mt-1 text-sm text-ink-soft">Siga na ordem ou entre direto no modo que faz sentido hoje.</p>
		</div>
	</div>

	<nav class="relative mt-5" aria-label="Trilha de estudo">
		<!-- Linha vertebral contínua conectando os nós da trilha -->
		<div
			class="pointer-events-none absolute top-7 bottom-7 left-5 w-0.5 bg-line sm:left-6"
			aria-hidden="true"
		></div>

		<ol class="space-y-3">
			{#each etapasTrilha as etapa, k (etapa.href)}
				<li class="rise relative pl-14 sm:pl-16" style="animation-delay: {k * 45}ms">
					<!-- Nó circular da trilha -->
					<span
						aria-hidden="true"
						class="absolute top-5 left-0 flex h-10 w-10 items-center justify-center rounded-full border-2 transition-transform sm:left-1 {etapa.estado === 'feito'
							? 'border-ok-solid bg-ok-solid text-white'
							: etapa.estado === 'atual'
								? 'border-accent bg-accent text-accent-on ring-4 ring-accent-soft'
								: etapa.estado === 'marco'
									? 'border-milestone bg-milestone-soft text-milestone-ink'
									: 'border-line-strong bg-card text-ink-soft'}"
					>
						{#if etapa.estado === 'feito'}
							<Check size={18} weight="bold" />
						{:else if etapa.estado === 'marco'}
							<FlagCheckered size={18} weight="bold" />
						{:else}
							<etapa.icone size={18} weight="bold" />
						{/if}
					</span>

					<a
						href={etapa.href}
						class="superficie group block rounded-3xl p-4 transition-[transform,border-color,box-shadow] duration-150 hover:-translate-y-0.5 hover:border-accent active:scale-[0.995] sm:p-5 {etapa.estado === 'atual'
							? 'border-accent-border'
							: ''}"
					>
						<div class="flex flex-wrap items-center gap-2">
							<span class="nums text-xs font-bold text-ink-soft">Etapa {etapa.passo}</span>
							{#if etapa.estado === 'atual'}
								<span class="rounded-full bg-accent-soft px-2.5 py-0.5 text-xs font-bold text-accent-ink">
									Próximo passo
								</span>
							{:else if etapa.estado === 'feito'}
								<span class="rounded-full bg-ok-bg px-2.5 py-0.5 text-xs font-bold text-ok-fg">
									Em ritmo
								</span>
							{:else if etapa.estado === 'marco'}
								<span class="rounded-full bg-milestone-soft px-2.5 py-0.5 text-xs font-bold text-milestone-ink">
									Prova completa
								</span>
							{/if}
							<span class="ml-auto text-xs font-semibold text-ink-soft">{etapa.selo}</span>
						</div>

						<div class="mt-2 flex items-center justify-between gap-4">
							<div class="min-w-0">
								<h3 class="font-display text-heading font-bold text-ink group-hover:text-accent-ink">
									{etapa.titulo}
								</h3>
								<p class="mt-1 text-sm leading-relaxed text-pretty text-ink-soft">
									{etapa.desc}
								</p>
							</div>
							<span
								class="hidden shrink-0 items-center gap-1 rounded-full bg-panel px-3.5 py-2 text-xs font-bold text-ink transition-colors group-hover:bg-accent-soft group-hover:text-accent-ink sm:inline-flex"
							>
								{etapa.cta}
								<CaretRight size={14} weight="bold" aria-hidden="true" />
							</span>
							<CaretRight
								size={20}
								weight="bold"
								class="shrink-0 text-ink-soft transition-transform group-hover:translate-x-0.5 group-hover:text-accent-ink sm:hidden"
								aria-hidden="true"
							/>
						</div>
					</a>
				</li>
			{/each}
		</ol>
	</nav>
</section>

<!-- 3. Materiais da turma (questionário do professor + guia do Matheus) -->
<section class="mt-10" aria-labelledby="titulo-turma-materiais">
	<h2 id="titulo-turma-materiais" class="font-display text-heading font-bold text-ink">Materiais da turma</h2>
	<p class="mt-0.5 text-sm text-ink-soft">Conteúdos extras compartilhados em aula — fora das estatísticas do banco oficial.</p>

	<div class="mt-3.5 grid gap-3 sm:grid-cols-2">
		<a
			href="/poo/"
			class="superficie group flex flex-col justify-between rounded-3xl p-5 transition-[transform,border-color] duration-150 hover:-translate-y-0.5 hover:border-accent active:scale-[0.995]"
		>
			<div>
				<div class="flex flex-wrap items-center gap-2">
					<span class="rounded-full bg-milestone-soft px-2.5 py-0.5 text-xs font-bold text-milestone-ink">Novo</span>
					<span class="text-xs font-medium text-ink-soft">Questionário · 28/10</span>
				</div>
				<div class="mt-3 flex items-start gap-3">
					<Code size={22} weight="bold" class="mt-0.5 shrink-0 text-accent-ink" aria-hidden="true" />
					<div class="min-w-0">
						<h3 class="font-display text-base font-bold text-ink group-hover:text-accent-ink">
							Programação Orientada a Objetos
						</h3>
						<p class="mt-1 text-sm leading-relaxed text-ink-soft">
							10 questões que o professor passou em aula, com correção no fim.
						</p>
					</div>
				</div>
			</div>
			<span class="mt-4 inline-flex items-center gap-1.5 text-sm font-bold text-accent-ink">
				Fazer o questionário <ArrowRight size={15} weight="bold" aria-hidden="true" />
			</span>
		</a>

		<a
			href="/guia/"
			class="superficie group flex flex-col justify-between rounded-3xl p-5 transition-[transform,border-color] duration-150 hover:-translate-y-0.5 hover:border-accent active:scale-[0.995]"
		>
			<div>
				<div class="flex flex-wrap items-center gap-2">
					<span class="rounded-full bg-milestone-soft px-2.5 py-0.5 text-xs font-bold text-milestone-ink">Novo</span>
					<span class="text-xs font-medium text-ink-soft">Do Matheus · 25/11</span>
				</div>
				<div class="mt-3 flex items-start gap-3">
					<BookOpen size={22} weight="bold" class="mt-0.5 shrink-0 text-accent-ink" aria-hidden="true" />
					<div class="min-w-0">
						<h3 class="font-display text-base font-bold text-ink group-hover:text-accent-ink">
							Guia de estudo do Matheus
						</h3>
						<p class="mt-1 text-sm leading-relaxed text-ink-soft">
							Resumos, folha de fórmulas, perguntas de memória e 24 + 2 questões autorais comentadas.
						</p>
					</div>
				</div>
			</div>
			<span class="mt-4 inline-flex items-center gap-1.5 text-sm font-bold text-accent-ink">
				Abrir o guia <ArrowRight size={15} weight="bold" aria-hidden="true" />
			</span>
		</a>
	</div>

	{#if pronto && total && temProgresso}
		<p class="mt-5 text-xs leading-relaxed text-pretty text-ink-soft">
			No banco oficial: {total} questões das provas de {listar(edicoes)} ({fg} de Formação Geral,
			{ce} específicas e {disc} discursivas){#if geradas}, mais {geradas} de revisão no modo Estudo{/if}.
		</p>
	{/if}
</section>
