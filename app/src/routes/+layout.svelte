<script>
	import '../app.css';
	import { onMount } from 'svelte';
	import { afterNavigate } from '$app/navigation';
	import { page } from '$app/stores';
	import { fade, fly } from 'svelte/transition';
	import {
		FileText,
		Infinity as InfinityIcon,
		List,
		Lock,
		Moon,
		Stairs,
		Sun,
		Timer,
		UserCircle,
		X
	} from 'phosphor-svelte';
	import { alternarTema, iniciarTema, temaAtual } from '$lib/tema.js';
	import { DUR } from '$lib/motion.js';
	import VigiaDevTools from '$lib/VigiaDevTools.svelte';
	import BordaVoltar from '$lib/BordaVoltar.svelte';
	import { foco } from '$lib/foco.svelte.js';
	import { iniciarNuvem, nuvemLigada, registrarVisita } from '$lib/nuvem.js';
	import Marca from '$lib/Marca.svelte';

	const tabs = [
		{ href: '/treino/', label: 'Treino', icone: InfinityIcon },
		{ href: '/estudo/', label: 'Estudo', icone: Stairs },
		{ href: '/simulado/', label: 'Simulado', icone: Timer }
	];

	// No quiz, o rodapé e a borda de voltar são a tela; a ação é inline, então
	// não existe mais barra fixa nem pb-32 reservado para ela.
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
		iniciarTema();
		escuro = temaAtual() === 'dark';
		// sem Supabase configurado no build, não faz nada (site 100% local)
		return iniciarNuvem();
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

<a href="#conteudo" class="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:rounded-lg focus:bg-accent focus:px-4 focus:py-2 focus:text-sm focus:font-bold focus:text-white">
	Pular para o conteúdo
</a>

