from functools import lru_cache

from supabase import Client, create_client

from app.config import settings


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    """
    Return a cached Supabase client using the service-role key.
    Service-role key bypasses Row Level Security — only used server-side.
    Call this from the DB layer (crud.py) and nowhere else.
    """
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
