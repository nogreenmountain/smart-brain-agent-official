import asyncio
import os
import threading
from typing import Annotated

import httpx
from fastapi import Depends
from supabase.client import AsyncClient as AsyncSupabase
from supabase.client import Client as Supabase
from supabase.client import ClientOptions

# Global variables to store client instances
supabase = None
async_supabase = None

# Create locks for thread-safe initialization
_supabase_lock = threading.Lock()
_async_supabase_lock = asyncio.Lock()


def _sync_client_options() -> ClientOptions:
    timeout_seconds = float(os.getenv('SUPABASE_AUTH_TIMEOUT_SECONDS', '15'))
    timeout = httpx.Timeout(
        timeout_seconds,
        connect=min(timeout_seconds, 5.0),
        read=timeout_seconds,
        write=timeout_seconds,
        pool=min(timeout_seconds, 5.0),
    )
    return ClientOptions(httpx_client=httpx.Client(timeout=timeout))


def get_supabase():
    """
    FastAPI dependency to get the synchronous Supabase client.
    This allows for proper dependency injection and easier testing.

    Returns:
        Supabase: The synchronous Supabase client instance
    """

    from agentops.api.environment import SUPABASE_KEY, SUPABASE_URL

    global supabase
    if supabase is None:
        with _supabase_lock:
            # Check again inside the lock to prevent race conditions
            if supabase is None:
                supabase = Supabase(SUPABASE_URL, SUPABASE_KEY, options=_sync_client_options())
    return supabase


async def get_async_supabase():
    """
    FastAPI dependency to get the async Supabase client.
    This allows for proper dependency injection and easier testing.

    Returns:
        AsyncSupabase: The async Supabase client instance
    """

    from agentops.api.environment import SUPABASE_KEY, SUPABASE_URL

    global async_supabase
    if async_supabase is None:
        async with _async_supabase_lock:
            # Check again inside the lock to prevent race conditions
            if async_supabase is None:
                async_supabase = AsyncSupabase(SUPABASE_URL, SUPABASE_KEY)
    return async_supabase


# Annotated dependencies for better type hinting
AsyncSupabaseClient = Annotated[AsyncSupabase, Depends(get_async_supabase)]
SupabaseClient = Annotated[Supabase, Depends(get_supabase)]


async def close_supabase_clients():
    """
    Close the Supabase client connections.
    """
    global supabase, async_supabase

    if supabase is not None:
        # Supabase client doesn't have an explicit close method
        # but we can set it to None to allow garbage collection
        supabase = None

    if async_supabase is not None:
        # Async Supabase client doesn't have an explicit close method
        # but we can set it to None to allow garbage collection
        async_supabase = None
