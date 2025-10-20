-- ENTER THIS CODE IN YOUR POSTGRESQL DB
-- FORSUPABASE: WITH ADDITIONAL COMMANDS AT THE END OF THE FILE

-- Enable the pgvector extension
create extension if not exists vector;

-- Create the documentation chunks table
create table site_pages (
    id bigserial primary key,
    url varchar not null,
    chunk_number integer not null,
    title varchar not null,
    summary varchar not null,
    content text not null,  -- Added content column
    meta_details jsonb not null default '{}'::jsonb,
    embedding vector(768),
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,

    -- Add a unique constraint to prevent duplicate chunks for the same URL
    unique(url, chunk_number)
);

-- Create an index for better vector similarity search performance
set maintenance_work_mem = '1GB';  -- Adjust memory if needed
create index on site_pages using ivfflat (embedding vector_cosine_ops) with (lists = 100);

-- Create an index on meta_details for faster filtering (formerly metadata)
create index idx_site_pages_meta_details on site_pages using gin (meta_details);

-- Create a function to search for documentation chunks
create function match_site_pages (
  query_embedding vector(768),
  match_count int default 10,
  filter jsonb DEFAULT '{}'::jsonb
) returns table (
  id bigint,
  url varchar,
  chunk_number integer,
  title varchar,
  summary varchar,
  content text,
  meta_details jsonb,
  similarity float
)
language plpgsql
as $$
#variable_conflict use_column
begin
  return query
  select
    id,
    url,
    chunk_number,
    title,
    summary,
    content,
    meta_details,
    1 - (site_pages.embedding <=> query_embedding) as similarity
  from site_pages
  where (filter = '{}'::jsonb OR meta_details @> filter)
  order by site_pages.embedding <=> query_embedding
  limit match_count;
end;
$$;

-- Optional: Add Supabase-specific security

-- alter table site_pages enable row level security;

-- Enable row level security with a public read policy (optional)
-- create policy "Allow public read access"
--   on site_pages
--   for select
--   to public
--   using (true);
