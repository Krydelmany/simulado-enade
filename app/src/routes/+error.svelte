<script>
	import { ArrowLeft, MagnifyingGlass } from 'phosphor-svelte';
</script>

<div class="py-10 text-center">
	<p class="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-ink">
		<MagnifyingGlass size={26} weight="bold" color="#fff" />
	</p>
	<h1 class="mt-4 text-2xl font-extrabold tracking-tight">Página não encontrada</h1>
	<p class="mx-auto mt-2 max-w-[40ch] text-sm text-ink-soft">
		Esse endereço não existe por aqui. Volte ao início e escolha um modo de estudo.
	</p>
	<a
		href="/"
		class="mt-5 inline-flex items-center gap-2 rounded-xl bg-ink px-5 py-3 text-sm font-bold text-white transition-transform active:scale-[0.98]"
	>
		<ArrowLeft size={17} weight="bold" aria-hidden="true" /> Voltar ao início
	</a>
</div>
