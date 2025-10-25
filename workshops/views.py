from rest_framework import generics

from .models import Workshop
from .serializers import WorkshopSerializer
from rest_framework.permissions import IsAuthenticated


class WorkshopListAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Workshop.objects.all()
    serializer_class = WorkshopSerializer
