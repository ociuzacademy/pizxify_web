
from django.urls import path
from . import views

urlpatterns = [
    path(
        "analyze-folder/<int:folder_id>/",
        views.analyze_folder_photos,
        name="analyze_folder_photos"
    ),
    path(
        'suggest-album-layout/',
        views.suggest_album_layout_api,
        name='suggest_album_layout'
    ),
    path(
    'group-faces/<int:folder_id>/',
    views.group_faces_api,
    name='group_faces'),
    path(
    'face-group/<int:folder_id>/<int:group_id>/',
    views.face_group_photos,
    name='face_group_photos'
),

path(
    'classify-photos/<int:folder_id>/',
    views.classify_folder_photos_api,
    name='classify_folder_photos'
),
]