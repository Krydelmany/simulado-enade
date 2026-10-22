<script>
	// Marca do site: uma linha de cartão-resposta com a bolha marcada a caneta
	// azul. É o mesmo desenho do favicon (static/favicon.svg); mudou um, mude o
	// outro.
	let { tamanho = 28 } = $props();
</script>

<svg width={tamanho} height={tamanho} viewBox="0 0 64 64" aria-hidden="true" class="shrink-0">
	<rect width="64" height="64" rx="16" fill="#fdfcf9" />
	<circle cx="17" cy="32" r="8" fill="none" stroke="#1a2340" stroke-width="4" opacity="0.35" />
	<circle cx="47" cy="32" r="8" fill="none" stroke="#1a2340" stroke-width="4" opacity="0.35" />
	<circle cx="32" cy="32" r="10" fill="#3459e0" />
</svg>
