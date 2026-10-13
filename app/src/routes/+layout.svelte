<script>
	import '../app.css';
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { GraduationCap, Infinity as InfinityIcon, Moon, Stairs, Sun, Timer } from 'phosphor-svelte';
	import { alternarTema, iniciarTema, temaAtual } from '$lib/tema.js';

	const tabs = [
		{ href: '/treino/', label: 'Treino', icone: InfinityIcon },
		{ href: '/estudo/', label: 'Estudo', icone: Stairs },
		{ href: '/simulado/', label: 'Simulado', icone: Timer }
	];

	// no fluxo de questão a tela é dona da parte de baixo (CTA fixo) —
	// a tab bar só aparece fora do quiz, e só no mobile
	let emQuiz = $derived(
		$page.url.pathname.startsWith('/treino/') || $page.url.pathname.startsWith('/estudo/')
	);

	let { children } = $props();

	let escuro = $state(false);
	onMount(() => {
		iniciarTema();
		escuro = temaAtual() === 'dark';
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
		<a href="/" class="mr-2 flex items-center gap-2">
			<span class="flex h-9 w-9 items-center justify-center rounded-xl bg-accent" aria-hidden="true">
				<GraduationCap size={22} weight="bold" class="text-white" aria-hidden="true" />
			</span>
			<span class="leading-tight">
				<span class="block font-display text-[15px] font-bold tracking-tight">Simulado ENADE</span>
				<span class="block text-[11px] font-medium text-bar-fg">Eng. de Computação</span>
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
				<p class="font-display text-sm font-extrabold tracking-tight">Simulado ENADE</p>
				<p class="mt-1 text-xs leading-relaxed text-pretty text-ink-soft">
					Estudo para a prova com questões oficiais do INEP. Sem conta, sem servidor.
				</p>
			</div>
			<nav aria-label="Modos">
				<p class="text-label font-bold text-ink-soft uppercase">Modos</p>
				<ul class="mt-2 space-y-1 text-sm font-semibold">
					<li><a href="/treino/" class="hover:text-accent-ink">Treino livre</a></li>
					<li><a href="/estudo/" class="hover:text-accent-ink">Estudo por níveis</a></li>
					<li><a href="/simulado/" class="hover:text-accent-ink">Simulado real</a></li>
				</ul>
			</nav>
			<div>
				<p class="text-label font-bold text-ink-soft uppercase">Fonte</p>
				<p class="mt-2 text-xs leading-relaxed text-pretty text-ink-soft">
					Provas ENADE Engenharia de Computação (INEP) + simulado da turma. Formato 2026:
					Portaria INEP nº 161.
				</p>
				<p class="mt-2 font-code text-label text-ink-soft" aria-hidden="true">
					REV A · GERADO DE PROVAS INEP · 2014/2017/2019/2023
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
					class="flex min-h-[60px] flex-1 flex-col items-center justify-center gap-1 py-2 text-xs font-bold transition-colors active:scale-[0.97] {$page.url.pathname ===
					t.href
						? 'text-accent-ink'
						: 'text-ink-soft'}"
				>
					<t.icone size={24} weight="bold" aria-hidden="true" />
					{t.label}
				</a>
			{/each}
		</div>
	</nav>
	<div class="h-20 sm:hidden" aria-hidden="true"></div>
{/if}
