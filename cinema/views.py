from datetime import datetime

from django.db.models import F, Count
from rest_framework import viewsets

from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieDetailSerializer,
    MovieSessionDetailSerializer,
    MovieListSerializer,
    OrderSerializer, OrderCreateSerializer,
)
from cinema.pagination import CustomPagination
from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related("genres", "actors")
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")
        title = self.request.query_params.get("title")

        if actors:
            actors_list = actors.split(",")
            queryset = queryset.filter(
                actors__id__in=actors_list,
            ).distinct()
        if genres:
            genres_list = genres.split(",")
            queryset = queryset.filter(
                genres__id__in=genres_list,
            ).distinct()
        if title:
            queryset = queryset.filter(title__icontains=title)
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset

        if self.action == "list":
            queryset = (
                queryset.prefetch_related("movie", "cinema_hall")
                .annotate(
                    capacity=F("cinema_hall__rows")
                    * F("cinema_hall__seats_in_row")
                )
                .annotate(tickets_available=F("capacity") - Count("tickets"))
                .order_by("id")
            )
        date_str = self.request.query_params.get("date")
        movie_id = self.request.query_params.get("movie")

        if date_str:
            queryset = queryset.filter(show_time__date=date_str)
        if movie_id:
            queryset = queryset.filter(movie_id=movie_id)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = self.queryset

        return queryset.prefetch_related(
            "tickets__movie_session",
            "tickets__movie_session__movie",
            "tickets__movie_session__cinema_hall"
        ).filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer
