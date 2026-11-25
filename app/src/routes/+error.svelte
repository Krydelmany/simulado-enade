<script>
	import { ArrowLeft, MagnifyingGlass } from 'phosphor-svelte';
</script>

<div class="folha mx-auto max-w-md rounded-3xl p-8 text-center">
	<MagnifyingGlass size={34} weight="bold" class="mx-auto text-accent-ink" aria-hidden="true" />
	<h1 class="mt-4 font-display text-2xl font-extrabold tracking-tight text-ink">Página não encontrada</h1>
	<p class="mx-auto mt-2 max-w-[38ch] text-sm text-ink-soft">
		Esse endereço não existe por aqui. Volte ao início e escolha uma etapa da sua trilha.
	</p>
	<a
		href="/"
		class="btn-primario mt-6 inline-flex min-h-11 items-center gap-2 rounded-full px-6 text-sm font-bold"
	>
		<ArrowLeft size={16} weight="bold" aria-hidden="true" /> Voltar ao início
	</a>
</div>
