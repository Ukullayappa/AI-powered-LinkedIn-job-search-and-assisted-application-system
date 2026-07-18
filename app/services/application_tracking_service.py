from datetime import datetime, timezone

from app.schemas.application_schema import (
    ApplicationHistoryItem,
    NextJobResponse,
)
from app.utils.json_storage import storage


class ApplicationTrackingService:
    def get_history(
        self,
    ) -> list[ApplicationHistoryItem]:
        """
        Return all saved submitted applications.
        """

        saved_applications = storage.read(
            "applications",
            [],
        )

        return [
            ApplicationHistoryItem(
                **application
            )
            for application in saved_applications
        ]

    def get_submitted_job_ids(
        self,
    ) -> set[str]:
        """
        Return all job IDs whose status is submitted.
        """

        applications = storage.read(
            "applications",
            [],
        )

        return {
            str(
                application.get(
                    "job_id",
                    "",
                )
            )
            for application in applications
            if (
                application.get("status")
                == "submitted"
                and application.get("job_id")
            )
        }

    def is_submitted(
        self,
        job_id: str,
    ) -> bool:
        """
        Check whether one job was already submitted.
        """

        return str(job_id) in (
            self.get_submitted_job_ids()
        )

    def mark_submitted(
        self,
        job_id: str,
    ) -> ApplicationHistoryItem:
        """
        Save one job as submitted.

        If the job already exists, update the existing
        record instead of creating a duplicate.
        """

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

        applications = storage.read(
            "applications",
            [],
        )

        submitted_at = datetime.now(
            timezone.utc
        ).isoformat()

        new_record = {
            "job_id": str(job_id),

            "title": selected_job.get(
                "title",
                "",
            ),

            "company": selected_job.get(
                "company",
                "",
            ),

            "url": selected_job.get(
                "url",
                "",
            ),

            "status": "submitted",

            "submitted_at": submitted_at,
        }

        existing_record = next(
            (
                application
                for application in applications
                if str(
                    application.get(
                        "job_id",
                        "",
                    )
                )
                == str(job_id)
            ),
            None,
        )

        if existing_record is not None:
            existing_record.update(
                new_record
            )
        else:
            applications.append(
                new_record
            )

        storage.write(
            "applications",
            applications,
        )

        print(
            "Application remembered as submitted:",
            selected_job.get(
                "title",
                "",
            ),
        )

        return ApplicationHistoryItem(
            **new_record
        )

    def get_next_job(
        self,
    ) -> NextJobResponse | None:
        """
        Return the next highest-ranked job that
        has not already been submitted.
        """

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
