"""Review-first entry point for idempotent relay-auth recovery."""

from relay_remote_dispatch import recovery_main


if __name__ == "__main__":
    raise SystemExit(recovery_main())
