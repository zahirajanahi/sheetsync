import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://opyohjpcfaizesfrjlha.supabase.co';
const supabaseKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9weW9oanBjZmFpemVzZnJqbGhhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ4MDU1MTEsImV4cCI6MjA2MDM4MTUxMX0.bzDy0pVpfqz1OFFuu5gGFGSY3y9ot4TMrWChxGIsCpQ";

export const supabase = createClient(supabaseUrl, supabaseKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true
  }
});
