import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://uawgxohzeqtbnxfbpjny.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVhd2d4b2h6ZXF0Ym54ZmJwam55Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTMyMzg4MTQsImV4cCI6MjA2ODgxNDgxNH0.oPie12ebJCNhDladNPnrtgTJOBgj2-_whe9vp1v3AvQ';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);