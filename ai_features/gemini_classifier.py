import os
import json
import mimetypes

from dotenv import load_dotenv
from google import genai


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not configured.")

client = genai.Client(
    api_key=GEMINI_API_KEY
)


def classify_image_with_gemini(image_path):
    """
    Classify a photo using Gemini Vision.
    """

    mime_type, _ = mimetypes.guess_type(image_path)

    if not mime_type:
        mime_type = "image/jpeg"

    with open(image_path, "rb") as image_file:
        image_bytes = image_file.read()

    prompt = """
You are an AI photo classification system for a professional
photographer's photo album management application.

Analyze the provided image and return ONLY valid JSON.

Classify the image into:

1. category
2. scene
3. photo_type
4. description
5. confidence

Use practical categories such as:

Wedding
Birthday
Portrait
Family
Event
Travel
Nature
Food
Product
Sports
Other

Scene examples:

Indoor
Outdoor
Beach
Garden
Hall
Stage
Street
Restaurant
Studio
Unknown

Photo type examples:

Portrait
Couple
Group Photo
Landscape
Event Photo
Product Photo
Food Photo
Other

Return exactly this JSON structure:

{
    "category": "Wedding",
    "scene": "Outdoor",
    "photo_type": "Group Photo",
    "description": "A group of people attending a wedding ceremony outdoors.",
    "confidence": 94.5
}

Confidence must be a number between 0 and 100.

Do not add markdown.
Do not add explanations outside the JSON.
"""

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=[
            {
                "text": prompt
            },
            {
                "inline_data": {
                    "mime_type": mime_type,
                    "data": image_bytes
                }
            }
        ]
    )

    text = response.text.strip()

    # Remove accidental markdown fences
    if text.startswith("```"):
        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        raise ValueError(
            f"Gemini returned invalid JSON: {text}"
        )

    return {
        "category": result.get("category", "Other"),
        "scene": result.get("scene", "Unknown"),
        "photo_type": result.get(
            "photo_type",
            "Other"
        ),
        "description": result.get(
            "description",
            ""
        ),
        "confidence": float(
            result.get("confidence", 0)
        ),
    }