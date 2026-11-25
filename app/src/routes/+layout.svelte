<script>
	import '../app.css';
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import { afterNavigate } from '$app/navigation';
	import { page } from '$app/stores';
	import { fade, fly } from 'svelte/transition';
	import {
		BookOpen,
		FileText,
		Infinity as InfinityIcon,
		List,
		Lock,
		Moon,
		NotePencil,
		Stairs,
		Sun,
		Timer,
		UserCircle,
		X
	} from 'phosphor-svelte';
	import { alternarTema, aoMudarTema, iniciarTema, temaAtual } from '$lib/tema.js';
	import { aplicarCurso, cursoAtual } from '$lib/curso.js';
	import { DUR } from '$lib/motion.js';
	import VigiaDevTools from '$lib/VigiaDevTools.svelte';
	import BordaVoltar from '$lib/BordaVoltar.svelte';
	import { foco } from '$lib/foco.svelte.js';
	import { iniciarNuvem, nuvemLigada, registrarVisita } from '$lib/nuvem.js';
	import Marca from '$lib/Marca.svelte';

	const curso = cursoAtual();

	const tabs = [
		{ href: '/treino/', label: 'Treino', icone: InfinityIcon },
		{ href: '/estudo/', label: 'Estudo', icone: Stairs },
		{ href: '/treino/?modo=discursivas', label: 'Discursivas', icone: NotePencil },
		{ href: '/guia/', label: 'Guia', icone: BookOpen },
		{ href: '/simulado/', label: 'Simulado', icone: Timer }
	];

	// "Discursivas" é um modo dentro de /treino/ — a aba precisa saber qual
	// dos dois está ativo (antes, as duas ficariam apagadas ou acesas juntas).
	let rotaAtual = $derived($page.url.pathname);
	// A query lança no prerender (o build não conhece a busca); no servidor a
	// aba fica sem destaque e o navegador corrige ao hidratar.
	let modoTreino = $derived(
		browser && rotaAtual === '/treino/'
			? (new URLSearchParams($page.url.search).get('modo') ?? '')
			: null
	);
	function abaAtiva(t) {
		if (t.href === '/treino/?modo=discursivas') return modoTreino === 'discursivas';
		if (t.href === '/treino/') return modoTreino !== null && modoTreino !== 'discursivas';
		return rotaAtual === t.href;
	}

	// No quiz, o rodapé e a borda de voltar são a tela; a ação é inline, então
	// não existe barra fixa nem pb-32 reservado para ela.
	let emQuiz = $derived(
		$page.url.pathname.startsWith('/treino/') ||
			$page.url.pathname.startsWith('/estudo/') ||
			foco.quiz
	);

	// menu mobile; `cabecalho` serve para fechar ao toque fora.
	let menuAberto = $state(false);
	let cabecalho = $state(null);

	let { children } = $props();

	// no quiz, puxar a página para baixo no topo recarregava (pull-to-refresh
	// do Chrome Android) e tirava o aluno da questão — ver `.sem-recarregar`
	$effect(() => {
		document.documentElement.classList.toggle('sem-recarregar', emQuiz);
		return () => document.documentElement.classList.remove('sem-recarregar');
	});

	let escuro = $state(false);
	onMount(() => {
		aplicarCurso(curso.id);
		iniciarTema();
		escuro = temaAtual() === 'dark';
		const pararTema = aoMudarTema((modo) => {
			escuro = modo === 'dark';
		});
		// sem Supabase configurado no build, não faz nada (site 100% local)
		const pararNuvem = iniciarNuvem();
		return () => {
			pararTema?.();
			pararNuvem?.();
		};
	});

	afterNavigate(({ to }) => {
		menuAberto = false;
		if (to?.url) registrarVisita(to.url);
	});

	function trocar() {
		escuro = alternarTema() === 'dark';
	}

	function fecharFora(e) {
		if (menuAberto && cabecalho && !cabecalho.contains(e.target)) menuAberto = false;
	}

	function aoTecla(e) {
		if (e.key === 'Escape' && menuAberto) menuAberto = false;
	}
</script>

<svelte:window onpointerdown={fecharFora} onkeydown={aoTecla} />

<a
	href="#conteudo"
	class="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:rounded-xl focus:bg-accent focus:px-4 focus:py-2 focus:text-sm focus:font-bold focus:text-accent-on"
>
	Pular para o conteúdo
</a>

<header
	bind:this={cabecalho}
	class="sticky top-0 z-40 border-b border-line/80 bg-paper/88 text-ink backdrop-blur-lg"