<header bind:this={cabecalho} class="sticky top-0 z-40 bg-bar text-white">
	<nav class="mx-auto flex h-16 w-full max-w-3xl items-center gap-1 px-4 lg:max-w-5xl" aria-label="Principal">
		<a href="/" class="mr-2 flex items-center gap-2.5">
			<Marca tamanho={30} />
			<span class="leading-tight">
				<span class="block font-display text-[15px] font-bold tracking-tight">Simulado ENADE</span>
				<span class="block text-xs font-medium text-bar-fg">Eng. de Computação</span>
			</span>
		</a>
		<span class="flex-1"></span>
		{#each tabs as t (t.href)}
			<a
				href={t.href}
				aria-current={$page.url.pathname === t.href ? 'page' : undefined}
				class="hidden items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-semibold transition-colors hover:bg-white/10 active:scale-[0.97] sm:flex {$page.url.pathname ===
				t.href
					? 'bg-white/15 text-white'
					: 'text-bar-fg'}"
			>
				<t.icone size={17} weight="bold" aria-hidden="true" />
				{t.label}
			</a>
		{/each}
		{#if nuvemLigada}
			<a
				href="/conta/"
				aria-label="Conta e turma"
				aria-current={$page.url.pathname === '/conta/' ? 'page' : undefined}
				class="flex h-11 min-h-11 min-w-11 items-center justify-center rounded-xl transition-colors hover:bg-white/10 active:scale-95 {$page.url.pathname === '/conta/' ? 'bg-white/15' : ''}"
			>
				<UserCircle size={22} weight="bold" aria-hidden="true" />
			</a>
		{/if}
		<button
			type="button"
			onclick={trocar}
			aria-label={escuro ? 'Usar modo claro' : 'Usar modo escuro'}
			aria-pressed={escuro}
			class="flex h-11 min-h-11 min-w-11 items-center justify-center rounded-xl transition-colors hover:bg-white/10 active:scale-95"
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
			class="flex h-11 min-h-11 min-w-11 items-center justify-center rounded-xl transition-colors hover:bg-white/10 active:scale-95 sm:hidden"
		>
			{#if menuAberto}
				<X size={22} weight="bold" aria-hidden="true" />
			{:else}
				<List size={22} weight="bold" aria-hidden="true" />
			{/if}
		</button>
	</nav>

	{#if menuAberto}
		<div
			id="menu-mobile"
			class="absolute inset-x-0 top-full z-50 border-t border-white/10 bg-bar text-white shadow-[0_18px_30px_-18px_rgba(0,0,0,0.75)] sm:hidden"
			in:fly={{ y: -8, duration: DUR }}
			out:fade={{ duration: DUR }}
		>
			<nav class="mx-auto flex w-full max-w-3xl flex-col gap-1 px-4 py-3" aria-label="Menu">
				{#each tabs as t (t.href)}
					<a
						href={t.href}
						aria-current={$page.url.pathname === t.href ? 'page' : undefined}
						class="flex min-h-12 items-center gap-3 rounded-xl px-3 text-base font-bold transition-colors active:scale-[0.99] {$page.url.pathname ===
						t.href
							? 'bg-white/15'
							: 'text-bar-fg hover:bg-white/10 hover:text-white'}"
					>
						<t.icone size={20} weight="bold" aria-hidden="true" />
						{t.label}
					</a>
				{/each}
				<div class="my-1 border-t border-white/10"></div>
				{#if nuvemLigada}
					<a
						href="/conta/"
						aria-current={$page.url.pathname === '/conta/' ? 'page' : undefined}
						class="flex min-h-12 items-center gap-3 rounded-xl px-3 text-base font-bold transition-colors active:scale-[0.99] {$page.url.pathname ===
						'/conta/'
							? 'bg-white/15'
							: 'text-bar-fg hover:bg-white/10 hover:text-white'}"
					>
						<UserCircle size={20} weight="bold" aria-hidden="true" />
						Conta e turma
					</a>
					<a
						href="/desempenho/"
						aria-current={$page.url.pathname === '/desempenho/' ? 'page' : undefined}
						class="flex min-h-12 items-center gap-3 rounded-xl px-3 text-base font-bold transition-colors active:scale-[0.99] {$page.url.pathname ===
						'/desempenho/'
							? 'bg-white/15'
							: 'text-bar-fg hover:bg-white/10 hover:text-white'}"
					>
						<FileText size={20} weight="bold" aria-hidden="true" />
						Simulado em papel
					</a>
				{/if}
				<a
					href="/privacidade/"
					aria-current={$page.url.pathname === '/privacidade/' ? 'page' : undefined}
					class="flex min-h-12 items-center gap-3 rounded-xl px-3 text-base font-bold transition-colors active:scale-[0.99] {$page.url.pathname ===
					'/privacidade/'
						? 'bg-white/15'
						: 'text-bar-fg hover:bg-white/10 hover:text-white'}"
				>
					<Lock size={20} weight="bold" aria-hidden="true" />
					Privacidade
				</a>
			</nav>
		</div>
	{/if}
</header>

<main id="conteudo" class="mx-auto w-full max-w-3xl px-4 pt-6 pb-10 lg:max-w-5xl">
	{@render children()}
</main>

{#if !emQuiz}
	<footer class="border-t border-line">
		<div class="mx-auto grid w-full max-w-3xl gap-8 px-4 py-10 sm:grid-cols-3 lg:max-w-5xl">
			<div>
				<p class="flex items-center gap-2 font-display text-sm font-extrabold tracking-tight">
					<Marca tamanho={22} /> Simulado ENADE
				</p>
				<p class="mt-1 text-xs leading-relaxed text-pretty text-ink-soft">
					Estudo para a prova com questões oficiais do INEP.
					{nuvemLigada ? 'Conta só se você quiser entrar numa turma.' : 'Sem conta, sem servidor.'}
				</p>
			</div>
			<nav aria-label="Modos">
				<p class="text-label font-bold text-ink-soft">Modos</p>
				<ul class="mt-2 space-y-1 text-sm font-semibold">
					<li><a href="/treino/" class="hover:text-accent-ink">Treino livre</a></li>
					<li><a href="/estudo/" class="hover:text-accent-ink">Estudo por níveis</a></li>
					<li><a href="/simulado/" class="hover:text-accent-ink">Simulado real</a></li>
					{#if nuvemLigada}
						<li><a href="/conta/" class="hover:text-accent-ink">Conta e turma</a></li>
						<li><a href="/desempenho/" class="hover:text-accent-ink">Simulado em papel</a></li>
					{/if}
					<li><a href="/privacidade/" class="hover:text-accent-ink">Privacidade</a></li>
				</ul>
			</nav>
			<div>
				<p class="text-label font-bold text-ink-soft">Fonte</p>
				<p class="mt-2 text-xs leading-relaxed text-pretty text-ink-soft">
					Provas de Engenharia de Computação do INEP de 2014, 2017, 2019 e 2023. Formato
					2026: Portaria INEP nº 161.
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
