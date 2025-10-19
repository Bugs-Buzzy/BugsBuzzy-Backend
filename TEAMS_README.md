# Teams System Implementation

This document describes the teams system for the BugsBuzzy event platform with separate team classes for different payment behaviors.

## Overview

The teams system supports two types of participation with distinct payment logic:

- **In-Person Teams**: Each member pays individually. Team is qualified when ALL members have paid.
- **Online Teams**: One payment covers the entire team. Team is qualified when ANY member pays for the whole team.

## Team Class Architecture

### BaseTeam (Abstract Base Class)

- **Purpose**: Shared logic for all team types
- **Fields**:
  - `name`: Team name
  - `description`: Optional team description
  - `status`: Team status (active/disbanded)
  - `invite_code`: Unique 8-character code for joining
  - `leader`: Team creator/leader
  - `created_at`, `updated_at`: Timestamps

### InPersonTeam (Inherits from BaseTeam)

- **Payment Logic**: Each member pays individually
- **Qualification**: Team is qualified when ALL members have paid
- **No additional fields** - uses member-level payment tracking
- **Business Rule**: Team is considered paid only when every single member has completed their individual payment

### OnlineTeam (Inherits from BaseTeam)

- **Payment Logic**: One payment covers the entire team
- **Qualification**: Team is qualified when ANY member pays for the whole team
- **Additional Fields**:
  - `is_paid`: Team payment status
  - `payment_completed_at`: When team payment was completed
  - `payment_completed_by`: Who completed the team payment
- **Business Rule**: Team is considered paid when any team member makes a single payment for the entire team

### TeamMember Model

- **Fields**:
  - `team`: Generic foreign key to either InPersonTeam or OnlineTeam
  - `user`: Team member
  - `role`: Member role (member/co_leader)
  - `is_paid`: Individual payment status (for in-person teams)
  - `payment_completed_at`: When individual payment was completed

## Payment Qualification Logic

### InPersonTeam Qualification

```python
def check_payment_status(self):
    """Team is qualified when ALL members have paid individually."""
    members = self.get_members()
    if not members.exists():
        return False
    return all(member.is_paid for member in members)
```

### OnlineTeam Qualification

```python
def check_payment_status(self):
    """Team is qualified when team payment is completed."""
    return self.is_paid
```

## API Endpoints

### Team Management

- `GET /api/teams/` - List user's teams (returns both in-person and online teams)
- `GET /api/teams/all/` - Get all teams in a unified format (single list with both types)
- `POST /api/teams/` - Create a new team (specify team_type: 'in_person' or 'online')

### Team Details

- `GET /api/teams/in-person/{id}/` - Get in-person team details
- `GET /api/teams/online/{id}/` - Get online team details

### Team Joining/Leaving

- `POST /api/teams/join/` - Join team with invite code
- `POST /api/teams/{id}/leave/` - Leave team

### Team Payments

- `POST /api/teams/in-person/{id}/payment/` - Process individual payment for in-person team
- `POST /api/teams/online/{id}/payment/` - Process team payment for online team

### Team Members

- `GET /api/teams/{id}/members/` - List team members

## Key Features

### 1. Team Creation

- Users can create teams for either in-person or online participation
- Each user can have one team per type
- Teams get unique invite codes automatically

### 2. Team Joining

- Users can join teams using invite codes
- Validation ensures users can't join multiple teams of the same type
- Team leaders can't leave their teams (must disband instead)

### 3. Payment System

#### In-Person Teams

- Each member must pay individually
- Team is considered qualified when ALL members have paid
- Payment tracking at individual member level
- Detailed status shows paid/unpaid members

#### Online Teams

- One payment covers the entire team
- Any team member can make the payment
- Team is considered qualified when team payment is completed
- Payment tracking at team level

## Business Rules

1. **One Team Per Type**: Users can only be in one active team per participation type
2. **Leader Restrictions**: Team leaders cannot leave their teams
3. **Payment Requirements**:
   - In-person: Each member must pay individually
   - Online: One payment covers the entire team
4. **Team Status**: Teams can be active or disbanded
5. **Qualification Logic**:
   - In-person teams: Qualified when ALL members have paid
   - Online teams: Qualified when ANY member pays for the team

## Usage Examples

### Creating Teams

```python
# Create an in-person team
in_person_team = InPersonTeam.objects.create(
    name="Local Developers",
    description="We meet in person",
    leader=user
)

# Create an online team
online_team = OnlineTeam.objects.create(
    name="Remote Developers",
    description="We work online",
    leader=user
)
```

### Payment Processing

```python
# In-person team - each member pays individually
member = TeamMember.objects.get(team=in_person_team, user=user)
member.mark_payment_completed()

# Online team - any member can pay for the whole team
online_team.mark_payment_completed(user)
```

### Checking Qualification

```python
# Check if team is qualified
if in_person_team.check_payment_status():
    print("All members have paid - team is qualified!")

if online_team.check_payment_status():
    print("Team payment completed - team is qualified!")
```

## API Usage Examples

### Create a Team

```bash
POST /api/teams/
{
    "name": "My Team",
    "description": "Team description",
    "team_type": "online"
}
```

### Join a Team

```bash
POST /api/teams/join/
{
    "invite_code": "ABC12345"
}
```

### Process Payment

```bash
# For online teams (any team member can pay for the whole team)
POST /api/teams/online/123/payment/

# For in-person teams (each member pays individually)
POST /api/teams/in-person/123/payment/
```

### Get All Teams

```bash
GET /api/teams/all/
```

**Response:**

```json
{
  "teams": [
    {
      "id": 1,
      "name": "Online Team",
      "team_type": "online",
      "is_paid": true,
      "payment_status": {
        "is_paid": true,
        "payment_type": "team",
        "payment_completed_by": "user@example.com",
        "payment_completed_at": "2024-01-15T10:30:00Z"
      },
      "created_at": "2024-01-15T10:00:00Z"
    },
    {
      "id": 2,
      "name": "In-Person Team",
      "team_type": "in_person",
      "payment_status": {
        "is_paid": false,
        "payment_type": "individual",
        "total_members": 3,
        "paid_members": 2,
        "unpaid_members": 1
      },
      "created_at": "2024-01-14T15:30:00Z"
    }
  ],
  "total_count": 2,
  "in_person_count": 1,
  "online_count": 1
}
```

## Database Migrations

To apply the database changes:

```bash
pdm run python manage.py makemigrations
pdm run python manage.py migrate
```

## Testing

Run the test suite:

```bash
pdm run python manage.py test teams
```

## Admin Interface

The Django admin interface provides full management capabilities for:

- InPersonTeam (specific admin with payment status)
- OnlineTeam (specific admin with team payment tracking)
- Team Members
- Payments
- Payment Methods

Access the admin at `/admin/` after creating a superuser.

## Key Benefits of the New Architecture

1. **Clear Separation**: Each team type has its own class with specific logic
2. **Type Safety**: Payment logic is enforced at the model level
3. **Maintainability**: Easy to extend or modify behavior for specific team types
4. **Generic Foreign Keys**: TeamMember can work with both team types
5. **Admin Interface**: Separate admin interfaces for different team types
6. **Testing**: Comprehensive test coverage for both team types
7. **API Clarity**: Separate endpoints for different team types and payment methods