>
	<nav
		class="mx-auto flex h-16 w-full max-w-3xl items-center gap-2 px-4 md:h-[4.5rem] lg:max-w-5xl"
		aria-label="Principal"
	>
		<a
			href="/"
			aria-current={rotaAtual === '/' ? 'page' : undefined}
			class="group flex min-h-11 items-center gap-2.5 rounded-2xl py-1 pr-2 transition-transform duration-150 active:scale-[0.98]"
		>
			<Marca tamanho={32} />
			<span class="leading-tight">
				<span class="block font-display text-[15px] font-extrabold tracking-tight text-ink">
					Simulado ENADE
				</span>
				<span class="block text-xs font-semibold text-ink-soft">{curso.nomeCurto}</span>
			</span>
		</a>

		<span class="flex-1"></span>

		<!-- Barra de navegação tátil no desktop -->
		<div
			class="hidden items-center gap-1 rounded-full border border-line bg-card/95 p-1 shadow-[inset_0_1px_0_var(--card-top),0_2.5px_0_0_var(--surface-lip)] md:flex"
		>
			{#each tabs as t (t.href)}
				{@const ativa = abaAtiva(t)}
				<a
					href={t.href}
					aria-current={ativa ? 'page' : undefined}
					class="inline-flex min-h-11 items-center gap-1.5 rounded-full px-2.5 py-2 text-[13px] font-bold transition-[transform,background-color,color,box-shadow] duration-150 active:translate-y-px lg:px-3.5 lg:text-sm {ativa
						? 'bg-accent text-accent-on shadow-[0_2px_0_0_var(--accent-lip)]'
						: 'text-ink-soft hover:bg-tile/80 hover:text-ink'}"
				>
					<t.icone size={15} weight={ativa ? 'fill' : 'bold'} aria-hidden="true" />
					{t.label}
				</a>
			{/each}
		</div>

		<span class="hidden flex-1 lg:block"></span>

		<div class="flex items-center gap-2">
			{#if nuvemLigada}
				<a
					href="/conta/"
					aria-label="Conta e turma"
					aria-current={$page.url.pathname === '/conta/' ? 'page' : undefined}
					class="btn-icone flex h-11 w-11 items-center justify-center rounded-full {$page.url.pathname ===
					'/conta/'
						? 'border-accent-border bg-accent-soft text-accent-ink'
						: ''}"
				>
					<UserCircle size={21} weight="bold" aria-hidden="true" />
				</a>
			{/if}
			<button
				type="button"
				onclick={trocar}
				aria-label={escuro ? 'Usar modo claro' : 'Usar modo escuro'}
				aria-pressed={escuro}
				class="btn-icone group/tema flex h-11 w-11 items-center justify-center rounded-full"
			>
				{#if escuro}
					<Sun
						size={20}
						weight="bold"
						class="transition-transform duration-200 group-hover/tema:rotate-45"
						aria-hidden="true"
					/>
				{:else}
					<Moon
						size={19}
						weight="bold"
						class="transition-transform duration-200 group-hover/tema:-rotate-12"
						aria-hidden="true"
					/>
				{/if}
			</button>
			<button
				type="button"
				onclick={() => (menuAberto = !menuAberto)}
				aria-expanded={menuAberto}
				aria-controls="menu-mobile"
				aria-label={menuAberto ? 'Fechar menu' : 'Abrir menu'}
				class="btn-icone flex h-11 w-11 items-center justify-center rounded-full md:hidden {menuAberto
					? 'border-accent-border bg-accent-soft text-accent-ink'
					: ''}"
			>
				{#if menuAberto}
					<X size={20} weight="bold" aria-hidden="true" />
				{:else}
					<List size={20} weight="bold" aria-hidden="true" />
				{/if}
			</button>
		</div>
	</nav>

	{#if menuAberto}
		<div
			id="menu-mobile"
			class="absolute inset-x-0 top-full z-50 px-3 pt-2 md:hidden"
			in:fly={{ y: -8, duration: DUR }}
			out:fade={{ duration: DUR }}
		>
			<nav
				class="folha mx-auto flex w-full max-w-3xl flex-col gap-1 rounded-3xl p-2.5 text-ink"
				aria-label="Menu"
			>
				{#each tabs as t (t.href)}
					{@const ativa = abaAtiva(t)}
					<a
						href={t.href}
						aria-current={ativa ? 'page' : undefined}
						class="flex min-h-12 items-center gap-3 rounded-2xl px-3.5 text-base font-bold transition-[transform,background-color,color] duration-150 active:scale-[0.985] {ativa
							? 'bg-accent text-accent-on shadow-[0_2.5px_0_0_var(--accent-lip)]'
							: 'text-ink hover:bg-tile'}"
					>
						<t.icone
							size={20}
							weight={ativa ? 'fill' : 'bold'}
							class={ativa ? '' : 'text-accent-ink'}
							aria-hidden="true"
						/>
						{t.label}
					</a>
				{/each}
				<div class="my-1 border-t border-line"></div>
				{#if nuvemLigada}
					<a
						href="/conta/"
						aria-current={$page.url.pathname === '/conta/' ? 'page' : undefined}
						class="flex min-h-12 items-center gap-3 rounded-2xl px-3.5 text-base font-semibold transition-colors active:scale-[0.99] {$page.url.pathname ===
						'/conta/'
							? 'bg-accent-soft text-accent-ink'
							: 'text-ink-soft hover:bg-tile hover:text-ink'}"
					>
						<UserCircle size={20} weight="bold" aria-hidden="true" />
						Conta e turma
					</a>
					<a
						href="/desempenho/"
						aria-current={$page.url.pathname === '/desempenho/' ? 'page' : undefined}
						class="flex min-h-12 items-center gap-3 rounded-2xl px-3.5 text-base font-semibold transition-colors active:scale-[0.99] {$page.url.pathname ===
						'/desempenho/'
							? 'bg-accent-soft text-accent-ink'
							: 'text-ink-soft hover:bg-tile hover:text-ink'}"
					>
						<FileText size={20} weight="bold" aria-hidden="true" />
						Simulado em papel
					</a>
				{/if}
				<a
					href="/privacidade/"
					aria-current={$page.url.pathname === '/privacidade/' ? 'page' : undefined}
					class="flex min-h-12 items-center gap-3 rounded-2xl px-3.5 text-base font-semibold transition-colors active:scale-[0.99] {$page.url.pathname ===
					'/privacidade/'
						? 'bg-accent-soft text-accent-ink'
						: 'text-ink-soft hover:bg-tile hover:text-ink'}"
				>
					<Lock size={20} weight="bold" aria-hidden="true" />
					Privacidade
				</a>
			</nav>
		</div>
	{/if}
