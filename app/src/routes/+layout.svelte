<script>
	import '../app.css';
</script>

<header class="sticky top-0 z-10 bg-blue-900 text-white shadow">
	<nav class="mx-auto flex max-w-3xl items-center gap-1 px-3 py-3 text-sm font-semibold">
		<a href="/" class="mr-2 rounded px-2 py-1 text-base">🎓 ENADE</a>
		<a href="/treino" class="rounded px-2 py-1 hover:bg-blue-800">Treino</a>
		<a href="/estudo" class="rounded px-2 py-1 hover:bg-blue-800">Estudo</a>
		<a href="/simulado" class="rounded px-2 py-1 hover:bg-blue-800">Simulado</a>
	</nav>
</header>

<main class="mx-auto max-w-3xl px-3 py-5 pb-16">
	<slot />
</main>
