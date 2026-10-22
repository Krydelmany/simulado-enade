// Testa a migração com um Postgres de verdade (PGlite, WASM) — sem Docker e
// sem projeto no Supabase. O schema `auth` é um dublê mínimo do Supabase:
// `auth.users` + `auth.uid()` lendo o claim `sub`, e os papéis anon/authenticated.
//
//   cd supabase/testes && npm install && npm test
//
// Cada `como(usuario, sql)` roda como `authenticated` com aquele `sub`, então a
// RLS e os grants valem de verdade (superusuário passaria por cima de tudo).

import { PGlite } from '@electric-sql/pglite';
import { readFileSync, readdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';

const aqui = dirname(fileURLToPath(import.meta.url));
const pastaMigracoes = join(aqui, '..', 'migrations');

const DUBLE_AUTH = `
	create role anon nologin;
	create role authenticated nologin;
	create schema auth;
	grant usage on schema auth to anon, authenticated;
	create table auth.users (id uuid primary key, raw_user_meta_data jsonb not null default '{}');
	create function auth.uid() returns uuid language sql stable as
		$$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
	grant execute on function auth.uid() to anon, authenticated;
	grant usage on schema public to anon, authenticated;
`;

const db = new PGlite();
await db.exec(DUBLE_AUTH);
for (const f of readdirSync(pastaMigracoes).filter((f) => f.endsWith('.sql')).sort()) {
	await db.exec(readFileSync(join(pastaMigracoes, f), 'utf8'));
}

const U = {
	prof: '00000000-0000-0000-0000-00000000000a',
	ana: '00000000-0000-0000-0000-00000000000b',
	beto: '00000000-0000-0000-0000-00000000000c',
	intruso: '00000000-0000-0000-0000-00000000000d'
};

async function como(usuario, sql, params = []) {
	await db.exec('reset role');
	await db.query(`select set_config('request.jwt.claim.sub', $1, false)`, [usuario ?? '']);
	await db.exec(usuario ? 'set role authenticated' : 'set role anon');
	try {
		return (await db.query(sql, params)).rows;
	} finally {
		await db.exec('reset role');
	}
}

async function falha(promessa, trecho) {
	await assert.rejects(promessa, (e) => {
		assert.match(String(e.message), trecho);
		return true;
	});
}

let n = 0;
async function teste(nome, fn) {
	await fn();
	n++;
	console.log('ok', nome);
}

// --- preparo (como admin, igual ao painel do Supabase) ---------------------
for (const [k, id] of Object.entries(U)) {
	await db.query(`insert into auth.users (id, raw_user_meta_data) values ($1, $2)`, [
		id,
		JSON.stringify({ full_name: `Nome ${k}` })
	]);
}
const [turma] = (
	await db.query(
		`insert into public.turmas (curso, instituicao, nome, data_prova, codigo)
		 values ('engcomp', 'Unisalesiano', 'Eng. Comp. 2026', '2026-11-29', 'ENGC26') returning id`
	)
).rows;
await db.query(
	`insert into public.membros (turma_id, usuario_id, papel, apelido) values ($1, $2, 'professor', 'Prof')`,
	[turma.id, U.prof]
);

const resp = (usuario, questao, resultado, extra = {}) =>
	como(
		usuario,
		`insert into public.respostas (id, questao_id, oficial, parte, materia, modo, resultado, duracao_ms, respondida_em)
		 values (gen_random_uuid(), $1, $2, $3, $4, $5, $6, 1000, coalesce($7::timestamptz, now())) returning usuario_id`,
		[questao, extra.oficial ?? true, extra.parte ?? 'CE', extra.materia ?? 'algoritmos', extra.modo ?? 'treino', resultado, extra.em ?? null]
	);

// --- testes ------------------------------------------------------------------
await teste('perfil nasce do login com o nome do Google', async () => {
	const r = await como(U.ana, 'select nome from public.perfis');
	assert.deepEqual(r, [{ nome: 'Nome ana' }]);
});

await teste('anon não lê nada além de cursos', async () => {
	assert.equal((await como(null, 'select * from public.cursos')).length, 1);
	await falha(como(null, 'select * from public.respostas'), /permission denied/);
	await falha(como(null, `select public.entrar_turma('ENGC26', 'x', null, true, true)`), /permission denied/);
});

await teste('quem não é membro não acha a turma', async () => {
	assert.equal((await como(U.ana, 'select * from public.turmas')).length, 0);
});

await teste('entrar sem consentimento ou com código errado falha', async () => {
	await falha(como(U.ana, `select * from public.entrar_turma('ENGC26', 'Ana', null, true, false)`), /sem_consentimento/);
	await falha(como(U.ana, `select * from public.entrar_turma('XXXXXX', 'Ana', null, true, true)`), /codigo_invalido/);
});

await teste('entrar com código (minúsculo e espaço valem) e RA opcional', async () => {
	const r = await como(U.ana, `select nome from public.entrar_turma(' engc26 ', 'Ana', '123456', true, true)`);
	assert.deepEqual(r, [{ nome: 'Eng. Comp. 2026' }]);
	await como(U.beto, `select * from public.entrar_turma('ENGC26', 'Beto', null, false, true)`);
	assert.equal((await como(U.ana, 'select * from public.turmas')).length, 1);
});

await teste('entrar de novo atualiza a matrícula sem virar professor', async () => {
	await como(U.ana, `select * from public.entrar_turma('ENGC26', 'Aninha', '123456', true, true)`);
	const r = await como(U.ana, 'select apelido, papel from public.membros');
	assert.deepEqual(r, [{ apelido: 'Aninha', papel: 'aluno' }]);
});

await teste('apelido repetido na turma é recusado (sem diferença de caixa)', async () => {
	await falha(como(U.beto, `select * from public.entrar_turma('ENGC26', 'ANINHA', null, true, true)`), /membros_apelido_unico/);
});

await teste('aluno não se promove a professor nem entra em turma direto', async () => {
	await falha(como(U.ana, `update public.membros set papel = 'professor'`), /permission denied/);
	await falha(
		como(U.intruso, `insert into public.membros (turma_id, usuario_id, apelido) values ($1, $2, 'x')`, [turma.id, U.intruso]),
		/permission denied/
	);
});

await teste('aluno vê só a própria matrícula; professor vê a turma', async () => {
	assert.equal((await como(U.ana, 'select * from public.membros')).length, 1);
	assert.equal((await como(U.prof, 'select * from public.membros')).length, 3);
});

await teste('resposta só se grava como si mesmo', async () => {
	const [r] = await resp(U.ana, '2019-CE-Q09', 'certa');
	assert.equal(r.usuario_id, U.ana);
	await falha(
		como(
			U.ana,
			`insert into public.respostas (id, usuario_id, questao_id, oficial, modo, resultado, respondida_em)
			 values (gen_random_uuid(), $1, '2019-CE-Q09', true, 'treino', 'certa', now())`,
			[U.beto]
		),
		/permission denied/
	);
});

await teste('reenviar a mesma resposta (mesmo id) não duplica', async () => {
	const id = '11111111-1111-1111-1111-111111111111';
	const sql = `insert into public.respostas (id, questao_id, oficial, materia, modo, resultado, respondida_em)
		values ($1, '2019-CE-Q10', true, 'algoritmos', 'treino', 'errada', now()) on conflict (id) do nothing`;
	await como(U.ana, sql, [id]);
	await como(U.ana, sql, [id]);
	const r = await como(U.ana, `select count(*)::int as n from public.respostas where id = $1`, [id]);
	assert.equal(r[0].n, 1);
});

await teste('resposta com data no futuro é recusada', async () => {
	await falha(resp(U.ana, '2019-CE-Q11', 'certa', { em: '2030-01-01' }), /check constraint/);
});

await teste('aluno lê só as próprias respostas', async () => {
	await resp(U.beto, '2019-CE-Q09', 'errada');
	await resp(U.beto, '2019-FG-Q01', 'certa', { parte: 'FG', materia: 'fg' });
	const r = await como(U.ana, 'select distinct usuario_id from public.respostas');
	assert.deepEqual(r, [{ usuario_id: U.ana }]);
	assert.equal((await como(U.prof, 'select * from public.respostas')).length, 0);
});

await teste('painel: professor vê alunos com nome e RA; aluno e intruso, nada', async () => {
	const r = await como(U.prof, 'select nome, apelido, ra, respondidas::int, certas::int from public.painel_alunos($1)', [turma.id]);
	assert.deepEqual(r, [
		{ nome: 'Nome ana', apelido: 'Aninha', ra: '123456', respondidas: 2, certas: 1 },
		{ nome: 'Nome beto', apelido: 'Beto', ra: null, respondidas: 2, certas: 1 }
	]);
	assert.equal((await como(U.ana, 'select * from public.painel_alunos($1)', [turma.id])).length, 0);
	assert.equal((await como(U.intruso, 'select * from public.painel_alunos($1)', [turma.id])).length, 0);
});

await teste('painel: questões mais erradas respeitam o mínimo de tentativas', async () => {
	const r = await como(U.prof, 'select questao_id, tentativas::int, erros::int from public.painel_questoes($1, 2)', [turma.id]);
	assert.deepEqual(r, [{ questao_id: '2019-CE-Q09', tentativas: 2, erros: 1 }]);
});

await teste('painel: matérias e semanas agregam a turma', async () => {
	const m = await como(U.prof, 'select materia, respondidas::int from public.painel_materias($1) order by materia', [turma.id]);
	assert.deepEqual(m, [
		{ materia: 'algoritmos', respondidas: 3 },
		{ materia: 'fg', respondidas: 1 }
	]);
	const s = await como(U.prof, 'select alunos_ativos::int, respondidas::int from public.painel_semanas($1)', [turma.id]);
	assert.deepEqual(s, [{ alunos_ativos: 2, respondidas: 4 }]);
});

await teste('ranking: só apelido, quem saiu do ranking some (menos para si)', async () => {
	const ana = await como(U.ana, 'select apelido, eu from public.ranking_turma($1)', [turma.id]);
	assert.deepEqual(ana, [{ apelido: 'Aninha', eu: true }]);
	const beto = await como(U.beto, 'select apelido, eu from public.ranking_turma($1)', [turma.id]);
	assert.deepEqual(beto.map((x) => x.apelido).sort(), ['Aninha', 'Beto']);
	assert.equal((await como(U.intruso, 'select * from public.ranking_turma($1)', [turma.id])).length, 0);
	const cols = Object.keys(beto[0]);
	assert.ok(!cols.includes('nome') && !cols.includes('ra'));
});

await teste('sair da turma tira do painel, mas mantém as respostas do aluno', async () => {
	await como(U.beto, 'delete from public.membros');
	assert.equal((await como(U.prof, 'select * from public.painel_alunos($1)', [turma.id])).length, 1);
	assert.equal((await como(U.beto, 'select * from public.respostas')).length, 2);
});

await teste('apagar a conta leva perfil e respostas junto', async () => {
	await como(U.ana, 'select public.apagar_minha_conta()');
	assert.equal((await db.query(`select * from public.respostas where usuario_id = $1`, [U.ana])).rows.length, 0);
	assert.equal((await db.query(`select * from public.perfis where id = $1`, [U.ana])).rows.length, 0);
});

console.log(`\n${n} testes passaram`);
