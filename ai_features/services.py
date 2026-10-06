import cv2
import numpy as np


def calculate_quality_score(
    sharpness,
    brightness,
    blur_status,
    brightness_status
):
    """
    Calculate an overall photo quality score
    from 0 to 100.

    This is a heuristic score based on:
    - Sharpness
    - Brightness
    - Blur classification
    """

    # ---------------------------------------
    # SHARPNESS SCORE
    # ---------------------------------------

    # 300 is treated as a strong sharpness level.
    # Anything above 300 gets 100.
    sharpness_score = min(
        (sharpness / 300) * 100,
        100
    )

    # ---------------------------------------
    # BRIGHTNESS SCORE
    # ---------------------------------------

    # Ideal average brightness is around 128.
    brightness_difference = abs(
        brightness - 128
    )

    brightness_score = max(
        0,
        100 - (
            brightness_difference / 128
        ) * 100
    )

    # ---------------------------------------
    # BLUR PENALTY
    # ---------------------------------------

    if blur_status == "Blurry":

        sharpness_score *= 0.30

    elif blur_status == "Moderately sharp":

        sharpness_score *= 0.75

    # ---------------------------------------
    # BRIGHTNESS PENALTY
    # ---------------------------------------

    if brightness_status == "Too dark":

        brightness_score *= 0.60

    elif brightness_status == "Too bright":

        brightness_score *= 0.70

    # ---------------------------------------
    # FINAL SCORE
    # ---------------------------------------

    quality_score = (
        sharpness_score * 0.70
        +
        brightness_score * 0.30
    )

    quality_score = round(
        min(max(quality_score, 0), 100),
        2
    )

    # ---------------------------------------
    # RECOMMENDATION
    # ---------------------------------------

    if quality_score >= 75:

        recommendation = "Recommended"

    elif quality_score >= 50:

        recommendation = "Review"

    else:

        recommendation = "Needs Review"

    return quality_score, recommendation


def analyze_photo(image_path):

    # ---------------------------------------
    # READ IMAGE
    # ---------------------------------------

    image = cv2.imread(
        str(image_path)
    )

    if image is None:

        raise ValueError(
            "Unable to read the image."
        )

    # ---------------------------------------
    # GRAYSCALE
    # ---------------------------------------

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    # ---------------------------------------
    # SHARPNESS
    # ---------------------------------------

    sharpness = float(
        cv2.Laplacian(
            gray,
            cv2.CV_64F
        ).var()
    )

    # ---------------------------------------
    # BRIGHTNESS
    # ---------------------------------------

    brightness = float(
        np.mean(gray)
    )

    # ---------------------------------------
    # DIMENSIONS
    # ---------------------------------------

    height, width = gray.shape

    # ---------------------------------------
    # BLUR STATUS
    # ---------------------------------------

    if sharpness < 50:

        blur_status = "Blurry"

    elif sharpness < 150:

        blur_status = "Moderately sharp"

    else:

        blur_status = "Sharp"

    # ---------------------------------------
    # BRIGHTNESS STATUS
    # ---------------------------------------

    if brightness < 70:

        brightness_status = "Too dark"

    elif brightness > 190:

        brightness_status = "Too bright"

    else:

        brightness_status = "Normal"

    # ---------------------------------------
    # QUALITY SCORE
    # ---------------------------------------

    quality_score, recommendation = (
        calculate_quality_score(
            sharpness,
            brightness,
            blur_status,
            brightness_status
        )
    )

    # ---------------------------------------
    # RESULT
    # ---------------------------------------

    return {

        "sharpness": round(
            sharpness,
            2
        ),

        "brightness": round(
            brightness,
            2
        ),

        "width": width,

        "height": height,

        "blur_status": blur_status,

        "brightness_status": brightness_status,

        "quality_score": quality_score,

        "recommendation": recommendation,
    }

def suggest_album_layout(photo_count):
    """
    Suggest an album page layout based on the number
    of photos available.

    Maximum recommended photos per page = 4.
    The layout is kept visually balanced.
    """

    if photo_count <= 0:
        return []

    # Common balanced layouts
    layouts = {
        1: [1],
        2: [1, 1],
        3: [1, 2],
        4: [2, 2],
        5: [1, 2, 2],
        6: [1, 2, 2, 1],
        7: [1, 2, 3, 1],
        8: [1, 2, 3, 2],
        9: [1, 2, 3, 2, 1],
        10: [1, 2, 4, 2, 1],
        11: [1, 2, 3, 3, 2],
        12: [1, 2, 3, 3, 2, 1],
        13: [1, 2, 3, 4, 2, 1],
        14: [1, 2, 3, 4, 3, 1],
        15: [1, 2, 3, 4, 3, 2],
        16: [1, 2, 3, 4, 3, 2, 1],
    }

    if photo_count in layouts:
        return layouts[photo_count]

    # For larger photo collections,
    # distribute photos with a maximum of 4 per page.
    result = []

    remaining = photo_count

    while remaining > 0:

        if remaining >= 4:
            result.append(4)
            remaining -= 4

        elif remaining == 3:
            result.append(3)
            remaining -= 3

        elif remaining == 2:
            result.append(2)
            remaining -= 2

        elif remaining == 1:
            # If the last page has one photo,
            # try to balance with the previous page.
            if result and result[-1] > 1:
                result[-1] -= 1
                result.append(2)
            else:
                result.append(1)

            remaining -= 1

    return result

