from django.db import models

# Create your models here.

class PhotoAnalysis(models.Model):

    photo = models.OneToOneField(
        "pizxifyapp.FolderPhoto",
        on_delete=models.CASCADE,
        related_name="ai_analysis"
    )

    sharpness = models.FloatField()
    brightness = models.FloatField()

    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()

    blur_status = models.CharField(max_length=30)
    brightness_status = models.CharField(max_length=30)

    # Step 2 fields
    quality_score = models.FloatField(
        default=0
    )

    recommendation = models.CharField(
        max_length=30,
        default="Needs Review"
    )

    analyzed_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"Analysis for photo {self.photo_id}"


from django.db import models


class PhotoClassification(models.Model):

    photo = models.OneToOneField(
        "pizxifyapp.FolderPhoto",
        on_delete=models.CASCADE,
        related_name="ai_classification"
    )

    category = models.CharField(
        max_length=50,
        default="Other"
    )

    scene = models.CharField(
        max_length=100,
        default="Unknown"
    )

    photo_type = models.CharField(
        max_length=50,
        default="Other"
    )

    description = models.TextField(
        blank=True,
        default=""
    )

    group_name = models.CharField(
        max_length=100,
        default="Other"
    )

    confidence = models.FloatField(
        default=0
    )

    analyzed_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"Classification for Photo {self.photo_id}"


class FaceGroup(models.Model):

    folder = models.ForeignKey(
        "pizxifyapp.PhotoFolder",
        on_delete=models.CASCADE,
        related_name="face_groups"
    )

    name = models.CharField(
        max_length=100
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name


class PhotoFace(models.Model):

    photo = models.ForeignKey(
        "pizxifyapp.FolderPhoto",
        on_delete=models.CASCADE,
        related_name="detected_faces"
    )

    face_group = models.ForeignKey(
        FaceGroup,
        on_delete=models.CASCADE,
        related_name="faces",
        null=True,
        blank=True
    )

    # Face embedding will be stored here
    embedding = models.JSONField(
        null=True,
        blank=True
    )

    confidence = models.FloatField(
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Face in Photo {self.photo_id}"
