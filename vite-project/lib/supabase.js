import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://oyeyfnxjciafhbfnkvdk.supabase.co';
const supabaseKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im95ZXlmbnhqY2lhZmhiZm5rdmRrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ3MTY4ODEsImV4cCI6MjA2MDI5Mjg4MX0.JX2YdvAaG4_FvpS_BqQXJgADw5w8Mo-tHDL6SRhc8MI";

export const supabase = createClient(supabaseUrl, supabaseKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true
  }
});


