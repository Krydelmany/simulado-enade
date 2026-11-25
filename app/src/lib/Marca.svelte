<script>
	// Símbolo livre da plataforma — idêntico ao favicon.svg, sem caixa/moldura.
	// Adapta-se automaticamente ao tema claro/escuro e ao pacote de cor do curso
	// ativo (`var(--accent)` + `var(--milestone)`).
	let { tamanho = 30, classe = '' } = $props();
</script>

<svg
	width={tamanho}
	height={tamanho}
	viewBox="0 0 32 32"
	fill="none"
	class="shrink-0 {classe}"
	aria-hidden="true"
>
	<path fill="var(--accent)" d="M3 7 L7 3 H9 V23 H26 L22 29 H3 Z" />
	<path fill="var(--accent-bar)" opacity="0.88" d="M12 3 H29 L25 9 H12 Z" />
	<path fill="var(--accent)" d="M12 13 H21 L17.5 19 H12 Z" />
	<path fill="var(--milestone)" d="M25.5 12.5 L29 16 L25.5 19.5 L22 16 Z" />
</svg>
