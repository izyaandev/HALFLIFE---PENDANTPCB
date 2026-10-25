-- Planned Supabase / Postgres schema for the Half Life pendant (matches the ER diagram in the README)
create extension if not exists vector;

create table devices (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  last_seen timestamptz
);

create table recordings (
  id uuid primary key default gen_random_uuid(),
  device_id uuid references devices(id) on delete cascade,
  created_at timestamptz default now(),
  duration_s real,
  audio_path text,
  transcript text,
  summary text,
  action_items jsonb default '[]',
  tags text[] default '{}',
  model_used text,
  embedding vector(1536)
);

create table bookmarks (
  id uuid primary key default gen_random_uuid(),
  recording_id uuid references recordings(id) on delete cascade,
  at_second real not null
);

create index on recordings using ivfflat (embedding vector_cosine_ops);
create index on recordings (created_at desc);
