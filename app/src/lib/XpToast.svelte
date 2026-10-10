<script>
	let { n } = $props();
	let visivel = $state(true);

	$effect(() => {
		n;
		visivel = true;
		const t = setTimeout(() => (visivel = false), 950);
		return () => clearTimeout(t);
	});
</script>

{#if visivel}
	<span class="xp-float pointer-events-none fixed bottom-24 left-1/2 z-40 -translate-x-1/2 rounded-full bg-accent px-4 py-2 text-sm font-extrabold whitespace-nowrap text-white shadow-lg" role="status">
		+10 XP
	</span>
{/if}
