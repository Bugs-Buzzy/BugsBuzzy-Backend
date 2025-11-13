from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import UserAnnouncement
from .serializers import UserAnnouncementSerializer


class MyAnnouncementsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserAnnouncementSerializer

    def get(self, request):
        user_announcements = (
            UserAnnouncement.objects.filter(user=request.user)
            .select_related("announcement")
            .order_by("-created_at")
        )
        serializer = UserAnnouncementSerializer(user_announcements, many=True)
        return Response(serializer.data)
