-- Belfort accounts and sync (T43). Run once in the Supabase project's SQL editor, or with `supabase db push`.
-- One row per (user, kind) holds a whole JSON document: practice, learn or settings (see docs/ARCHITECTURE.md).
-- Row-level security means a signed-in user can read and write only their own rows; the public anon key alone
-- can read nothing.

create table if not exists public.user_state (
  user_id    uuid        not null references auth.users (id) on delete cascade,
  kind       text        not null check (kind in ('practice', 'learn', 'settings')),
  payload    jsonb       not null,
  updated_at timestamptz not null default now(),
  primary key (user_id, kind)
);

-- updated_at is always the server's clock, so "last write wins" compares times from one clock across devices.
create or replace function public.user_state_touch() returns trigger
language plpgsql as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

drop trigger if exists user_state_touch on public.user_state;
create trigger user_state_touch before insert or update on public.user_state
  for each row execute function public.user_state_touch();

alter table public.user_state enable row level security;

drop policy if exists "read own state" on public.user_state;
create policy "read own state" on public.user_state
  for select to authenticated using ((select auth.uid()) = user_id);

drop policy if exists "insert own state" on public.user_state;
create policy "insert own state" on public.user_state
  for insert to authenticated with check ((select auth.uid()) = user_id);

drop policy if exists "update own state" on public.user_state;
create policy "update own state" on public.user_state
  for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);

drop policy if exists "delete own state" on public.user_state;
create policy "delete own state" on public.user_state
  for delete to authenticated using ((select auth.uid()) = user_id);

revoke all on public.user_state from anon;
grant select, insert, update, delete on public.user_state to authenticated;

-- Delete my account: removes the signed-in user and, through the foreign key, all their synced rows.
-- SECURITY DEFINER so it may delete from auth.users, but it only ever deletes the caller.
create or replace function public.delete_my_account() returns void
language plpgsql security definer set search_path = '' as $$
begin
  if auth.uid() is null then
    raise exception 'not signed in';
  end if;
  delete from auth.users where id = auth.uid();
end;
$$;

revoke all on function public.delete_my_account() from public, anon;
grant execute on function public.delete_my_account() to authenticated;
