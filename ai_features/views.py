from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.shortcuts import redirect

from .services import classify_folder_photos
from pizxifyapp.models import (
    PhotoFolder,
    FolderPhoto
)

from .models import PhotoAnalysis
from .services import analyze_photo

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .services import suggest_album_layout

@require_POST
def analyze_folder_photos(
    request,
    folder_id
):

    # ---------------------------------------
    # CHECK ROLE
    # ---------------------------------------

    if request.session.get(
        "user_role"
    ) != "photographer":

        return redirect("login")

    # ---------------------------------------
    # GET USER
    # ---------------------------------------

    user_id = request.session.get(
        "user_id"
    )

    # ---------------------------------------
    # GET FOLDER
    # ---------------------------------------

    folder = get_object_or_404(
        PhotoFolder,
        id=folder_id,
        created_by_id=user_id
    )

    # ---------------------------------------
    # GET PHOTOS
    # ---------------------------------------

    photos = FolderPhoto.objects.filter(
        folder=folder
    )

    analyzed_count = 0
    failed_count = 0

    # ---------------------------------------
    # ANALYZE PHOTOS
    # ---------------------------------------

    for photo in photos:

        try:

            result = analyze_photo(
                photo.image.path
            )

            # -----------------------------------
            # SAVE / UPDATE DATABASE
            # -----------------------------------

            PhotoAnalysis.objects.update_or_create(

                photo=photo,

                defaults=result
            )

            analyzed_count += 1

        except Exception as e:

            print(
                f"AI analysis failed "
                f"for photo {photo.id}: {e}"
            )

            failed_count += 1

    # ---------------------------------------
    # MESSAGE
    # ---------------------------------------

    if failed_count:

        messages.warning(
            request,
            f"Analyzed {analyzed_count} photos. "
            f"{failed_count} photos could not be analyzed."
        )

    else:

        messages.success(
            request,
            f"Successfully analyzed "
            f"{analyzed_count} photos."
        )

    # ---------------------------------------
    # REDIRECT
    # ---------------------------------------

    return redirect(
        "folder_details",
        id=folder.id
    )


@require_GET
def suggest_album_layout_api(request):

    if request.session.get('user_role') != 'photographer':
        return JsonResponse(
            {
                'status': 'error',
                'message': 'Unauthorized'
            },
            status=403
        )

    try:
        photo_count = int(
            request.GET.get('photo_count', 0)
        )
    except (TypeError, ValueError):
        return JsonResponse(
            {
                'status': 'error',
                'message': 'Invalid photo count'
            },
            status=400
        )

    if photo_count <= 0:
        return JsonResponse(
            {
                'status': 'error',
                'message': 'Photo count must be greater than 0'
            },
            status=400
        )

    layout = suggest_album_layout(photo_count)

    return JsonResponse(
        {
            'status': 'success',
            'photo_count': photo_count,
            'total_pages': len(layout),
            'layout': layout
        }
    )
from django.shortcuts import redirect
from django.contrib import messages
from django.views.decorators.http import require_POST

from .services import group_folder_faces


@require_POST
def group_faces_api(request, folder_id):

    # ---------------------------------------
    # CHECK USER ROLE
    # ---------------------------------------

    if request.session.get("user_role") != "photographer":
        return redirect("login")

    user_id = request.session.get("user_id")

    try:

        # ---------------------------------------
        # RUN AI FACE GROUPING
        # ---------------------------------------

        result = group_folder_faces(
            folder_id=folder_id,
            user_id=user_id
        )

        # ---------------------------------------
        # SUCCESS MESSAGE
        # ---------------------------------------

        messages.success(
            request,
            (
                "AI Face Grouping Completed! "
                f"Photos Processed: {result['photos_processed']} | "
                f"Faces Detected: {result['faces_detected']} | "
                f"Groups Created: {result['groups_created']}"
            )
        )

    except ValueError as e:

        messages.error(
            request,
            str(e)
        )

    except Exception as e:

        print(
            f"AI face grouping error: {e}"
        )

        messages.error(
            request,
            "AI face grouping failed. Please try again."
        )

    # ---------------------------------------
    # GO BACK TO FOLDER
    # ---------------------------------------

    return redirect(
        "folder_details",
        id=folder_id
    )

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from pizxifyapp.models import PhotoFolder, FolderPhoto
from .models import FaceGroup, PhotoFace


def face_group_photos(request, folder_id, group_id):
    # Photographer only
    if request.session.get("user_role") != "photographer":
        return redirect("login")

    user_id = request.session.get("user_id")

    # Make sure folder belongs to logged-in photographer
    folder = get_object_or_404(
        PhotoFolder,
        id=folder_id,
        created_by_id=user_id
    )

    # Make sure group belongs to this folder
    face_group = get_object_or_404(
        FaceGroup,
        id=group_id,
        folder=folder
    )

    # Get all detected faces in this group
    face_records = (
        PhotoFace.objects
        .filter(face_group=face_group)
        .select_related("photo")
        .order_by("photo_id")
    )

    # Avoid showing the same photo multiple times
    photo_ids = []
    seen_photo_ids = set()

    for face in face_records:
        if face.photo_id not in seen_photo_ids:
            seen_photo_ids.add(face.photo_id)
            photo_ids.append(face.photo_id)

    photos = FolderPhoto.objects.filter(
        id__in=photo_ids,
        folder=folder
    ).order_by("id")

    context = {
        "folder": folder,
        "face_group": face_group,
        "photos": photos,
        "face_count": face_records.count(),
        "photo_count": photos.count(),
    }

    return render(
        request,
        "photographer/face_group_photos.html",
        context
    )



@require_POST
def classify_folder_photos_api(request, folder_id):

    if request.session.get("user_role") != "photographer":
        return redirect("login")

    user_id = request.session.get("user_id")

    try:
        result = classify_folder_photos(
            folder_id=folder_id,
            user_id=user_id
        )

        if result["classified_count"] > 0:
            messages.success(
                request,
                (
                    "AI Photo Classification Completed! "
                    f"Processed: {result['photos_processed']} | "
                    f"Classified: {result['classified_count']} | "
                    f"Failed: {result['failed_count']}"
                )
            )
        else:
            messages.warning(
                request,
                "AI Photo Classification could not be completed. "
                "Please check your Gemini API quota."
            )

    except ValueError as e:
        messages.error(request, str(e))

    except Exception as e:
        print(f"AI photo classification error: {e}")
        messages.error(
            request,
            "AI photo classification failed."
        )

    return redirect("folder_details", id=folder_id)