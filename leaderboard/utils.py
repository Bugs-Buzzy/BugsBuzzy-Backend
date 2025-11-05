import math
from inperson.models import InPersonTeam, InPersonSubmission
from django.db.models import Sum


def calculate_in_person_score(solve_count, solved_count, phase0_score):
    try:
        teams_with_solved = InPersonTeam.objects.filter(status="attended", solved_count__gt=0)
        non_zero_solved_counts = [team.solved_count for team in teams_with_solved]
        ttavg = (
            sum(non_zero_solved_counts) / len(non_zero_solved_counts) * 2 / 3
            if non_zero_solved_counts
            else 0
        )
        phase4_solved_score = 500 * math.exp(
            -1 * ((solved_count - ttavg) ** 2) / len(teams_with_solved)
        )
    except ZeroDivisionError:
        phase4_solved_score = 0

    return phase4_solved_score + 10 * solve_count + phase0_score
