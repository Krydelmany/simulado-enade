<script>
	let { rotulo, onClick, mostrarXP = false } = $props();
</script>

<div class="fixed inset-x-0 bottom-0 z-30 border-t border-line bg-paper" style="padding-bottom: env(safe-area-inset-bottom);">
	<div class="mx-auto max-w-3xl px-4 py-3">
		<div class="relative">
			{#if mostrarXP}
				<span
					class="xp-float pointer-events-none absolute -top-11 right-3 rounded-full bg-accent-soft px-3 py-1 text-sm font-extrabold text-accent-ink nums shadow"
					role="status"
				>
					+10 XP
				</span>
			{/if}
			<button
				type="button"
				onclick={onClick}
				class="btn3d duo-accent min-h-[52px] w-full rounded-[14px] font-display text-lg font-bold"
			>
				{rotulo}
			</button>
		</div>
	</div>
</div>
