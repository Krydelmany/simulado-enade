<script>
	import { onMount } from 'svelte';
	import { carregarBanco } from '$lib/banco.js';
	import { ArrowLeft, LockKey, Timer } from 'phosphor-svelte';

	const META = 160;
	let total = $state(0);
	let obj = $state(0);
	let disc = $state(0);

	onMount(async () => {
		const b = await carregarBanco();
		total = b.length;
		obj = b.filter((q) => q.tipo === 'objetiva').length;
		disc = b.filter((q) => q.tipo === 'discursiva').length;
	});
</script>

<div class="mx-auto w-full max-w-3xl">


<div class="mb-4 flex items-center gap-2">
	<a href="/" class="flex items-center gap-1 rounded-lg px-2 py-2 text-sm font-bold text-ink-soft" aria-label="Voltar ao início">
		<ArrowLeft size={18} weight="bold" aria-hidden="true" /> Início
	</a>
	<span class="flex-1"></span>
	<h1 class="text-sm font-bold tracking-wide text-ink-soft uppercase">Simulado real</h1>
</div>

<div class="space-y-4">
	<div class="rise rounded-3xl bg-bar p-5 text-white shadow-[0_10px_30px_-12px_rgba(20,33,61,0.45)]">
		<p class="flex items-center gap-2 text-[11px] font-bold tracking-[0.14em] text-bar-fg uppercase">
			<Timer size={15} weight="bold" aria-hidden="true" /> Formato ENADE 2026
		</p>
		<ul class="nums mt-3 space-y-1.5 text-[15px] font-semibold">
			<li class="flex justify-between gap-3"><span>Formação Geral</span><span>15 objetivas</span></li>
			<li class="flex justify-between gap-3"><span>Componente Específico</span><span>30 objetivas</span></li>
			<li class="flex justify-between gap-3"><span>Discursiva</span><span>1 questão</span></li>
			<li class="flex justify-between gap-3 border-t border-white/20 pt-2"><span>Tempo</span><span>4 horas</span></li>
		</ul>
	</div>

	<div class="rise rounded-3xl bg-card p-5 shadow-[0_10px_30px_-12px_rgba(20,33,61,0.25)]" style="animation-delay: 80ms">
		<p class="text-sm font-bold">Banco atual</p>
		<p class="nums mt-1 text-sm text-ink-soft">
			{total} de {META} questões ({obj} objetivas + {disc} discursivas)
		</p>
		<div class="mt-2 h-2.5 overflow-hidden rounded-full bg-track" role="progressbar" aria-valuenow={total} aria-valuemin="0" aria-valuemax={META} aria-label="Progresso do banco de questões">
			<div class="h-full rounded-full bg-accent transition-[width] duration-700 ease-out" style="width: {(total / META) * 100}%"></div>
		</div>
		<button
			type="button"
			disabled
			aria-disabled="true"
			title="Disponível quando o banco estiver completo"
			class="mt-4 flex w-full cursor-not-allowed items-center justify-center gap-2 rounded-2xl bg-tile p-3.5 font-bold text-ink-soft"
		>
			<LockKey size={18} weight="bold" aria-hidden="true" /> Cronometrado em breve
		</button>
		<p class="mt-2 text-center text-xs text-ink-soft">
			Enquanto isso: <a href="/treino/" class="font-bold text-accent-ink underline">treino livre</a> e
			<a href="/estudo/" class="font-bold text-accent-ink underline">estudo por níveis</a>.
		</p>
	</div>
</div>

</div>
