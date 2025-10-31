# راهنمای استفاده از اسکریپت ارسال اعلان به تیم‌ها

این اسکریپت برای ارسال اعلان به اعضای تیم‌ها از طریق Django shell طراحی شده است.

## ساختار

- `send_team_announcement.py`: فایل اصلی شامل توابع
- `example_usage.py`: مثال‌های استفاده

## روش استفاده

### روش ۱: اجرا مستقیم در Django Shell

```bash
cd BugsBuzzy-Backend
python manage.py shell
```

سپس در shell:

```python
from send_team_announcement import send_announcement_to_team
from inperson.models import InPersonTeam

# دریافت تیم
team = InPersonTeam.objects.get(id=1)  # یا get(name="نام تیم")

# ارسال اعلان
send_announcement_to_team(
    team=team,
    title="عنوان اعلان",
    description="متن اعلان اینجا",
    team_type='inperson'
)
```

### روش ۲: استفاده از فایل مثال

```bash
python manage.py shell < example_usage.py
```

یا در Django shell:

```python
exec(open('example_usage.py').read())
```

## توابع موجود

### `send_announcement_to_team(team, title, description=None, team_type='inperson')`

ارسال اعلان به یک تیم خاص.

**پارامترها:**
- `team`: شی تیم (`InPersonTeam` یا `OnlineTeam`)
- `title`: عنوان اعلان (ضروری)
- `description`: متن اعلان (اختیاری)
- `team_type`: نوع تیم (`'inperson'` یا `'gamejam'`)

**مثال:**
```python
team = InPersonTeam.objects.get(id=1)
send_announcement_to_team(
    team=team,
    title="اعلان مهم",
    description="این اعلان به تمام اعضای تیم ارسال می‌شود",
    team_type='inperson'
)
```

### `send_announcement_to_all_teams(title, description=None, team_type='inperson', filter_active=True)`

ارسال اعلان به تمام تیم‌ها.

**پارامترها:**
- `title`: عنوان اعلان (ضروری)
- `description`: متن اعلان (اختیاری)
- `team_type`: نوع تیم (`'inperson'` یا `'gamejam'`)
- `filter_active`: اگر `True` باشد، فقط تیم‌های active را شامل می‌شود

**مثال:**
```python
send_announcement_to_all_teams(
    title="اعلان عمومی",
    description="این اعلان به تمام تیم‌های فعال ارسال می‌شود",
    team_type='inperson',
    filter_active=True
)
```

## نکات مهم

1. هر تیم ۳ عضو دارد: ۱ لیدر + ۲ عضو
2. اعلان‌ها در جدول `UserAnnouncement` ذخیره می‌شوند
3. اگر اعلان برای یک کاربر قبلاً وجود داشته باشد، دوباره ایجاد نمی‌شود
4. برای ارسال ایمیل، باید از کد موجود در `accounts/admin.py` استفاده کنید

## مثال‌های کامل

### مثال ۱: ارسال به یک تیم خاص با ID
```python
from send_team_announcement import send_announcement_to_team
from inperson.models import InPersonTeam

team = InPersonTeam.objects.get(id=1)
send_announcement_to_team(
    team=team,
    title="اعلان تست",
    description="متن اعلان",
    team_type='inperson'
)
```

### مثال ۲: ارسال به یک تیم خاص با نام
```python
team = InPersonTeam.objects.get(name="نام تیم")
send_announcement_to_team(
    team=team,
    title="اعلان مهم",
    team_type='inperson'
)
```

### مثال ۳: ارسال به تمام تیم‌های InPerson فعال
```python
from send_team_announcement import send_announcement_to_all_teams

send_announcement_to_all_teams(
    title="اعلان عمومی",
    description="این اعلان برای تمام تیم‌ها است",
    team_type='inperson',
    filter_active=True
)
```

### مثال ۴: ارسال به تیم‌های GameJam
```python
from send_team_announcement import send_announcement_to_team
from gamejam.models import OnlineTeam

team = OnlineTeam.objects.get(id=1)
send_announcement_to_team(
    team=team,
    title="اعلان GameJam",
    team_type='gamejam'
)
```

