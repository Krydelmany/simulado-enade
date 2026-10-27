-- Simulado em papel: o retrato que vem do site do professor (pilar.ia.br).
--
-- O dado lá é FIXO (a prova em papel já aconteceu e não há outro simulado
-- marcado), então não existe proxy em tempo real nem scraping no navegador:
-- um script importa uma vez e o site só lê. Isso também evita o CORS do
-- pilar e faz a página abrir mesmo se o site do professor cair.
--
-- Guardamos só o resumo que o aluno e o professor precisam (acertos,
-- percentual, áreas, prioridades e a comparação com a turma). Não guardamos
-- cookie de sessão, resposta por questão nem uma segunda cópia do RA.
-- `usuario_id` aponta para `perfis`, que cai em cascata com `auth.users`:
-- apagar a conta apaga o retrato junto (D7).
--
-- O cliente NÃO escreve nesta tabela. Quem importa é o admin, pela SQL
-- gerada por `supabase/importar-pilar.py` (roda como postgres e ignora RLS).
-- Assim o aluno não consegue inflar os próprios números pelo DevTools.

create table public.desempenho_papel (
	usuario_id uuid not null references public.perfis (id) on delete cascade,
	curso text not null default 'engcomp' references public.cursos (id),
	-- o id do simulado no pilar pode ser número; guardamos como texto
	simulado_id text not null check (char_length(simulado_id) between 1 and 60),
	rotulo text not null check (char_length(rotulo) between 1 and 120),
	acertos integer not null check (acertos >= 0),
	total integer not null check (total > 0),
	percentual numeric(5, 4) not null check (percentual between 0 and 1),
	-- { "Área": { "total": 5, "percentual": 0.4, "turma": 0.55 } }
	areas jsonb not null default '{}'::jsonb check (jsonb_typeof(areas) = 'object'),
	-- [{ "area": "Redes", "percentual": 0.25, "tendencia": "piorou" }]
	prioridades jsonb not null default '[]'::jsonb check (jsonb_typeof(prioridades) = 'array'),
	-- { "total_questoes": 40, "media_acertos": 23.5, "mediana_acertos": 24 }
	turma jsonb not null default '{}'::jsonb check (jsonb_typeof(turma) = 'object'),
	-- { "nota_1": 7.5, "nota_2": 8.0 } quando a prova teve discursiva corrigida
	discursiva jsonb check (discursiva is null or jsonb_typeof(discursiva) = 'object'),
	importado_em timestamptz not null default now(),
	primary key (usuario_id, curso, simulado_id)
);

alter table public.desempenho_papel enable row level security;

-- O aluno lê só o próprio retrato. O professor lê a turma pela função
-- `painel_papel`, como todas as outras `painel_*` (D5).
create policy desempenho_papel_proprio_ler on public.desempenho_papel
	for select to authenticated using (usuario_id = auth.uid());

revoke all on public.desempenho_papel from anon, authenticated;
grant select on public.desempenho_papel to authenticated;

-- ---------------------------------------------------------------------------
-- Painel do professor
-- ---------------------------------------------------------------------------

-- Retrato do simulado em papel de um aluno (ou da turma toda, sem p_aluno).
-- Quem não é professor da turma recebe zero linhas, como as outras painel_*.
create function public.painel_papel(p_turma uuid, p_aluno uuid default null)
returns table (
	usuario_id uuid,
	simulado_id text,
	rotulo text,
	acertos integer,
	total integer,
	percentual numeric,
	areas jsonb,
	prioridades jsonb,
	turma jsonb,
	discursiva jsonb,
	importado_em timestamptz
)
language sql
stable
security definer
set search_path = ''
as $$
	select
		d.usuario_id, d.simulado_id, d.rotulo, d.acertos, d.total,
		d.percentual, d.areas, d.prioridades, d.turma, d.discursiva,
		d.importado_em
	from public.desempenho_papel d
	join public.membros m
		on m.usuario_id = d.usuario_id
		and m.turma_id = p_turma
		and m.papel = 'aluno'
	join public.turmas t on t.id = p_turma and t.curso = d.curso
	where public.eh_professor(p_turma)
		and (p_aluno is null or d.usuario_id = p_aluno)
	order by d.importado_em desc, d.rotulo;
$$;

revoke all on function public.painel_papel(uuid, uuid) from public, anon;
grant execute on function public.painel_papel(uuid, uuid) to authenticated;

-- ---------------------------------------------------------------------------
-- O aluno informa ou troca o RA depois de já estar na turma
-- ---------------------------------------------------------------------------

-- Sem isso, quem entrou antes do campo de RA (ou deixou em branco) só
-- conseguiria informar saindo da turma e entrando de novo. O RA é o que
-- liga a conta ao resultado do simulado em papel.
create function public.salvar_ra(p_turma uuid, p_ra text)
returns text
language plpgsql
security definer
set search_path = ''
as $$
declare
	v_ra text := nullif(btrim(coalesce(p_ra, '')), '');
begin
	if auth.uid() is null then
		raise exception 'sem_login' using errcode = '28000';
	end if;

	update public.membros
	set ra = v_ra
	where turma_id = p_turma and usuario_id = auth.uid();

	if not found then
		raise exception 'nao_e_membro' using errcode = '22023';
	end if;

	return v_ra;
end;
$$;

revoke all on function public.salvar_ra(uuid, text) from public, anon;
grant execute on function public.salvar_ra(uuid, text) to authenticated;
