from django.core.files.storage import Storage
from vercel.blob import BlobClient


class VercelBlobStorage(Storage):
    """Store user-uploaded product images in the project's public Blob store."""

    def _save(self, name, content):
        content.open()
        result = BlobClient().put(
            name,
            content.read(),
            access='public',
            content_type=getattr(content, 'content_type', None),
            add_random_suffix=True,
            cache_control_max_age=31536000,
        )
        return result.url

    def delete(self, name):
        if name:
            BlobClient().delete(name)

    def exists(self, name):
        # Blob adds a random suffix, so uploads never overwrite one another.
        return False

    def url(self, name):
        return name

