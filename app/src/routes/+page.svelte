<script>
	import { onMount } from 'svelte';
	import { carregarBanco } from '$lib/banco.js';
	import { getXP, getStreak } from '$lib/stats.js';

	let total = $state(0);
	let xp = $state(0);
	let dias = $state(0);

	onMount(async () => {
		total = (await carregarBanco()).length;
		xp = getXP();
		dias = getStreak().dias;
	});
</script>

<div class="space-y-4">
	<div class="rounded-xl bg-blue-900 p-5 text-white">
		<h1 class="text-xl font-bold">Simulado ENADE — Eng. de Computação</h1>
		<p class="mt-1 text-sm text-blue-200">Questões oficiais do INEP + simulado da turma. {total} no banco.</p>
		<div class="mt-3 flex gap-4 text-sm font-semibold">
			<span>⚡ {xp} XP</span>
			<span>🔥 {dias} dia(s) seguidos</span>
		</div>
	</div>

	<a href="/treino" class="block rounded-xl bg-white p-5 shadow-sm active:bg-blue-50">
		<p class="text-lg font-bold">🏃 Treino livre</p>
		<p class="mt-1 text-sm text-slate-600">Fila infinita, sem total fixo. Para quando quiser e vê o resumo.</p>
	</a>

	<a href="/estudo" class="block rounded-xl bg-white p-5 shadow-sm active:bg-blue-50">
		<p class="text-lg font-bold">📚 Estudo · 10 questões</p>
		<p class="mt-1 text-sm text-slate-600">Sessão curta com níveis: N1 fundamentos, N2 intermediário, N3 avançado.</p>
	</a>

	<a href="/simulado" class="block rounded-xl bg-white p-5 shadow-sm active:bg-blue-50">
		<p class="text-lg font-bold">⏱️ Simulado real</p>
		<p class="mt-1 text-sm text-slate-600">Formato da prova: 46 questões em 4h (15 FG + 30 CE + 1 discursiva).</p>
	</a>
</div>
