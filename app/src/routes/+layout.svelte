<script>
	import '../app.css';
	import { page } from '$app/stores';
	import { GraduationCap } from 'phosphor-svelte';

	const links = [
		{ href: '/treino/', label: 'Treino' },
		{ href: '/estudo/', label: 'Estudo' },
		{ href: '/simulado/', label: 'Simulado' }
	];
</script>

<a href="#conteudo" class="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:rounded-lg focus:bg-white focus:px-4 focus:py-2 focus:text-sm focus:font-bold">
	Pular para o conteúdo
</a>

<header class="bg-ink text-white">
	<nav class="mx-auto flex h-16 max-w-3xl items-center gap-1 px-4" aria-label="Principal">
		<a href="/" class="mr-3 flex items-center gap-2">
			<span class="flex h-9 w-9 items-center justify-center rounded-xl bg-accent" aria-hidden="true">
				<GraduationCap size={22} weight="bold" color="#fff" aria-hidden="true" />
			</span>
			<span class="leading-tight">
				<span class="block text-[15px] font-bold tracking-tight">Simulado ENADE</span>
				<span class="block text-[11px] font-medium text-slate-300">Eng. de Computação</span>
			</span>
		</a>
		<span class="flex-1"></span>
		{#each links as l (l.href)}
			<a
				href={l.href}
				aria-current={$page.url.pathname === l.href ? 'page' : undefined}
				class="rounded-lg px-3 py-2 text-sm font-semibold transition-colors hover:bg-white/10 active:scale-[0.97] {$page.url.pathname === l.href
					? 'bg-white/15 text-white'
					: 'text-slate-300'}"
			>
				{l.label}
			</a>
		{/each}
	</nav>
</header>

<main id="conteudo" class="mx-auto max-w-3xl px-4 pt-6 pb-16">
	<slot />
</main>

<footer class="border-t border-slate-300/70">
	<p class="mx-auto max-w-3xl px-4 py-5 text-xs text-ink-soft">
		Questões oficiais do INEP (ENADE Engenharia de Computação) + simulado da turma. Feito para
		estudar — sem conta, sem servidor, seu progresso fica no seu aparelho.
	</p>
</footer>