from django.db import transaction

from pizxifyapp.models import PhotoFolder, FolderPhoto
from .models import FaceGroup, PhotoFace
from .face_grouping import extract_faces, group_embeddings


def group_folder_faces(folder_id, user_id):
    """
    Detect and group faces from all photos
    inside a Pizxify folder.
    """

    # -------------------------------------------------
    # 1. Get the folder and verify ownership
    # -------------------------------------------------

    folder = PhotoFolder.objects.filter(
        id=folder_id,
        created_by_id=user_id
    ).first()

    if not folder:
        raise ValueError(
            "Folder not found or you do not have permission."
        )

    # -------------------------------------------------
    # 2. Get all photos in the folder
    # -------------------------------------------------

    photos = list(
        FolderPhoto.objects.filter(
            folder=folder
        ).order_by("id")
    )

    if not photos:
        return {
            "photos_processed": 0,
            "faces_detected": 0,
            "groups_created": 0,
        }

    # -------------------------------------------------
    # 3. Detect faces and generate embeddings
    # -------------------------------------------------

    face_records = []

    for photo in photos:

        try:

            faces = extract_faces(
                photo.image.path
            )

            for face in faces:

                face_records.append({
                    "photo": photo,
                    "face_id": face["face_id"],
                    "bbox": face["bbox"],
                    "confidence": face["confidence"],
                    "embedding": face["embedding"],
                })

        except Exception as e:

            print(
                f"Face detection failed "
                f"for photo {photo.id}: {e}"
            )

    # -------------------------------------------------
    # 4. No faces found
    # -------------------------------------------------

    if not face_records:

        return {
            "photos_processed": len(photos),
            "faces_detected": 0,
            "groups_created": 0,
        }

    # -------------------------------------------------
    # 5. Prepare data for DBSCAN
    # -------------------------------------------------

    clustering_records = [
        {
            "photo_id": record["photo"].id,
            "face_id": record["face_id"],
            "bbox": record["bbox"],
            "confidence": record["confidence"],
            "embedding": record["embedding"],
        }
        for record in face_records
    ]

    # -------------------------------------------------
    # 6. Group similar faces
    # -------------------------------------------------

    grouped_records = group_embeddings(
        clustering_records
    )

    # -------------------------------------------------
    # 7. Save results in database
    # -------------------------------------------------

    with transaction.atomic():

        # Remove previous grouping results
        PhotoFace.objects.filter(
            photo__folder=folder
        ).delete()

        FaceGroup.objects.filter(
            folder=folder
        ).delete()

        # Get unique group names
        group_names = sorted({
            record["group"]
            for record in grouped_records
        })

        # Create FaceGroup records
        group_objects = {}

        for group_name in group_names:

            group = FaceGroup.objects.create(
                folder=folder,
                name=group_name
            )

            group_objects[group_name] = group

        # Create PhotoFace records
        for record in grouped_records:

            photo = FolderPhoto.objects.get(
                id=record["photo_id"]
            )

            PhotoFace.objects.create(
                photo=photo,
                face_group=group_objects[
                    record["group"]
                ],
                embedding=record["embedding"],
                confidence=record["confidence"]
            )

    # -------------------------------------------------
    # 8. Return summary
    # -------------------------------------------------

    return {
        "photos_processed": len(photos),
        "faces_detected": len(grouped_records),
        "groups_created": len(group_objects),
    }

from .gemini_classifier import classify_image_with_gemini
from .models import PhotoClassification
def classify_folder_photos(folder_id, user_id):
    """
    Classify all photos in a folder using Gemini Vision
    and save the results into PhotoClassification.
    """

    folder = PhotoFolder.objects.filter(
        id=folder_id,
        created_by_id=user_id
    ).first()

    if not folder:
        raise ValueError(
            "Folder not found or you do not have permission."
        )

    photos = list(
        FolderPhoto.objects
        .filter(folder=folder)
        .order_by("id")
    )

    if not photos:
        return {
            "photos_processed": 0,
            "classified_count": 0,
            "failed_count": 0,
        }

    classified_count = 0
    failed_count = 0

    for photo in photos:

        try:

            result = classify_image_with_gemini(
                photo.image.path
            )

            PhotoClassification.objects.update_or_create(
                photo=photo,
                defaults={
                    "category": result["category"],
                    "scene": result["scene"],
                    "photo_type": result["photo_type"],
                    "description": result["description"],
                    "confidence": result["confidence"],
                }
            )

            classified_count += 1

        except Exception as e:

            print(
                f"Photo classification failed "
                f"for photo {photo.id}: {e}"
            )

            failed_count += 1

    return {
        "photos_processed": len(photos),
        "classified_count": classified_count,
        "failed_count": failed_count,
    }