<script>
	import '../app.css';
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { Infinity as InfinityIcon, Moon, Stairs, Sun, Timer, UserCircle } from 'phosphor-svelte';
	import { alternarTema, iniciarTema, temaAtual } from '$lib/tema.js';
	import VigiaDevTools from '$lib/VigiaDevTools.svelte';
	import BordaVoltar from '$lib/BordaVoltar.svelte';
	import { foco } from '$lib/foco.svelte.js';
	import { iniciarNuvem, nuvemLigada } from '$lib/nuvem.js';
	import Marca from '$lib/Marca.svelte';

	const tabs = [
		{ href: '/treino/', label: 'Treino', icone: InfinityIcon },
		{ href: '/estudo/', label: 'Estudo', icone: Stairs },
		{ href: '/simulado/', label: 'Simulado', icone: Timer }
	];

	// no fluxo de questão a tela é dona da parte de baixo (CTA fixo) —
	// a tab bar só aparece fora do quiz, e só no mobile
	let emQuiz = $derived(
		$page.url.pathname.startsWith('/treino/') ||
			$page.url.pathname.startsWith('/estudo/') ||
			foco.quiz
	);

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

	function trocar() {
		escuro = alternarTema() === 'dark';
	}
</script>

<a href="#conteudo" class="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:rounded-lg focus:bg-accent focus:px-4 focus:py-2 focus:text-sm focus:font-bold focus:text-white">
	Pular para o conteúdo
</a>

<header class="bg-bar text-white">
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
				class="hidden rounded-lg px-3 py-2 text-sm font-semibold transition-colors hover:bg-white/10 active:scale-[0.97] sm:block {$page.url.pathname ===
				t.href
					? 'bg-white/15 text-white'
					: 'text-bar-fg'}"
			>
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
	</nav>
</header>

<main id="conteudo" class="mx-auto w-full max-w-3xl px-4 pt-6 lg:max-w-5xl {emQuiz ? 'pb-32' : 'pb-10'}">
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
					{/if}
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
	<nav
		class="fixed inset-x-0 bottom-0 z-30 border-t border-line bg-card sm:hidden"
		style="padding-bottom: env(safe-area-inset-bottom);"
		aria-label="Modos de estudo"
	>
		<div class="mx-auto flex max-w-md">
			{#each tabs as t (t.href)}
				<a
					href={t.href}
					aria-current={$page.url.pathname === t.href ? 'page' : undefined}
					class="relative flex min-h-[60px] flex-1 flex-col items-center justify-center gap-1 py-2 text-xs font-bold transition-colors active:scale-[0.97] {$page.url.pathname ===
					t.href
						? 'text-accent-ink'
						: 'text-ink-soft'}"
				>
					{#if $page.url.pathname === t.href}
						<!-- traço de caneta sobre a aba ativa: a cor sozinha não basta para quem não distingue azul -->
						<span class="absolute top-0 h-[3px] w-10 rounded-b-full bg-accent" aria-hidden="true"></span>
					{/if}
					<t.icone size={24} weight="bold" aria-hidden="true" />
					{t.label}
				</a>
			{/each}
		</div>
	</nav>
	<div class="h-20 sm:hidden" aria-hidden="true"></div>
{/if}

<!-- Aviso de DevTools aberto. Fica fora do fluxo e depois do rodapé: é a
     última coisa da página, e só aparece quando o sinal dispara. -->
<VigiaDevTools />
<!-- Voltar puxando da borda, para aparelho sem esse gesto no sistema. -->
<BordaVoltar ativo={emQuiz} />
