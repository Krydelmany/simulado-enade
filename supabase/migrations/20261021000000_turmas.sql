-- Turmas, membros e respostas: o backend do piloto (ENADE 29/11/2026).
--
-- Decisões que este arquivo implementa (ver docs/DECISOES.md):
--   D3  o navegador fala direto com o Supabase; a permissão mora AQUI (RLS),
--       não em endpoint. Tabela nova sem policy = ninguém lê.
--   D4  uma linha por resposta (`respostas`); painel e ranking são derivados.
--   D5  professor lê a turma só pelas funções `painel_*`, que conferem o papel.
--   D6  RA é opcional, fica na matrícula (`membros`), não no perfil.
--   D7  o aluno consente ao entrar na turma e pode apagar a conta sozinho.
--
-- Regra para quem mexer: função `security definer` sempre com
-- `set search_path = ''` e nomes qualificados (`public.x`), senão um objeto
-- criado no schema do chamador sequestra a função.

-- ---------------------------------------------------------------------------
-- Tabelas
-- ---------------------------------------------------------------------------

-- Um por usuário do Supabase Auth; o nome vem do Google no primeiro login.
create table public.perfis (
	id uuid primary key references auth.users (id) on delete cascade,
	nome text not null default '' check (char_length(nome) <= 120),
	criado_em timestamptz not null default now()
);

-- Área do ENADE (ex.: 'engcomp'). O id é o mesmo prefixo usado no app.
create table public.cursos (
	id text primary key check (id ~ '^[a-z0-9-]{2,30}$'),
	nome text not null
);

create table public.turmas (
	id uuid primary key default gen_random_uuid(),
	curso text not null references public.cursos (id),
	instituicao text not null check (char_length(instituicao) between 2 and 120),
	nome text not null check (char_length(nome) between 2 and 120),
	data_prova date,
	-- código do convite: 6+ caracteres sem ambíguos (0/O, 1/I/L)
	codigo text not null unique check (codigo ~ '^[A-HJKMNP-Z2-9]{6,12}$'),
	ranking_ativo boolean not null default true,
	criado_em timestamptz not null default now()
);

create table public.membros (
	turma_id uuid not null references public.turmas (id) on delete cascade,
	usuario_id uuid not null references public.perfis (id) on delete cascade,
	papel text not null default 'aluno' check (papel in ('aluno', 'professor')),
	apelido text not null check (char_length(btrim(apelido)) between 2 and 24),
	ra text check (ra is null or ra ~ '^[0-9A-Za-z.-]{3,20}$'),
	-- "no ranking" = aparece no ranking (opt-out); o professor vê todo mundo no painel
	no_ranking boolean not null default true,
	consentiu_em timestamptz not null default now(),
	entrou_em timestamptz not null default now(),
	primary key (turma_id, usuario_id)
);

create index membros_usuario on public.membros (usuario_id);
-- dois "Aluno" no ranking não dá para saber quem é quem
create unique index membros_apelido_unico on public.membros (turma_id, lower(btrim(apelido)));

-- O id vem do aparelho (crypto.randomUUID): reenviar a fila depois de uma
-- falha de rede não duplica a resposta (`on conflict do nothing`).
create table public.respostas (
	id uuid primary key,
	usuario_id uuid not null default auth.uid() references public.perfis (id) on delete cascade,
	curso text not null default 'engcomp' references public.cursos (id),
	questao_id text not null check (char_length(questao_id) between 3 and 40),
	oficial boolean not null,
	parte text check (parte in ('FG', 'CE')),
	materia text check (char_length(materia) <= 60),
	modo text not null check (modo in ('treino', 'estudo', 'simulado')),
	resultado text not null check (resultado in ('certa', 'errada', 'parcial', 'anulada')),
	duracao_ms integer check (duracao_ms between 0 and 86400000),
	respondida_em timestamptz not null,
	recebida_em timestamptz not null default now(),
	-- relógio do aparelho errado não pode jogar resposta para o futuro
	check (respondida_em <= recebida_em + interval '1 day')
);

create index respostas_usuario_data on public.respostas (usuario_id, respondida_em desc);
create index respostas_questao on public.respostas (curso, questao_id);

-- ---------------------------------------------------------------------------
-- Perfil automático no primeiro login
-- ---------------------------------------------------------------------------

create function public.criar_perfil()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
	insert into public.perfis (id, nome)
	values (
		new.id,
		left(coalesce(new.raw_user_meta_data ->> 'full_name', new.raw_user_meta_data ->> 'name', ''), 120)
	)
	on conflict (id) do nothing;
	return new;
end;
$$;

create trigger ao_criar_usuario
after insert on auth.users
for each row execute function public.criar_perfil();

-- ---------------------------------------------------------------------------
-- Ajudantes de permissão (security definer para não recursar na RLS de membros)
-- ---------------------------------------------------------------------------

create function public.eh_membro(t uuid)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
	select exists (
		select 1 from public.membros m where m.turma_id = t and m.usuario_id = auth.uid()
	);
$$;

create function public.eh_professor(t uuid)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
	select exists (
		select 1 from public.membros m
		where m.turma_id = t and m.usuario_id = auth.uid() and m.papel = 'professor'
	);
