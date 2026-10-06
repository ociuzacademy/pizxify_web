import cv2
import numpy as np

from insightface.app import FaceAnalysis
from sklearn.cluster import DBSCAN


# Load InsightFace once
face_app = FaceAnalysis(
    name="buffalo_l",
    providers=["CPUExecutionProvider"]
)

face_app.prepare(
    ctx_id=0,
    det_size=(640, 640)
)


def extract_faces(image_path):
    """
    Detect faces and generate normalized face embeddings
    from a single image.
    """

    image = cv2.imread(str(image_path))

    if image is None:
        raise ValueError(
            f"Unable to read image: {image_path}"
        )

    faces = face_app.get(image)

    results = []

    for face_index, face in enumerate(faces):

        bbox = face.bbox.astype(int)

        embedding = face.embedding.astype(
            np.float32
        )

        # Normalize embedding
        norm = np.linalg.norm(embedding)

        if norm > 0:
            embedding = embedding / norm

        results.append({
            "face_id": face_index,
            "bbox": [
                int(bbox[0]),
                int(bbox[1]),
                int(bbox[2]),
                int(bbox[3])
            ],
            "confidence": float(face.det_score),
            "embedding": embedding.tolist()
        })

    return results

def group_embeddings(face_records, eps=0.45):
    """
    Group similar faces using DBSCAN.
    """

    if not face_records:
        return []

    embeddings = np.array([
        record["embedding"]
        for record in face_records
    ], dtype=np.float32)

    clustering = DBSCAN(
        eps=eps,
        min_samples=2,
        metric="cosine"
    ).fit(embeddings)

    labels = clustering.labels_

    for record, label in zip(face_records, labels):

        if label == -1:
            record["group"] = "Unknown"
        else:
            record["group"] = f"Person {label + 1}"

    return face_records