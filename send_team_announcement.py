"""
اسکریپت Django Shell برای ارسال اعلان به اعضای تیم

استفاده:
    python manage.py shell < send_team_announcement.py
    
یا در Django shell:
    exec(open('send_team_announcement.py').read())
"""

from announcement.models import Announcement, UserAnnouncement
from inperson.models import InPersonTeam
from gamejam.models import OnlineTeam
from django.contrib.auth import get_user_model

User = get_user_model()


def send_announcement_to_team(team, title, description=None, team_type="inperson"):
    """
    ارسال اعلان به تمام اعضای یک تیم (۳ عضو)

    Args:
        team: شی تیم (InPersonTeam یا OnlineTeam)
        title: عنوان اعلان
        description: متن اعلان (اختیاری)
        team_type: نوع تیم ('inperson' یا 'gamejam')

    Returns:
        تعداد اعلان‌های ایجاد شده
    """
    # ایجاد اعلان
    announcement = Announcement.objects.create(title=title, description=description)

    # دریافت اعضای تیم
    if team_type == "inperson":
        team_members = [team.leader]  # لیدر
        team_members.extend([member.user for member in team.members.all()])  # اعضا
    else:  # gamejam
        team_members = [team.leader]  # لیدر
        team_members.extend([member.user for member in team.members.all()])  # اعضا

    # حذف تکراری‌ها (در صورت وجود)
    team_members = list(set(team_members))

    # ایجاد UserAnnouncement برای هر عضو
    created_count = 0
    for user in team_members:
        user_announcement, created = UserAnnouncement.objects.get_or_create(
            announcement=announcement, user=user
        )
        if created:
            created_count += 1
            print(f"✓ اعلان برای {user.email} ایجاد شد")
        else:
            print(f"⚠ اعلان برای {user.email} قبلاً وجود داشت")

    print(f"\n✅ اعلان '{title}' برای تیم '{team.name}' ایجاد شد")
    print(f"📊 تعداد اعضا: {len(team_members)} | اعلان‌های جدید: {created_count}")

    return created_count


def send_announcement_to_all_teams(
    title, description=None, team_type="inperson", filter_active=True
):
    """
    ارسال اعلان به تمام تیم‌ها

    Args:
        title: عنوان اعلان
        description: متن اعلان (اختیاری)
        team_type: نوع تیم ('inperson' یا 'gamejam')
        filter_active: اگر True باشد، فقط تیم‌های active را شامل می‌شود
    """
    if team_type == "inperson":
        teams = InPersonTeam.objects.all()
        if filter_active:
            teams = teams.filter(status="active")
    else:  # gamejam
        teams = OnlineTeam.objects.all()
        if filter_active:
            teams = teams.filter(status="active")

    total_teams = teams.count()
    print(f"📋 تعداد تیم‌های پیدا شده: {total_teams}\n")

    total_announcements = 0
    for i, team in enumerate(teams, 1):
        print(f"\n[{i}/{total_teams}] پردازش تیم: {team.name} (ID: {team.id})")
        count = send_announcement_to_team(team, title, description, team_type)
        total_announcements += count

    print(f"\n{'='*60}")
    print(f"✅ تمام شد!")
    print(f"📊 تعداد کل تیم‌ها: {total_teams}")
    print(f"📊 تعداد کل اعلان‌های ایجاد شده: {total_announcements}")
    print(f"{'='*60}")


# ============================================
# مثال‌های استفاده:
# ============================================

if __name__ == "__main__":
    # برای استفاده در Django shell، این بخش اجرا نمی‌شود
    # به جای آن، توابع بالا را مستقیماً صدا بزنید
    pass

# مثال ۱: ارسال اعلان به یک تیم خاص (InPerson)
# team = InPersonTeam.objects.get(id=1)  # یا get(name="نام تیم")
# send_announcement_to_team(
#     team=team,
#     title="عنوان اعلان",
#     description="متن اعلان",
#     team_type='inperson'
# )

# مثال ۲: ارسال اعلان به یک تیم خاص (GameJam)
# team = OnlineTeam.objects.get(id=1)
# send_announcement_to_team(
#     team=team,
#     title="عنوان اعلان",
#     description="متن اعلان",
#     team_type='gamejam'
# )

# مثال ۳: ارسال اعلان به تمام تیم‌های InPerson فعال
# send_announcement_to_all_teams(
#     title="عنوان اعلان برای تمام تیم‌ها",
#     description="متن اعلان",
#     team_type='inperson',
#     filter_active=True
# )

# مثال ۴: ارسال اعلان به تمام تیم‌های GameJam
# send_announcement_to_all_teams(
#     title="عنوان اعلان",
#     description="متن اعلان",
#     team_type='gamejam',
#     filter_active=False  # شامل همه تیم‌ها، حتی inactive
# )