$$;

-- ---------------------------------------------------------------------------
-- RLS
-- ---------------------------------------------------------------------------

alter table public.perfis enable row level security;
alter table public.cursos enable row level security;
alter table public.turmas enable row level security;
alter table public.membros enable row level security;
alter table public.respostas enable row level security;

create policy perfis_proprio_ler on public.perfis
	for select to authenticated using (id = auth.uid());
create policy perfis_proprio_editar on public.perfis
	for update to authenticated using (id = auth.uid()) with check (id = auth.uid());

create policy cursos_ler on public.cursos
	for select to anon, authenticated using (true);

-- turma: só quem é membro enxerga; criar turma é coisa do admin (service role)
create policy turmas_membro_ler on public.turmas
	for select to authenticated using (public.eh_membro(id));

-- matrícula: cada um vê a própria; o professor vê as da turma.
-- Entrar é pela função `entrar_turma` (precisa achar a turma pelo código,
-- que o aluno ainda não enxerga); por isso não há policy de insert.
create policy membros_ler on public.membros
	for select to authenticated
	using (usuario_id = auth.uid() or public.eh_professor(turma_id));
create policy membros_proprio_sair on public.membros
	for delete to authenticated using (usuario_id = auth.uid());

-- respostas: o aluno grava e lê só as próprias; o professor lê pelo painel
create policy respostas_proprio_ler on public.respostas
	for select to authenticated using (usuario_id = auth.uid());
create policy respostas_proprio_gravar on public.respostas
	for insert to authenticated with check (usuario_id = auth.uid());

-- O Supabase dá ALL nas tabelas novas para anon/authenticated por padrão;
-- a RLS barra as linhas, mas fechamos as colunas também.
revoke all on public.perfis, public.cursos, public.turmas, public.membros, public.respostas from anon, authenticated;
grant select on public.cursos to anon, authenticated;
grant select on public.perfis, public.turmas, public.membros, public.respostas to authenticated;
grant update (nome) on public.perfis to authenticated;
grant insert (id, curso, questao_id, oficial, parte, materia, modo, resultado, duracao_ms, respondida_em)
	on public.respostas to authenticated;
grant delete on public.membros to authenticated;

-- ---------------------------------------------------------------------------
-- Ações do aluno
-- ---------------------------------------------------------------------------

-- Entra (ou atualiza a matrícula) pelo código do convite. Sempre como aluno:
-- professor é cadastrado pelo admin. Devolve a turma.
create function public.entrar_turma(
	p_codigo text,
	p_apelido text,
	p_ra text default null,
	p_no_ranking boolean default true,
	p_consentiu boolean default false
)
returns setof public.turmas
language plpgsql
security definer
set search_path = ''
as $$
declare
	v_turma public.turmas;
	v_ra text := nullif(btrim(coalesce(p_ra, '')), '');
begin
	if auth.uid() is null then
		raise exception 'sem_login' using errcode = '28000';
	end if;
	if not coalesce(p_consentiu, false) then
		raise exception 'sem_consentimento' using errcode = '22023';
	end if;

	select * into v_turma from public.turmas where codigo = upper(btrim(p_codigo));
	if not found then
		raise exception 'codigo_invalido' using errcode = '22023';
	end if;

	insert into public.membros (turma_id, usuario_id, apelido, ra, no_ranking, consentiu_em)
	values (v_turma.id, auth.uid(), btrim(p_apelido), v_ra, coalesce(p_no_ranking, true), now())
	on conflict (turma_id, usuario_id) do update
		set apelido = excluded.apelido,
			ra = excluded.ra,
			no_ranking = excluded.no_ranking,
			consentiu_em = excluded.consentiu_em;

	return next v_turma;
end;
$$;

-- LGPD: apaga o usuário do Auth; perfil, matrículas e respostas vão em cascata.
create function public.apagar_minha_conta()
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
	if auth.uid() is null then
		raise exception 'sem_login' using errcode = '28000';
	end if;
	delete from auth.users where id = auth.uid();
end;
$$;

-- ---------------------------------------------------------------------------
-- Ranking (qualquer membro) — só apelido, nunca nome nem RA
-- ---------------------------------------------------------------------------

create function public.ranking_turma(p_turma uuid, p_desde timestamptz default null)
returns table (apelido text, eu boolean, respondidas bigint, certas bigint, dias_ativos bigint)
language sql
stable
security definer
set search_path = ''
as $$
	select
		m.apelido,
		m.usuario_id = auth.uid(),
		count(r.id),
		count(r.id) filter (where r.resultado = 'certa'),
		count(distinct (r.respondida_em at time zone 'America/Sao_Paulo')::date)
	from public.membros m
	join public.turmas t on t.id = m.turma_id
	left join public.respostas r
		on r.usuario_id = m.usuario_id
		and r.curso = t.curso
		and (p_desde is null or r.respondida_em >= p_desde)
	where m.turma_id = p_turma
		and m.papel = 'aluno'
		and (m.no_ranking or m.usuario_id = auth.uid())
		and t.ranking_ativo
		and public.eh_membro(p_turma)
	group by m.usuario_id, m.apelido
	order by 4 desc, 3 desc, 1;
