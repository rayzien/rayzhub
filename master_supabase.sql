-- Create users table
CREATE TABLE IF NOT EXISTS public.users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    full_name TEXT,
    role TEXT DEFAULT 'admin',
    is_verified BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

-- Create requests table
CREATE TABLE IF NOT EXISTS public.requests (
    id SERIAL PRIMARY KEY,
    name TEXT,
    email TEXT,
    message TEXT,
    photo_path TEXT,
    request_type TEXT DEFAULT 'request',
    amount TEXT,
    transaction_id TEXT,
    is_anonymous BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now()),
    status TEXT DEFAULT 'pending'
);

-- Create verification logs table
CREATE TABLE IF NOT EXISTS public.verification_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    action TEXT NOT NULL,
    ip_address TEXT,
    status TEXT DEFAULT 'success',
    details TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

-- Create widget configs table
CREATE TABLE IF NOT EXISTS public.widget_configs (
    id SERIAL PRIMARY KEY,
    config_key TEXT UNIQUE NOT NULL,
    config_json TEXT NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

-- Create links table
CREATE TABLE IF NOT EXISTS public.links (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    target_url TEXT NOT NULL,
    short_code TEXT UNIQUE NOT NULL,
    clicks INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

-- Create Supabase Storage Bucket for uploads
INSERT INTO storage.buckets (id, name, public) 
VALUES ('rayzhub_uploads', 'rayzhub_uploads', true) 
ON CONFLICT (id) DO NOTHING;
