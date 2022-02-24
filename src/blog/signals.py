from os import getcwd, remove
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from django.utils.text import slugify
from extensions.code_generator import slug_generator
from .models import Blog


@receiver(pre_save, sender=Blog)
def save_slug_blog(sender, instance, *args, **kwargs):
    if len(instance.slug) <= 5:
        instance.slug = slugify(slug_generator(10))


@receiver(post_delete, sender=Blog)
def delete_media_blog(sender, instance, *args, **kwargs):
    remove(getcwd() + instance.image.url)
