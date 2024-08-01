from rest_framework import viewsets, permissions

from book.models import Book
from book.permisions import IsAdminOrIfAuthenticatedReadOnly
from book.serializers import BookSerializer


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects
    serializer_class = BookSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)
