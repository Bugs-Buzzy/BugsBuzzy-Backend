import math
from inperson.models import InPersonTeam, InPersonSubmission
from django.db.models import Sum

def calculate_in_person_score(solve_count, solved_count, phase0_score):
    try: 
        teams_count = InPersonTeam.objects.filter(status="attended").count()
        games_count = InPersonSubmission.objects.filter(phase=2, score=1).count()
        ttavg = InPersonTeam.objects.filter(status="attended").aggregate(sum=Sum('solved_count'))['sum'] / games_count
        phase4_solved_score = 10 * teams_count * math.exp(-1 * ((solved_count - ttavg) ** 2) / teams_count)
    except ZeroDivisionError:
        phase4_solved_score = 0

    return phase4_solved_score + 10 * solve_count + phase0_score