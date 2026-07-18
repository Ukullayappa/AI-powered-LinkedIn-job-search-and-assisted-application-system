from app.repositories.supabase_client import (
    supabase_client,
)


class SupabaseHealthRepository:
    def check_connection(
        self,
    ) -> dict:
        """
        Run a small database query to confirm
        that Supabase is reachable.
        """

        result = (
            supabase_client
            .table("profiles")
            .select("id")
            .limit(1)
            .execute()
        )

        return {
            "connected": True,
            "rows_checked": len(
                result.data
            ),
        }


supabase_health_repository = (
    SupabaseHealthRepository()
)