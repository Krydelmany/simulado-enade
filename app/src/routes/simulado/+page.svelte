<script>
	import { onMount } from 'svelte';
	import { carregarBanco } from '$lib/banco.js';

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

<div class="space-y-4">
	<h1 class="text-xl font-bold">⏱️ Simulado real</h1>

	<div class="rounded-xl bg-white p-5 shadow-sm">
		<p class="font-semibold">Formato ENADE 2026 (Portaria INEP nº 161)</p>
		<ul class="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
			<li>15 questões de Formação Geral (objetivas)</li>
			<li>30 questões do Componente Específico (objetivas)</li>
			<li>1 questão discursiva</li>
			<li>4 horas de prova · peso 25% FG / 75% CE</li>
		</ul>
	</div>

	<div class="rounded-xl bg-white p-5 shadow-sm">
		<p class="font-semibold">Banco atual</p>
		<p class="mt-1 text-sm text-slate-600">
			{total} questões ({obj} objetivas + {disc} discursivas) de 160 mapeadas.
		</p>
		<div class="mt-2 h-2 overflow-hidden rounded-full bg-slate-200">
			<div class="h-full bg-green-700" style="width: {(total / 160) * 100}%"></div>
		</div>
		<p class="mt-3 rounded-lg bg-amber-50 p-3 text-sm text-amber-900">
			🚧 O modo simulado cronometrado abre quando o banco estiver completo.
			Enquanto isso, treine nos modos <a href="/treino" class="font-bold underline">Treino</a> e
			<a href="/estudo" class="font-bold underline">Estudo</a>.
		</p>
	</div>
</div>
