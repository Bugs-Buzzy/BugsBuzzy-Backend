from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseForbidden
from django.shortcuts import render
from inperson.models import InPersonTeam, InPersonSubmission
from django.db.models import OuterRef, Subquery, DecimalField, IntegerField
from django.db.models.functions import Cast
from django.db.models import Value
from django.db.models.functions import Coalesce
from .utils import calculate_in_person_score


def _base_queryset_with_phase0():
    final_subq = (
        InPersonSubmission.objects.filter(team=OuterRef('pk'), phase=0, is_final=True)
        .values('score')[:1]
    )
    return (
        InPersonTeam.objects.filter(status='attended')
        .annotate(
            team_number_int=Coalesce(Cast('team_number', IntegerField()), Value(None)),
            phase0_score=Subquery(final_subq, output_field=DecimalField(null=True)),
        )
    )


def public_leaderboard(request):
    teams = list(_base_queryset_with_phase0().order_by('team_number_int', 'team_number'))

    count = len(teams)
    avg_solve_count = sum(t.solve_count for t in teams) / count if count else 0.0
    avg_solved_count = sum(t.solved_count for t in teams) / count if count else 0.0
    phase0_vals = [float(t.phase0_score) for t in teams if t.phase0_score is not None]
    avg_phase0_score = sum(phase0_vals) / len(phase0_vals) if phase0_vals else 0.0

    return render(
        request,
        'leaderboard/public.html',
        {
            'teams': teams,
            'avg_solve_count': avg_solve_count,
            'avg_solved_count': avg_solved_count,
            'avg_phase0_score': avg_phase0_score,
        },
    )


def ranked_leaderboard(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return HttpResponseForbidden('Forbidden')

    teams = list(_base_queryset_with_phase0())

    def tn_int(o):
        return o.team_number_int if o.team_number_int is not None else 10**9

    for t in teams:
        t.total_score = float(
            calculate_in_person_score(t.solve_count, t.solved_count, float(t.phase0_score or 0))
        )

    teams.sort(key=lambda o: (-o.total_score, tn_int(o)))
    count = len(teams)
    avg_solve_count = sum(t.solve_count for t in teams) / count if count else 0.0
    avg_solved_count = sum(t.solved_count for t in teams) / count if count else 0.0
    phase0_vals = [float(t.phase0_score) for t in teams if t.phase0_score is not None]
    avg_phase0_score = sum(phase0_vals) / len(phase0_vals) if phase0_vals else 0.0
    avg_total_score = sum(t.total_score for t in teams) / count if count else 0.0

    return render(
        request,
        'leaderboard/ranked.html',
        {
            'teams': teams,
            'avg_solve_count': avg_solve_count,
            'avg_solved_count': avg_solved_count,
            'avg_phase0_score': avg_phase0_score,
            'avg_total_score': avg_total_score,
        },
    )
