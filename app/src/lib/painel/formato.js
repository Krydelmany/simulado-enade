// Formatação compartilhada pelo painel do professor e pela ficha do aluno.

/** Número vindo do banco (bigint chega como string) → number. */
export const num = (v) => Number(v) || 0;

/** Porcentagem inteira, ou `null` sem base. */
export const pct = (c, t) => (num(t) ? Math.round((num(c) / num(t)) * 100) : null);

/** "42%" ou "—". */
export const fmtPct = (c, t) => (pct(c, t) === null ? '—' : `${pct(c, t)}%`);

/** "hoje", "ontem", "há 5 dias" ou "nunca". */
export function quando(iso) {
	if (!iso) return 'nunca';
	const dias = Math.floor((Date.now() - new Date(iso).getTime()) / 86_400_000);
	if (dias <= 0) return 'hoje';
	if (dias === 1) return 'ontem';
	return `há ${dias} dias`;
}

/** "sex 31/10 às 23:59". */
export function diaHora(iso) {
	const d = new Date(iso);
	if (Number.isNaN(d.getTime())) return '';
	const dia = d.toLocaleDateString('pt-BR', { weekday: 'short' }).replace('.', '');
	const data = d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
	const hora = d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
	return `${dia} ${data} às ${hora}`;
}

/** "2026-10-19" (ou Date) → "19/10". Data sem hora: meio-dia evita virar o dia no fuso. */
export function diaMes(d) {
	const x = typeof d === 'string' ? new Date(`${d.slice(0, 10)}T12:00:00`) : d;
	return x.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
}

/** Data local "AAAA-MM-DD" (a mesma chave que o banco usa por dia). */
export function isoDia(d) {
	const p = (n) => String(n).padStart(2, '0');
	return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

/** Segunda-feira da semana de `d` (o `date_trunc('week')` do Postgres). */
export function inicioDaSemana(d = new Date()) {
	const x = new Date(d);
	x.setHours(12, 0, 0, 0);
	x.setDate(x.getDate() - ((x.getDay() + 6) % 7));
	return x;
}

/** "1 aluno" / "3 alunos". */
export const plural = (n, um, varios) => `${num(n)} ${num(n) === 1 ? um : varios}`;
