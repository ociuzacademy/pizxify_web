import cv2

from .face_grouping import face_app


def classify_photo(image_path):
    """
    AI-assisted photo classification.

    Uses the existing InsightFace model from
    the Pizxify face-grouping system.
    """

    # -----------------------------------------
    # Read image
    # -----------------------------------------

    image = cv2.imread(str(image_path))

    if image is None:
        raise ValueError(
            f"Unable to read image: {image_path}"
        )

    # -----------------------------------------
    # InsightFace face detection
    # -----------------------------------------

    faces = face_app.get(image)

    face_count = len(faces)

    # -----------------------------------------
    # Photo type
    # -----------------------------------------

    if face_count == 0:

        photo_type = "Landscape"

    elif face_count == 1:

        photo_type = "Portrait"

    else:

        photo_type = "Group Photo"

    # -----------------------------------------
    # Brightness
    # -----------------------------------------

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    brightness = float(gray.mean())

    # -----------------------------------------
    # Scene
    # -----------------------------------------

    if brightness < 80:

        scene = "Indoor"

    elif brightness > 170:

        scene = "Outdoor"

    else:

        scene = "Unknown"

    # -----------------------------------------
    # Category
    # -----------------------------------------

    if face_count >= 2:

        category = "Event"

    elif face_count == 1:

        category = "Portrait"

    else:

        category = "Nature"

    # -----------------------------------------
    # Description
    # -----------------------------------------

    if face_count == 0:

        description = (
            f"{scene} photograph without "
            f"detected people."
        )

    elif face_count == 1:

        description = (
            f"{scene} portrait photograph "
            f"with one detected person."
        )

    else:

        description = (
            f"{scene} group photograph with "
            f"{face_count} detected people."
        )

    # -----------------------------------------
    # Confidence
    # -----------------------------------------

    if face_count >= 2:

        confidence = 90.0

    elif face_count == 1:

        confidence = 88.0

    else:

        confidence = 70.0

    return {
        "category": category,
        "scene": scene,
        "photo_type": photo_type,
        "description": description,
        "confidence": confidence,
    }