$$;

-- ---------------------------------------------------------------------------
-- Painel do professor — todas conferem eh_professor e devolvem vazio se não
-- ---------------------------------------------------------------------------

-- Um por aluno: quem está estudando e como.
create function public.painel_alunos(p_turma uuid)
returns table (
	usuario_id uuid,
	nome text,
	apelido text,
	ra text,
	respondidas bigint,
	certas bigint,
	respondidas_7d bigint,
	dias_ativos bigint,
	simulados bigint,
	ultima_em timestamptz
)
language sql
stable
security definer
set search_path = ''
as $$
	select
		m.usuario_id,
		p.nome,
		m.apelido,
		m.ra,
		count(r.id),
		count(r.id) filter (where r.resultado = 'certa'),
		count(r.id) filter (where r.respondida_em >= now() - interval '7 days'),
		count(distinct (r.respondida_em at time zone 'America/Sao_Paulo')::date),
		count(r.id) filter (where r.modo = 'simulado'),
		max(r.respondida_em)
	from public.membros m
	join public.turmas t on t.id = m.turma_id
	join public.perfis p on p.id = m.usuario_id
	left join public.respostas r on r.usuario_id = m.usuario_id and r.curso = t.curso
	where m.turma_id = p_turma and m.papel = 'aluno' and public.eh_professor(p_turma)
	group by m.usuario_id, p.nome, m.apelido, m.ra
	order by 5 desc, 3;
$$;

-- Onde a turma está fraca: acerto por matéria (oficiais e geradas separadas).
create function public.painel_materias(p_turma uuid)
returns table (materia text, oficial boolean, alunos bigint, respondidas bigint, certas bigint)
language sql
stable
security definer
set search_path = ''
as $$
	select r.materia, r.oficial, count(distinct r.usuario_id), count(*),
		count(*) filter (where r.resultado = 'certa')
	from public.respostas r
	join public.membros m on m.usuario_id = r.usuario_id and m.turma_id = p_turma and m.papel = 'aluno'
	join public.turmas t on t.id = p_turma and t.curso = r.curso
	where public.eh_professor(p_turma) and r.resultado <> 'anulada'
	group by r.materia, r.oficial
	order by 4 desc;
$$;

-- As questões que a turma mais erra (com um mínimo de tentativas para a taxa
-- não ser ruído de uma pessoa só).
create function public.painel_questoes(p_turma uuid, p_minimo integer default 3, p_limite integer default 20)
returns table (questao_id text, materia text, alunos bigint, tentativas bigint, erros bigint)
language sql
stable
security definer
set search_path = ''
as $$
	select r.questao_id, max(r.materia), count(distinct r.usuario_id), count(*),
		count(*) filter (where r.resultado = 'errada')
	from public.respostas r
	join public.membros m on m.usuario_id = r.usuario_id and m.turma_id = p_turma and m.papel = 'aluno'
	join public.turmas t on t.id = p_turma and t.curso = r.curso
	where public.eh_professor(p_turma) and r.resultado in ('certa', 'errada')
	group by r.questao_id
	having count(*) >= greatest(p_minimo, 1)
	order by (count(*) filter (where r.resultado = 'errada'))::numeric / count(*) desc, 4 desc
	limit least(greatest(p_limite, 1), 100);
$$;

-- Evolução semana a semana até a prova.
create function public.painel_semanas(p_turma uuid)
returns table (semana date, alunos_ativos bigint, respondidas bigint, certas bigint)
language sql
stable
security definer
set search_path = ''
as $$
	select date_trunc('week', r.respondida_em at time zone 'America/Sao_Paulo')::date,
		count(distinct r.usuario_id), count(*), count(*) filter (where r.resultado = 'certa')
	from public.respostas r
	join public.membros m on m.usuario_id = r.usuario_id and m.turma_id = p_turma and m.papel = 'aluno'
	join public.turmas t on t.id = p_turma and t.curso = r.curso
	where public.eh_professor(p_turma)
	group by 1
	order by 1;
$$;

revoke all on function
	public.criar_perfil(),
	public.eh_membro(uuid),
	public.eh_professor(uuid),
	public.entrar_turma(text, text, text, boolean, boolean),
	public.apagar_minha_conta(),
	public.ranking_turma(uuid, timestamptz),
	public.painel_alunos(uuid),
	public.painel_materias(uuid),
	public.painel_questoes(uuid, integer, integer),
	public.painel_semanas(uuid)
from public, anon;

grant execute on function
	public.eh_membro(uuid),
	public.eh_professor(uuid),
	public.entrar_turma(text, text, text, boolean, boolean),
	public.apagar_minha_conta(),
	public.ranking_turma(uuid, timestamptz),
	public.painel_alunos(uuid),
	public.painel_materias(uuid),
	public.painel_questoes(uuid, integer, integer),
	public.painel_semanas(uuid)
to authenticated;

insert into public.cursos (id, nome) values ('engcomp', 'Engenharia de Computação');
