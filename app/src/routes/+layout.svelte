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
	// dos dois está ativo.
	let rotaAtual = $derived($page.url.pathname);
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

	let emQuiz = $derived(
		$page.url.pathname.startsWith('/treino/') ||
			$page.url.pathname.startsWith('/estudo/') ||
			foco.quiz
	);

	let menuAberto = $state(false);
	let cabecalho = $state(null);

	let { children } = $props();

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
	class="sticky top-0 z-40 border-b border-line bg-card/90 text-ink backdrop-blur-md"
>
	<nav
		class="mx-auto flex h-16 w-full max-w-3xl items-center gap-1 px-4 lg:max-w-5xl"
		aria-label="Principal"
	>
		<a
			href="/"
			class="group mr-2 flex items-center gap-2.5 rounded-xl py-1 pr-2 transition-opacity hover:opacity-90"
		>
			<Marca tamanho={28} />
			<span class="leading-tight">
				<span class="block font-display text-[15px] font-bold tracking-tight text-ink">
					Simulado ENADE
				</span>
				<span class="block text-[11px] font-medium text-ink-soft">{curso.nomeCurto}</span>
			</span>
		</a>
		<span class="flex-1"></span>
		{#each tabs as t (t.href)}
			<a
				href={t.href}
				aria-current={abaAtiva(t) ? 'page' : undefined}
				class="hidden items-center gap-1.5 rounded-full px-3 py-2 text-sm font-semibold transition-colors active:scale-[0.98] md:flex {abaAtiva(
					t
				)
					? 'bg-accent-soft text-accent-ink'
					: 'text-ink-soft hover:bg-tile hover:text-ink'}"
			>
				<t.icone size={16} weight={abaAtiva(t) ? 'fill' : 'bold'} aria-hidden="true" />
				{t.label}
			</a>
		{/each}
		{#if nuvemLigada}
			<a
				href="/conta/"
				aria-label="Conta e turma"
				aria-current={$page.url.pathname === '/conta/' ? 'page' : undefined}
				class="flex h-11 min-h-11 min-w-11 items-center justify-center rounded-full transition-colors active:scale-95 {$page.url.pathname === '/conta/'
					? 'bg-accent-soft text-accent-ink'
					: 'text-ink-soft hover:bg-tile hover:text-ink'}"
			>
				<UserCircle size={22} weight="bold" aria-hidden="true" />
			</a>
		{/if}
		<button
			type="button"
			onclick={trocar}
			aria-label={escuro ? 'Usar modo claro' : 'Usar modo escuro'}
			aria-pressed={escuro}
			class="flex h-11 min-h-11 min-w-11 items-center justify-center rounded-full text-ink-soft transition-colors hover:bg-tile hover:text-ink active:scale-95"
		>
			{#if escuro}
				<Sun size={20} weight="bold" aria-hidden="true" />
			{:else}
				<Moon size={20} weight="bold" aria-hidden="true" />
			{/if}
		</button>
		<button
			type="button"
			onclick={() => (menuAberto = !menuAberto)}
			aria-expanded={menuAberto}
			aria-controls="menu-mobile"
			aria-label={menuAberto ? 'Fechar menu' : 'Abrir menu'}
			class="flex h-11 min-h-11 min-w-11 items-center justify-center rounded-full text-ink-soft transition-colors hover:bg-tile hover:text-ink active:scale-95 md:hidden"
		>
			{#if menuAberto}
				<X size={21} weight="bold" aria-hidden="true" />
			{:else}
				<List size={21} weight="bold" aria-hidden="true" />
			{/if}
		</button>
	</nav>

	{#if menuAberto}
		<div
			id="menu-mobile"
			class="absolute inset-x-0 top-full z-50 border-b border-line bg-card text-ink shadow-xl md:hidden"
			in:fly={{ y: -8, duration: DUR }}
			out:fade={{ duration: DUR }}
		>
			<nav class="mx-auto flex w-full max-w-3xl flex-col gap-1 px-4 py-3" aria-label="Menu">
				{#each tabs as t (t.href)}
					<a
						href={t.href}
						aria-current={abaAtiva(t) ? 'page' : undefined}
						class="flex min-h-12 items-center gap-3 rounded-2xl px-3.5 text-base font-semibold transition-colors active:scale-[0.99] {abaAtiva(
							t
						)
							? 'bg-accent-soft text-accent-ink'
							: 'text-ink-soft hover:bg-tile hover:text-ink'}"
					>
						<t.icone size={20} weight={abaAtiva(t) ? 'fill' : 'bold'} aria-hidden="true" />
						{t.label}
					</a>
				{/each}
				<div class="my-1.5 border-t border-line"></div>
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

<main id="conteudo" class="mx-auto w-full max-w-3xl px-4 pt-6 pb-12 lg:max-w-5xl">
	{@render children()}
</main>

{#if !emQuiz}
	<footer class="border-t border-line bg-card/60">
		<div class="mx-auto grid w-full max-w-3xl gap-8 px-4 py-10 sm:grid-cols-3 lg:max-w-5xl">
			<div>
				<p class="flex items-center gap-2 font-display text-sm font-bold tracking-tight text-ink">
					<Marca tamanho={22} /> Simulado ENADE
				</p>
				<p class="mt-2 text-xs leading-relaxed text-pretty text-ink-soft">
					Estudo guiado para a prova com questões oficiais do INEP.
					{nuvemLigada ? 'Conta só se você quiser entrar numa turma.' : 'Sem conta, sem servidor.'}
				</p>
			</div>
			<nav aria-label="Modos">
				<p class="text-label font-bold text-ink-soft">Estudo</p>
				<ul class="mt-2.5 space-y-1.5 text-sm font-medium">
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
				<p class="text-label font-bold text-ink-soft">Fonte oficial</p>
				<p class="mt-2.5 text-xs leading-relaxed text-pretty text-ink-soft">
					Provas de {curso.nome} do INEP de 2014, 2017, 2019 e 2023. Formato 2026: Portaria INEP nº 161.
				</p>
			</div>
		</div>
	</footer>
{/if}

<!-- Aviso de DevTools aberto. Fica fora do fluxo e depois do rodapé. -->
<VigiaDevTools />
<!-- Voltar puxando da borda, para aparelho sem esse gesto no sistema. -->
<BordaVoltar ativo={emQuiz} />
