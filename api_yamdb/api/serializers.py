import re

from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from reviews.models import (Category,
                            Comment,
                            Genre,
                            Review,
                            Title)
from users.models import User, MAX_LENGTH_EMAIL, MAX_LENGTH_NAME


class SignUpSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=MAX_LENGTH_NAME)
    email = serializers.EmailField(max_length=MAX_LENGTH_EMAIL)

    class Meta:
        model = User
        fields = ('username', 'email')

    def validate_username(self, value):
        name = value.lower()
        if name == 'me':
            raise serializers.ValidationError(
                'Невозможно создать пользователя с именем me'
            )
        elif re.fullmatch(r'^[\w.@+-]+\Z', value):
            return value
        raise serializers.ValidationError(
            'Невозможно создать пользователя с таким набором симвлолов'
        )

    def validate(self, data):
        if not ('username' or 'email') in data:
            raise serializers.ValidationError(
                'Нет обязательных ключей'
            )
        username = data['username']
        email = data['email']
        if (User.objects.filter(**data).exists()
            or (not User.objects.filter(username=username).exists()
                and not User.objects.filter(email=email).exists())):
            return data
        raise serializers.ValidationError(
            'Невозможно создать пользователя с такими значениями'
            '"username" и "email"'
        )


class TokenSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=MAX_LENGTH_NAME)

    class Meta:
        model = User
        fields = ('username', 'confirmation_code')

    def validate(self, data):
        user = get_object_or_404(User, username=data['username'])
        if user.confirmation_code != data['confirmation_code']:
            raise serializers.ValidationError('Код подтверждения не верен')
        return data


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'bio',
            'role',
        )

    def validate_username(self, value):
        if re.fullmatch(r'^[\w.@+-]+\Z', value):
            return value
        raise serializers.ValidationError(
            'Невозможно создать пользователя с таким набором симвлолов'
        )


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        exclude = ('id',)


class GenreSerializer(serializers.ModelSerializer):

    class Meta:
        model = Genre
        exclude = ('id',)


class CreateTitleSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Category.objects.all()
    )
    genre = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Genre.objects.all(),
        many=True
    )

    class Meta:
        model = Title
        fields = '__all__'

    def validate_year(self, value):
        current_year = timezone.now().year
        if value > current_year:
            raise serializers.ValidationError(
                'Год выпуска произведения не может быть в будущем'
            )
        return value


class TitleSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    genre = GenreSerializer(many=True)
    rating = serializers.IntegerField()

    class Meta:
        model = Title
        fields = '__all__'


class ReviewSerializer(serializers.ModelSerializer):
    title = serializers.SlugRelatedField(
        slug_field='name',
        read_only=True
    )
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    def validate_score(self, value):
        if 0 > value > 10:
            raise serializers.ValidationError('Оценка по 10-бальной шкале!')
        return value

    def validate(self, data):
        request = self.context['request']
        author = request.user
        title_id = self.context.get('view').kwargs.get('title_id')
        title = get_object_or_404(Title, pk=title_id)
        if (
            request.method == 'POST'
            and Review.objects.filter(title=title, author=author).exists()
        ):
            raise ValidationError('Может существовать только один отзыв!')
        return data

    class Meta:
        fields = '__all__'
        model = Review


class CommentSerializer(serializers.ModelSerializer):
    review = serializers.SlugRelatedField(
        slug_field='text',
        read_only=True
    )
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        fields = '__all__'
        model = Comment
