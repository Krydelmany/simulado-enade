<script>
	/**
	 * Símbolo livre da plataforma — idêntico ao `favicon.svg`, sem caixa/moldura.
	 * Prisma âmbar facetado flutuando sobre uma base isométrica na cor do curso
	 * ativo (`var(--accent)` + `var(--milestone)`). Com `interativo` ligado, o
	 * cristal levita com mola no hover do próprio ícone ou de um ancestral `.group`.
	 */
	let { tamanho = 32, classe = '', interativo = true } = $props();
</script>

<svg
	width={tamanho}
	height={tamanho}
	viewBox="0 0 32 32"
	fill="none"
	class="marca-prisma shrink-0 overflow-visible {interativo ? 'marca-viva' : ''} {classe}"
	aria-hidden="true"
>
	<!-- Base isométrica tátil na paleta do curso ativo -->
	<g class="marca-base">
		<path
			fill="color-mix(in oklab, var(--accent-bar) 78%, white)"
			d="M16 11 L28.5 17.5 L16 24 L3.5 17.5 Z"
		/>
		<path fill="var(--accent)" d="M3.5 17.5 L16 24 V30.5 L3.5 24 Z" />
		<path
			fill="color-mix(in oklab, var(--accent) 66%, #070e24)"
			d="M28.5 17.5 L16 24 V30.5 L28.5 24 Z"
		/>
		<path
			class="marca-sombra"
			fill="#09132e"
			opacity="0.26"
			d="M16 14.4 L21.4 17.2 L16 20 L10.6 17.2 Z"
		/>
	</g>

	<!-- Cristal âmbar facetado que flutua acima da base -->
	<g class="marca-cristal">
		<path
			fill="color-mix(in oklab, var(--milestone) 64%, white)"
			d="M16 1.6 L23.2 5.4 L16 9.2 L8.8 5.4 Z"
		/>
		<path fill="var(--milestone)" d="M8.8 5.4 L16 9.2 V16.4 L8.8 12.6 Z" />
		<path
			fill="color-mix(in oklab, var(--milestone) 72%, #3a1700)"
			d="M23.2 5.4 L16 9.2 V16.4 L23.2 12.6 Z"
		/>
	</g>
</svg>

<style>
	.marca-base,
	.marca-cristal,
	.marca-sombra {
		transform-box: fill-box;
		transform-origin: center;
		transition:
			transform 230ms var(--mola-curva, cubic-bezier(0.34, 1.56, 0.64, 1)),
			opacity 180ms ease;
	}

	:global(.group:hover) .marca-viva .marca-cristal,
	.marca-viva:hover .marca-cristal {
		transform: translateY(-2.4px) scale(1.04);
	}

	:global(.group:hover) .marca-viva .marca-sombra,
	.marca-viva:hover .marca-sombra {
		transform: scale(0.8);
		opacity: 0.16;
	}

	:global(.group:hover) .marca-viva .marca-base,
	.marca-viva:hover .marca-base {
		transform: translateY(0.6px);
	}

	:global(.group:active) .marca-viva .marca-cristal,
	.marca-viva:active .marca-cristal {
		transform: translateY(0.8px) scale(0.97);
		transition-duration: 75ms;
	}

	@media (prefers-reduced-motion: reduce) {
		.marca-base,
		.marca-cristal,
		.marca-sombra {
			transition: none !important;
			transform: none !important;
		}
	}
</style>
