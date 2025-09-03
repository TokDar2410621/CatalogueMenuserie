# pages/views.py
from django.http import JsonResponse
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

def storage_check(request):
    info = {
        "storage_backend": default_storage.__class__.__module__ + "." + default_storage.__class__.__name__,
        "media_url": getattr(request, "build_absolute_uri", lambda x=None: None)(None),
    }
    # Essayons d'écrire un petit fichier pour vérifier S3
    try:
        default_storage.save("diagnostic_test.txt", ContentFile(b"hello s3"))
        info["write_test"] = "ok (diagnostic_test.txt ecrit)"
    except Exception as e:
        info["write_test"] = f"KO: {e.__class__.__name__}: {e}"
    return JsonResponse(info)
