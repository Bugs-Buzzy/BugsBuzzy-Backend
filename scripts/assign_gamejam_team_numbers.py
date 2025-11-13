from __future__ import annotations

"""
Assign sequential team numbers to completed GameJam teams.

Run via Django shell, e.g.:
    python manage.py shell < scripts/assign_gamejam_team_numbers.py
"""

from collections import OrderedDict

from django.apps import apps
from django.db import transaction


def _get_payment_timestamps(transaction_model, leader_ids: set[int]):
    """Return earliest payment timestamps for the provided leader IDs."""
    transactions = (
        transaction_model.objects.filter(
            user_id__in=leader_ids,
            status="completed",
            items__icontains='"gamejam"',
        )
        .order_by("completed_at", "created_at")
        .values_list("user_id", "completed_at", "created_at")
    )

    earliest_by_user = {}
    for user_id, completed_at, created_at in transactions:
        if user_id in earliest_by_user:
            continue
        earliest_by_user[user_id] = completed_at or created_at
    return earliest_by_user


def assign_gamejam_team_numbers():
    OnlineTeam = apps.get_model("gamejam", "OnlineTeam")
    Transaction = apps.get_model("payments", "Transaction")

    teams = list(
        OnlineTeam.objects.filter(status="completed")
        .select_related("leader")
        .order_by("created_at")
    )

    if not teams:
        print("No completed teams found; nothing to do.")
        return

    leader_ids = {team.leader_id for team in teams}
    payment_timestamps = _get_payment_timestamps(Transaction, leader_ids)

    # Sort teams by payment time, falling back to creation timestamp, then PK.
    def sort_key(team):
        return (
            payment_timestamps.get(team.leader_id, team.created_at),
            team.created_at,
            team.pk,
        )

    ordered_teams = OrderedDict()
    for team in sorted(teams, key=sort_key):
        ordered_teams[team.pk] = team

    with transaction.atomic():
        for index, team in enumerate(ordered_teams.values(), start=1):
            new_number = str(index)
            if team.team_number == new_number:
                continue
            team.team_number = new_number
            team.save(update_fields=["team_number"])
            print(f"Assigned team_number={new_number} to team '{team.name}'")

    print(f"Finished assigning team numbers to {len(ordered_teams)} team(s).")


if __name__ == "__main__":
    assign_gamejam_team_numbers()
