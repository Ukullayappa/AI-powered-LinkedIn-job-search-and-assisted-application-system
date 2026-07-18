from app.repositories.application_repository import (
    application_repository,
)
from app.schemas.application_schema import (
    ApplicationHistoryItem,
    NextJobResponse,
)
from app.utils.json_storage import storage


class ApplicationTrackingService:
    def get_history(
        self,
    ) -> list[ApplicationHistoryItem]:
        saved_applications = (
            application_repository.get_all()
        )

        return [
            ApplicationHistoryItem(
                job_id=str(
                    application.get(
                        "linkedin_job_id",
                        "",
                    )
                ),
                title=str(
                    application.get(
                        "title",
                        "",
                    )
                ),
                company=str(
                    application.get(
                        "company",
                        "",
                    )
                ),
                url=str(
                    application.get(
                        "url",
                        "",
                    )
                ),
                status=str(
                    application.get(
                        "status",
                        "",
                    )
                ),
                submitted_at=str(
                    application.get(
                        "submitted_at",
                        "",
                    )
                ),
            )
            for application in saved_applications
        ]

    def get_submitted_job_ids(
        self,
    ) -> set[str]:
        return (
            application_repository
            .get_submitted_job_ids()
        )

    def is_submitted(
        self,
        job_id: str,
    ) -> bool:
        return str(job_id) in (
            self.get_submitted_job_ids()
        )

    def mark_submitted(
        self,
        job_id: str,
    ) -> ApplicationHistoryItem:
        best_jobs = storage.read(
            "best_jobs",
            [],
        )

        if not best_jobs:
            raise ValueError(
                "Best jobs were not found. "
                "Run job ranking first."
            )

        selected_job = next(
            (
                job
                for job in best_jobs
                if str(
                    job.get(
                        "job_id",
                        "",
                    )
                )
                == str(job_id)
            ),
            None,
        )

        if selected_job is None:
            raise ValueError(
                "Job ID was not found inside "
                "data/best_jobs.json."
            )

        saved = (
            application_repository
            .save_submitted(
                selected_job
            )
        )

        print(
            "Application saved in Supabase:",
            selected_job.get(
                "title",
                "",
            ),
        )

        return ApplicationHistoryItem(
            job_id=str(
                saved.get(
                    "linkedin_job_id",
                    "",
                )
            ),
            title=str(
                saved.get(
                    "title",
                    "",
                )
            ),
            company=str(
                saved.get(
                    "company",
                    "",
                )
            ),
            url=str(
                saved.get(
                    "url",
                    "",
                )
            ),
            status=str(
                saved.get(
                    "status",
                    "",
                )
            ),
            submitted_at=str(
                saved.get(
                    "submitted_at",
                    "",
                )
            ),
        )

    def get_next_job(
        self,
    ) -> NextJobResponse | None:
        best_jobs = storage.read(
            "best_jobs",
            [],
        )

        if not best_jobs:
            raise ValueError(
                "Best jobs were not found. "
                "Run job ranking first."
            )

        submitted_job_ids = (
            self.get_submitted_job_ids()
        )

        for job in best_jobs:
            job_id = str(
                job.get(
                    "job_id",
                    "",
                )
            )

            if job_id in submitted_job_ids:
                continue

            return NextJobResponse(
                job_id=job_id,
                title=job.get(
                    "title",
                    "",
                ),
                company=job.get(
                    "company",
                    "",
                ),
                location=job.get(
                    "location",
                    "",
                ),
                url=job.get(
                    "url",
                    "",
                ),
                match_score=job.get(
                    "match_score",
                    0,
                ),
                message=(
                    "This is the next highest-ranked "
                    "job that has not been submitted."
                ),
            )

        return None


application_tracking_service = (
    ApplicationTrackingService()
)
