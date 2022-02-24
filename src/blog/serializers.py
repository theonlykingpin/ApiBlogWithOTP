from rest_framework import serializers
from blog.models import Blog, Category


class BlogsListSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField(method_name='get_author')
    category = serializers.SerializerMethodField(method_name='get_category')

    def get_author(self, obj):
        return {"first_name": obj.author.first_name, "last_name": obj.author.last_name}

    def get_category(self, obj):
        return [cat.title for cat in obj.category.get_queryset()]

    class Meta:
        model = Blog
        exclude = ['id', 'likes', 'create', 'body', 'status', 'updated', 'publish', 'visits', 'special']


class BlogCreateSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(many=True, queryset=Category.objects.all(), slug_field='id')

    class Meta:
        model = Blog
        fields = ['title', 'body', 'image', 'summary', 'category', 'publish', 'special', 'status']


class BlogDetailUpdateDeleteSerializer(serializers.ModelSerializer):
    slug = serializers.ReadOnlyField()
    author = serializers.SerializerMethodField(method_name='get_author')
    likes = serializers.SerializerMethodField(method_name='get_likes')

    def get_author(self, obj):
        return {"first_name": obj.author.first_name, "last_name": obj.author.last_name}

    def get_likes(self, obj):
        return obj.likes.count()

    class Meta:
        model = Blog
        exclude = ["create", "updated"]
        read_only_fields = ["likes"]


class CategoryListSerializer(serializers.ModelSerializer):
    parent = serializers.SerializerMethodField(method_name='get_parent')

    def get_parent(self, obj):
        return {"title": str(obj.parent)}

    class Meta:
        model = Category
        fields = ["parent", "title"]
