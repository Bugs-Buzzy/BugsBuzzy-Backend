from django.core.management.base import BaseCommand
from inperson.models import InPersonTeam, InPersonSubmission
from inperson.utils import generate_hash
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Updates solver_team_number and owner_team_number for InPersonSubmissions based on hash matching"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run without making any changes to the database",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(
                self.style.WARNING("Running in DRY RUN mode - no changes will be saved")
            )

        # Get all attended in-person teams
        teams = InPersonTeam.objects.filter(status="attended")
        teams_list = list(teams)

        self.stdout.write(f"Found {len(teams_list)} attended teams")

        updated_count = 0
        skipped_count = 0
        same_team_count = 0
        not_found_count = 0

        # Iterate through all pairs of solver and owner teams
        for solver_team in teams_list:
            for owner_team in teams_list:
                # Skip if solver and owner are the same team
                if solver_team.id == owner_team.id:
                    same_team_count += 1
                    logger.info(
                        f"Skipping same team pair: solver={solver_team.team_number} ({solver_team.name}), "
                        f"owner={owner_team.team_number} ({owner_team.name})"
                    )
                    self.stdout.write(
                        self.style.WARNING(
                            f"Skipped same team: {solver_team.team_number} ({solver_team.name})"
                        )
                    )
                    continue

                # Calculate hash using team_number as the group code
                hash_value = generate_hash(solver_team.invite_code, owner_team.invite_code)

                # Parse team numbers as integers
                try:
                    solver_number = int(solver_team.team_number)
                except (ValueError, TypeError):
                    self.stdout.write(
                        self.style.ERROR(
                            f"Invalid solver team_number: {solver_team.team_number} for team {solver_team.name}"
                        )
                    )
                    skipped_count += 1
                    continue

                try:
                    owner_number = int(owner_team.team_number)
                except (ValueError, TypeError):
                    self.stdout.write(
                        self.style.ERROR(
                            f"Invalid owner team_number: {owner_team.team_number} for team {owner_team.name}"
                        )
                    )
                    skipped_count += 1
                    continue

                # Find all submissions with this hash in content field
                submissions = InPersonSubmission.objects.filter(content=hash_value)

                if not submissions.exists():
                    not_found_count += 1
                    logger.debug(
                        f"No submission found for hash {hash_value}: "
                        f"solver={solver_team.team_number}, owner={owner_team.team_number}"
                    )
                    continue

                # Update all submissions with this hash
                for submission in submissions:
                    if not dry_run:
                        submission.solver_team_number = solver_number
                        submission.owner_team_number = owner_number
                        submission.save()

                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'{"[DRY RUN] " if dry_run else ""}Updated submission {submission.id} '
                            f"(Phase {submission.phase}, Final: {submission.is_final}): "
                            f"solver={solver_team.team_number} ({solver_team.name}), "
                            f"owner={owner_team.team_number} ({owner_team.name}), "
                            f"hash={hash_value}"
                        )
                    )

        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS(f"Processing complete!"))
        self.stdout.write(f"Total team pairs processed: {len(teams_list) * (len(teams_list) - 1)}")
        self.stdout.write(self.style.SUCCESS(f"Submissions updated: {updated_count}"))
        self.stdout.write(self.style.WARNING(f"Same team pairs skipped: {same_team_count}"))
        self.stdout.write(f"Submissions not found: {not_found_count}")
        self.stdout.write(f"Errors/Skipped: {skipped_count}")
        self.stdout.write("=" * 60)

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "\nThis was a DRY RUN - no changes were saved. "
                    "Run without --dry-run to apply changes."
                )
            )