</header>

<main id="conteudo" class="mx-auto w-full max-w-3xl px-4 pt-5 pb-12 lg:max-w-5xl lg:pt-7">
	{@render children()}
</main>

{#if !emQuiz}
	<footer class="border-t border-line/80 bg-card/70">
		<div class="mx-auto grid w-full max-w-3xl gap-7 px-4 py-9 sm:grid-cols-3 lg:max-w-5xl">
			<div>
				<p class="flex items-center gap-2 font-display text-sm font-extrabold tracking-tight text-ink">
					<Marca tamanho={22} interativo={false} /> Simulado ENADE
				</p>
				<p class="mt-2 text-xs leading-relaxed text-pretty text-ink-soft">
					Prática interativa com questões oficiais do INEP.
					{nuvemLigada ? 'Conta opcional para entrar em turma.' : 'Tudo salvo direto no aparelho.'}
				</p>
			</div>
			<nav aria-label="Modos">
				<p class="text-label font-bold text-ink-soft">Atalhos</p>
				<ul class="mt-2.5 grid grid-cols-2 gap-x-4 gap-y-1.5 text-sm font-medium sm:grid-cols-1">
					<li><a href="/treino/" class="text-ink hover:text-accent-ink">Treino livre</a></li>
					<li><a href="/estudo/" class="text-ink hover:text-accent-ink">Estudo por níveis</a></li>
					<li><a href="/treino/?modo=discursivas" class="text-ink hover:text-accent-ink">Discursivas do CE</a></li>
					<li><a href="/poo/" class="text-ink hover:text-accent-ink">Questionário de POO</a></li>
					<li><a href="/guia/" class="text-ink hover:text-accent-ink">Guia do Matheus</a></li>
					<li><a href="/simulado/" class="text-ink hover:text-accent-ink">Simulado real</a></li>
					{#if nuvemLigada}
						<li><a href="/conta/" class="text-ink hover:text-accent-ink">Conta e turma</a></li>
						<li><a href="/desempenho/" class="text-ink hover:text-accent-ink">Simulado em papel</a></li>
					{/if}
					<li><a href="/privacidade/" class="text-ink hover:text-accent-ink">Privacidade</a></li>
				</ul>
			</nav>
			<div>
				<p class="text-label font-bold text-ink-soft">Base oficial</p>
				<p class="mt-2.5 text-xs leading-relaxed text-pretty text-ink-soft">
					Provas de {curso.nome} do INEP de 2014, 2017, 2019 e 2023. Formato 2026: Portaria INEP nº 161.
				</p>
			</div>
		</div>
	</footer>
{/if}

<!-- Aviso de DevTools aberto. Fica fora do fluxo e depois do rodapé: é a
     última coisa da página, e só aparece quando o sinal dispara. -->
<VigiaDevTools />
<!-- Voltar puxando da borda, para aparelho sem esse gesto no sistema. -->
<BordaVoltar ativo={emQuiz} />
