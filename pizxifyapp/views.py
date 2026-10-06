from random import random
from urllib import request

from django.shortcuts import render, redirect
from .models import *
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re

from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.shortcuts import render, redirect

from .models import UserRegister
import re

from ai_features.models import PhotoAnalysis
# Create your views here.

#Index

def index(request):
    return render(request,'index.html')

#About

def about(request):
    return render(request,'about.html')

#Register As Client, Photographer, Freelance

def register(request):

    if request.method == "POST":

        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        phone = request.POST.get("phone", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")
        role = request.POST.get("user_type", "").strip()

        # Full Name Validation
        if not full_name:
            messages.error(request, "Full name is required.")
            return redirect('register')

        if len(full_name) < 2:
            messages.error(request, "Full name must contain at least 2 characters.")
            return redirect('register')

        if not re.match(r'^[A-Za-z ]+$', full_name):
            messages.error(request, "Full name should contain only letters and spaces.")
            return redirect('register')

        # Email Validation
        if not email:
            messages.error(request, "Email is required.")
            return redirect('register')

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Please enter a valid email address.")
            return redirect('register')

        if UserRegister.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect('register')

        # Phone Validation
        if not phone:
            messages.error(request, "Phone number is required.")
            return redirect('register')

        if not re.match(r'^\d{10}$', phone):
            messages.error(request, "Phone number must be exactly 10 digits.")
            return redirect('register')

        # Password Validation
        if not password:
            messages.error(request, "Password is required.")
            return redirect('register')

        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return redirect('register')

        if not re.search(r'[A-Z]', password):
            messages.error(request, "Password must contain at least one uppercase letter.")
            return redirect('register')

        if not re.search(r'[a-z]', password):
            messages.error(request, "Password must contain at least one lowercase letter.")
            return redirect('register')

        if not re.search(r'\d', password):
            messages.error(request, "Password must contain at least one number.")
            return redirect('register')

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            messages.error(request, "Password must contain at least one special character.")
            return redirect('register')

        # Confirm Password Validation
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('register')

        # Role Validation
        allowed_roles = ['photographer', 'client', 'freelance']

        if role not in allowed_roles:
            messages.error(request, "Invalid account type.")
            return redirect('register')

        # Save User
        UserRegister.objects.create(
            full_name=full_name,
            email=email,
            phone=phone,
            password=make_password(password),
            role=role
        )

        messages.success(request, "Registration successful.")
        return redirect('login')

    return render(request, 'register.html')

#Login

def login(request):

    if request.method == "POST":

        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        if not email or not password:
            messages.error(request, "Email and Password are required.")
            return redirect('login')

        # Photographer / Client / Freelance Login (Hashed Password)
        try:
            user = UserRegister.objects.get(email=email)

            if check_password(password, user.password):

                request.session['user_id'] = user.id
                request.session['user_name'] = user.full_name
                request.session['user_role'] = user.role
                if request.POST.get('remember_me'):
                     request.session.set_expiry(60 * 60 * 24 * 30)   # 30 days
                else:
                     request.session.set_expiry(0)  # Session expires on browser close
                if user.role == 'photographer':
                    return redirect('photographer_dashboard')

                elif user.role == 'client':
                    return redirect('client_dashboard')

                elif user.role == 'freelance':
                    return redirect('freelance_dashboard')

            else:
                messages.error(request, "Invalid Password")
                return redirect('login')

        except UserRegister.DoesNotExist:
            messages.error(request, "Account not found")
            return redirect('login')

    return render(request, 'login.html')

#Forgot Password, Verify OTP, Reset Password
import random
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings

from .models import UserRegister


def forgot_password(request):

    if request.method == "POST":

        email = request.POST.get("email")

        try:

            user = UserRegister.objects.get(email=email)

            otp = str(random.randint(100000, 999999))

            request.session["reset_email"] = email
            request.session["reset_otp"] = otp

            send_mail(
                subject="Pizxify Password Reset OTP",
                message=f"Your OTP is {otp}. It is valid for 5 minutes.",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )

            messages.success(
                request,
                "OTP sent successfully."
            )

            return redirect("verify_otp")

        except UserRegister.DoesNotExist:

            messages.error(
                request,
                "Email not registered. Please register first."
            )

    return render(
        request,
        "forgot_password.html"
    )


def verify_otp(request):

    if request.method == "POST":

        entered_otp = request.POST.get("otp")

        session_otp = request.session.get("reset_otp")

        if entered_otp == session_otp:

            messages.success(
                request,
                "OTP Verified."
            )

            return redirect("reset_password")

        else:

            messages.error(
                request,
                "Invalid OTP."
            )

    return render(
        request,
        "verify_otp.html"
    )


def reset_password(request):

    email = request.session.get("reset_email")

    if not email:

        messages.error(
            request,
            "Password reset session expired."
        )

        return redirect("forgot_password")

    if request.method == "POST":

        password = request.POST.get(
            "password",
            ""
        )

        confirm_password = request.POST.get(
            "confirm_password",
            ""
        )

        # Confirm Password Validation

        if password != confirm_password:

            messages.error(
                request,
                "Passwords do not match."
            )

            return redirect(
                "reset_password"
            )

        # Password Validation

        if len(password) < 8:

            messages.error(
                request,
                "Password must be at least 8 characters long."
            )

            return redirect(
                "reset_password"
            )

        if not re.search(r'[A-Z]', password):

            messages.error(
                request,
                "Password must contain at least one uppercase letter."
            )

            return redirect(
                "reset_password"
            )

        if not re.search(r'[a-z]', password):

            messages.error(
                request,
                "Password must contain at least one lowercase letter."
            )

            return redirect(
                "reset_password"
            )

        if not re.search(r'\d', password):

            messages.error(
                request,
                "Password must contain at least one number."
            )

            return redirect(
                "reset_password"
            )

        if not re.search(
            r'[!@#$%^&*(),.?":{}|<>]',
            password
        ):

            messages.error(
                request,
                "Password must contain at least one special character."
            )

            return redirect(
                "reset_password"
            )

        user = UserRegister.objects.get(
            email=email
        )

        # Save password in hashed format

        user.password = make_password(
            password
        )

        user.save()

        # Clear session

        request.session.pop(
            "reset_email",
            None
        )

        request.session.pop(
            "reset_otp",
            None
        )

        messages.success(
            request,
            "Password updated successfully. Please login."
        )

        return redirect(
            "login"
        )

    return render(
        request,
        "reset_password.html"
    )

#Logout

def logout(request):

    request.session.flush()

    messages.success(request, "Logged out successfully.")

    return redirect('login')


# Dashboard Views for Photographer, Client, Freelance



def photographer_dashboard(request):

    if not request.session.get('user_id'):
        return redirect('login')

    if request.session.get('user_role') != 'photographer':
        return redirect('login')

    return render(request, 'photographer/photographer_dashboard.html')


def client_dashboard(request):

    if not request.session.get('user_id'):
        return redirect('login')

    if request.session.get('user_role') != 'client':
        return redirect('login')

    return render(request, 'client/client_dashboard.html')


def freelance_dashboard(request):

    if not request.session.get('user_id'):
        return redirect('login')

    if request.session.get('user_role') != 'freelance':
        return redirect('login')

    return render(request, 'freelance/freelance_dashboard.html')


#Photographer

def photographer_profile(request):

    if request.session.get('user_role') != 'photographer':
        return redirect('login')

    user = UserRegister.objects.get(
        id=request.session.get('user_id')
    )

    if request.method == "POST":

        user.full_name = request.POST.get('full_name')
        user.phone = request.POST.get('phone')
        user.place = request.POST.get('place')
        user.address = request.POST.get('address')

        if 'profile_pic' in request.FILES:
            user.profile_pic = request.FILES['profile_pic']

        user.save()

        messages.success(
            request,
            "Profile updated successfully."
        )

        return redirect('photographer_profile')

    return render(
        request,
        'photographer/profile.html',
        {'user': user}
    )

def create_folder(request):

    if request.session.get('user_role') != 'photographer':
        return redirect('login')

    if request.method == "POST":

        folder_id = request.POST.get('folder_id').strip()
        password = request.POST.get('password').strip()

        if PhotoFolder.objects.filter(password=password).exists():
            messages.error(request, "Folder password already exists. Please use another password.")
            return redirect('create_folder')

        PhotoFolder.objects.create(
            folder_id=folder_id,
            password=password,
            created_by_id=request.session['user_id']
        )

        messages.success(request, "Folder created successfully.")
        return redirect('view_folders')

    return render(request, 'photographer/create_folder.html')

def view_folders(request):

    if request.session.get('user_role') != 'photographer':
        return redirect('login')

    folders = PhotoFolder.objects.filter(
        created_by_id=request.session['user_id']
    ).order_by('-id')

    return render(
        request,
        'photographer/view_folders.html',
        {'folders': folders}
    )

def edit_folder(request, id):

    if request.session.get('user_role') != 'photographer':
        return redirect('login')

    folder = PhotoFolder.objects.get(id=id)

    if request.method == "POST":

        folder_id = request.POST.get('folder_id').strip()
        password = request.POST.get('password').strip()

        if PhotoFolder.objects.filter(password=password).exclude(id=id).exists():
            messages.error(request, "Folder password already exists. Please use another password.")
            return redirect('edit_folder', id=id)

        folder.folder_id = folder_id
        folder.password = password
        folder.save()

        messages.success(request, "Folder updated successfully.")
        return redirect('view_folders')

    return render(
        request,
        'photographer/edit_folder.html',
        {'folder': folder}
    )

def delete_folder(request, id):

    if request.session.get('user_role') != 'photographer':
        return redirect('login')

    folder = PhotoFolder.objects.get(id=id)

    if request.method == "POST":

        password = request.POST.get('password')

        if password == folder.password:

            folder.delete()

            messages.success(
                request,
                "Folder deleted successfully."
            )

        else:

            messages.error(
                request,
                "Incorrect folder password."
            )

        return redirect('view_folders')

    return redirect('view_folders')


def upload_folder_photos(request, id):

    if request.session.get('user_role') != 'photographer':
        return redirect('login')

    folder = PhotoFolder.objects.get(id=id)

    if request.method == "POST":

        photos = request.FILES.getlist('photos')

        for photo in photos:

            FolderPhoto.objects.create(
                folder=folder,
                image=photo
            )

        messages.success(
            request,
            "Photos uploaded successfully."
        )

        return redirect(
            'folder_details',
            id=folder.id
        )

    return render(
        request,
        'photographer/upload_photos.html',
        {'folder': folder}
    )

from django.shortcuts import render, redirect, get_object_or_404

from .models import (
    PhotoFolder,
    FolderPhoto,
    PhotoLike,
    Album,
)

from ai_features.models import (
    PhotoAnalysis,
    FaceGroup,
    PhotoFace,
)


from django.shortcuts import render, redirect, get_object_or_404

from .models import (
    PhotoFolder,
    FolderPhoto,
    PhotoLike,
    Album,
)

from ai_features.models import (
    PhotoAnalysis,
    FaceGroup,
    PhotoFace,
)


def folder_details(request, id):

    # ---------------------------------------
    # CHECK USER ROLE
    # ---------------------------------------

    if request.session.get("user_role") != "photographer":
        return redirect("login")

    # ---------------------------------------
    # GET FOLDER
    # ---------------------------------------

    folder = get_object_or_404(
        PhotoFolder,
        id=id,
        created_by_id=request.session.get("user_id")
    )

    # ---------------------------------------
    # GET ALL PHOTOS
    # ---------------------------------------

    all_photos = list(
        FolderPhoto.objects
        .filter(folder=folder)
        .order_by("id")
    )

    # ---------------------------------------
    # GET AI ANALYSIS
    # ---------------------------------------

    analysis_by_photo = {
        analysis.photo_id: analysis
        for analysis in PhotoAnalysis.objects.filter(
            photo__in=all_photos
        )
    }

    # ---------------------------------------
    # ATTACH ANALYSIS TO PHOTO
    # ---------------------------------------

    for photo in all_photos:

        photo.analysis_result = (
            analysis_by_photo.get(photo.id)
        )

    # ---------------------------------------
    # GET PHOTO FILTER
    # ---------------------------------------

    current_filter = request.GET.get(
        "filter",
        "all"
    )

    # ---------------------------------------
    # FILTER PHOTOS
    # ---------------------------------------

    if current_filter == "recommended":

        photos = [
            photo
            for photo in all_photos
            if photo.analysis_result
            and photo.analysis_result.recommendation
            == "Recommended"
        ]

    elif current_filter == "review":

        photos = [
            photo
            for photo in all_photos
            if photo.analysis_result
            and photo.analysis_result.recommendation
            == "Review"
        ]

    elif current_filter == "needs_review":

        photos = [
            photo
            for photo in all_photos
            if photo.analysis_result
            and photo.analysis_result.recommendation
            == "Needs Review"
        ]

    else:

        photos = all_photos

    # ---------------------------------------
    # AI ANALYSIS COUNTS
    # ---------------------------------------

    analyzed_count = sum(
        1
        for photo in all_photos
        if photo.analysis_result
    )

    recommended_count = sum(
        1
        for photo in all_photos
        if photo.analysis_result
        and photo.analysis_result.recommendation
        == "Recommended"
    )

    review_count = sum(
        1
        for photo in all_photos
        if photo.analysis_result
        and photo.analysis_result.recommendation
        == "Review"
    )

    needs_review_count = sum(
        1
        for photo in all_photos
        if photo.analysis_result
        and photo.analysis_result.recommendation
        == "Needs Review"
    )

    # ---------------------------------------
    # ALBUMS
    # ---------------------------------------

    albums = Album.objects.filter(
        folder=folder
    ).order_by("id")

    # ---------------------------------------
    # LIKES
    # ---------------------------------------

    liked_count = PhotoLike.objects.filter(
        photo__folder=folder
    ).count()

    # ---------------------------------------
    # AI FACE GROUPING
    # ---------------------------------------

    face_groups = (
        FaceGroup.objects
        .filter(folder=folder)
        .prefetch_related("faces")
        .order_by("id")
    )

    # ---------------------------------------
    # TOTAL DETECTED FACES
    # ---------------------------------------

    face_count = PhotoFace.objects.filter(
        photo__folder=folder
    ).count()

    # ---------------------------------------
    # PEOPLE GROUP COUNT
    # ---------------------------------------
    # Exclude "Unknown" because Unknown
    # is not an actual identified person.

    people_group_count = face_groups.exclude(
        name="Unknown"
    ).count()

    # ---------------------------------------
    # UNKNOWN FACE COUNT
    # ---------------------------------------

    unknown_group = face_groups.filter(
        name="Unknown"
    ).first()

    if unknown_group:
        unknown_face_count = unknown_group.faces.count()
    else:
        unknown_face_count = 0

    # ---------------------------------------
    # CONTEXT
    # ---------------------------------------

    context = {

        # Folder
        "folder": folder,

        # Photos
        "photos": photos,

        "all_photos_count": len(all_photos),

        # Likes
        "liked_count": liked_count,

        # Albums
        "albums": albums,

        # AI Photo Analysis
        "analyzed_count": analyzed_count,

        "recommended_count": recommended_count,

        "review_count": review_count,

        "needs_review_count": needs_review_count,

        "current_filter": current_filter,

        # AI Face Grouping
        "face_count": face_count,

        "face_groups": face_groups,

        "people_group_count": people_group_count,

        "unknown_face_count": unknown_face_count,
    }

    # ---------------------------------------
    # RENDER
    # ---------------------------------------

    return render(
        request,
        "photographer/folder_details.html",
        context
    )

def delete_photo(request, id):

    if request.session.get('user_role') != 'photographer':
        return redirect('login')

    photo = FolderPhoto.objects.get(id=id)

    folder_id = photo.folder.id

    photo.delete()

    messages.success(
        request,
        "Photo deleted successfully."
    )

    return redirect(
        'folder_details',
        id=folder_id
    )

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .models import PhotoFolder, FolderPhoto, Album, AlbumPhoto


def create_album(request, folder_id):

    # --------------------------------------------------
    # Photographer access
    # --------------------------------------------------

    if request.session.get('user_role') != 'photographer':
        return redirect('login')

    user_id = request.session.get('user_id')

    # --------------------------------------------------
    # Get folder owned by logged-in photographer
    # --------------------------------------------------

    folder = get_object_or_404(
        PhotoFolder,
        id=folder_id,
        created_by_id=user_id
    )

    # --------------------------------------------------
    # Client liked photos
    # --------------------------------------------------

    liked_photos = list(
        FolderPhoto.objects.filter(
            folder=folder,
            photolike__isnull=False
        )
        .distinct()
        .order_by('id')
    )

    # --------------------------------------------------
    # Get AI analysis for liked photos
    # --------------------------------------------------

    analysis_by_photo = {
        analysis.photo_id: analysis
        for analysis in PhotoAnalysis.objects.filter(
            photo__in=liked_photos
        )
    }

    # Attach AI analysis to each liked photo
    for photo in liked_photos:
        photo.analysis_result = analysis_by_photo.get(photo.id)

    # --------------------------------------------------
    # AI recommended photos
    # --------------------------------------------------

    recommended_photos = [
        photo
        for photo in liked_photos
        if (
            photo.analysis_result
            and
            photo.analysis_result.recommendation == 'Recommended'
        )
    ]

    # ==================================================
    # POST - CREATE ALBUM
    # ==================================================

    if request.method == "POST":

        # --------------------------------------------------
        # Album details
        # --------------------------------------------------

        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()

        # --------------------------------------------------
        # Validate total pages
        # --------------------------------------------------

        try:
            total_pages = int(
                request.POST.get('total_pages', 0)
            )
        except (TypeError, ValueError):
            total_pages = 0

        if total_pages < 1:

            messages.error(
                request,
                "Please enter a valid number of pages."
            )

            return redirect(
                'create_album',
                folder_id=folder.id
            )

        # --------------------------------------------------
        # Get selected photo order
        # --------------------------------------------------

        ordered_raw = request.POST.get(
            'ordered_photo_ids',
            ''
        )

        selected_photos = [
            photo_id
            for photo_id in ordered_raw.split(',')
            if photo_id
        ]

        # --------------------------------------------------
        # Valid photo IDs
        #
        # Only liked photos can be selected
        # --------------------------------------------------

        valid_photo_ids = {
            str(photo.id)
            for photo in liked_photos
        }

        selected_photos = [
            photo_id
            for photo_id in selected_photos
            if photo_id in valid_photo_ids
        ]

        # --------------------------------------------------
        # At least one photo required
        # --------------------------------------------------

        if not selected_photos:

            messages.error(
                request,
                "Please select at least one photo."
            )

            return redirect(
                'create_album',
                folder_id=folder.id
            )

        # --------------------------------------------------
        # Page settings
        # --------------------------------------------------

        photos_per_page = {}

        total_selected = 0

        for i in range(1, total_pages + 1):

            try:
                count = int(
                    request.POST.get(
                        f'page_{i}',
                        1
                    )
                )
            except (TypeError, ValueError):
                count = 1

            if count < 1:
                count = 1

            photos_per_page[str(i)] = count

            total_selected += count

        # --------------------------------------------------
        # Make sure page layout matches selected photos
        # --------------------------------------------------

        if total_selected != len(selected_photos):

            messages.error(
                request,
                f"Page layout contains {total_selected} photo slots, "
                f"but {len(selected_photos)} photos are selected. "
                f"Please adjust the page settings."
            )

            return redirect(
                'create_album',
                folder_id=folder.id
            )

        # ==================================================
        # CREATE ALBUM
        # ==================================================

        album = Album.objects.create(
            title=title,
            description=description,
            folder=folder,
            created_by_id=user_id,
            total_pages=total_pages,
            photos_per_page=photos_per_page,
            photo_ids=",".join(selected_photos)
        )

        # ==================================================
        # CREATE ALBUM PHOTO RECORDS
        # ==================================================

        position = 1
        index = 0

        for page_no in range(
            1,
            total_pages + 1
        ):

            count = photos_per_page.get(
                str(page_no),
                1
            )

            page_photos = selected_photos[
                index:index + count
            ]

            for photo_id in page_photos:

                AlbumPhoto.objects.create(
                    album=album,
                    photo_id=photo_id,
                    page_number=page_no,
                    position=position,
                    rotation=0,
                    crop_x=0,
                    crop_y=0,
                    crop_width=0,
                    crop_height=0
                )

                position += 1

            index += count

        # --------------------------------------------------
        # Success
        # --------------------------------------------------

        messages.success(
            request,
            'Album Created Successfully'
        )

        return redirect(
            'album_designer',
            album.id
        )

    # ==================================================
    # GET - CREATE ALBUM PAGE
    # ==================================================

    return render(
        request,
        'photographer/create_album.html',
        {
            'folder': folder,
            'liked_photos': liked_photos,
            'recommended_photos': recommended_photos,
        }
    )

import math
from django.shortcuts import render, redirect
from .models import PhotoFolder, FolderPhoto
from django.conf import settings
from .utils import create_collage
import os


from django.shortcuts import render, redirect
from .models import Album, AlbumPage


def album_designer(request, id):

    if request.session.get('user_role') != 'photographer':
        return redirect('login')

    album = Album.objects.get(id=id)

    album_photos = AlbumPhoto.objects.filter(
        album=album
    ).select_related('photo').order_by('page_number', 'position')

    pages = {}
    for item in album_photos:
        pages.setdefault(item.page_number, []).append(item)

    pages = dict(sorted(pages.items()))  # ensure page_number order, not insertion order

    layout = get_page_layout(album)

    return render(
        request,
        'photographer/album_designer.html',
        {
            'album': album,
            'pages': pages,
            'layout': layout
        }
    )

from django.http import JsonResponse
import json

def save_crop(request):
    if request.method != "POST":
        return JsonResponse({'status': 'error'})

    data = json.loads(request.body)
    album_photo = AlbumPhoto.objects.get(id=data['id'])

    # Always edit the latest version: edited_image if it exists, else the original
    source_path = (
        album_photo.edited_image.path
        if album_photo.edited_image
        else album_photo.photo.image.path
    )

    img = Image.open(source_path)
    if img.mode != "RGB":
        img = img.convert("RGB")

    rotation = int(data.get('rotation', 0)) % 360
    if rotation:
        img = img.rotate(-rotation, expand=True)

    width = float(data['width'])
    height = float(data['height'])
    if width > 0 and height > 0:
        x, y = float(data['x']), float(data['y'])
        img = img.crop((x, y, x + width, y + height))

    # Overwrite this photo's edited file (one file per AlbumPhoto, not a pile-up)
    edited_name = f"album_photo_{album_photo.id}.jpg"
    edited_rel_path = os.path.join('album_edited', edited_name)
    edited_abs_path = os.path.join(settings.MEDIA_ROOT, edited_rel_path)
    os.makedirs(os.path.dirname(edited_abs_path), exist_ok=True)
    img.save(edited_abs_path, quality=95)

    album_photo.edited_image = edited_rel_path
    # Transform already baked into the file — reset so it's never reapplied
    album_photo.rotation = 0
    album_photo.crop_x = 0
    album_photo.crop_y = 0
    album_photo.crop_width = 0
    album_photo.crop_height = 0
    album_photo.save()

    return JsonResponse({
        'status': 'success',
        'image_url': album_photo.edited_image.url
    })

def rotate_photo(request):

    if request.method != "POST":
        return JsonResponse(
            {'status': 'error'}
        )

    data = json.loads(
        request.body
    )

    album_photo = AlbumPhoto.objects.get(
        id=data['id']
    )

    album_photo.rotation = int(
        data['rotation']
    )

    album_photo.save()

    return JsonResponse({
        'status': 'success'
    })

def update_photo_order(request):
    if request.method != "POST":
        return JsonResponse({'status': 'error'})

    data = json.loads(request.body)

    for item in data:
        AlbumPhoto.objects.filter(id=item['id']).update(
            page_number=int(item['page']),
            position=int(item['position'])
        )

    return JsonResponse({'status': 'success'})


from PIL import Image
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
import os
import uuid

from PIL import Image
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
import os
import uuid


def _build_album_collages(album, output_subfolder):
    layout = get_page_layout(album)  # {1: 1, 2: 2, 3: 3, 4: 4, 5: 3, 6: 2, 7: 1}

    temp_folder = os.path.join(settings.MEDIA_ROOT, 'temp_album')
    os.makedirs(temp_folder, exist_ok=True)

    output_folder = os.path.join(settings.MEDIA_ROOT, output_subfolder)
    os.makedirs(output_folder, exist_ok=True)

    results = []

    for page_no, expected_count in layout.items():

        photos = AlbumPhoto.objects.filter(
            album=album,
            page_number=page_no
        ).order_by('position')

        photo_paths = []

        for item in photos:
            source_path = (
                item.edited_image.path if item.edited_image else item.photo.image.path
            )

            img = Image.open(source_path)
            if img.mode != "RGB":
                img = img.convert("RGB")

            temp_name = f"{uuid.uuid4()}.jpg"
            temp_path = os.path.join(temp_folder, temp_name)
            img.save(temp_path, quality=95)
            photo_paths.append(temp_path)

        filename = f'album_{album.id}_page_{page_no}.jpg'
        output_path = os.path.join(output_folder, filename)

        create_collage(photo_paths, output_path)

        results.append({
            'page_number': page_no,
            'url': settings.MEDIA_URL + output_subfolder + '/' + filename
        })

    return results

def preview_album(request, id):
    """
    Builds the collages fresh from current edits but does NOT save
    AlbumPage records — purely a 'what would this look like' view.
    """
    if request.session.get('user_role') != 'photographer':
        return redirect('login')

    album = Album.objects.get(id=id)

    pages = _build_album_collages(album, 'album_preview')

    return render(
        request,
        'photographer/preview_album.html',
        {
            'album': album,
            'pages': pages
        }
    )


def generate_album(request, id):

    if request.session.get('user_role') != 'photographer':
        return redirect('login')

    album = Album.objects.get(id=id)

    AlbumPage.objects.filter(album=album).delete()

    pages = _build_album_collages(album, 'album_pages')

    for page in pages:
        AlbumPage.objects.create(
            album=album,
            page_number=page['page_number'],
            collage=f"album_pages/album_{album.id}_page_{page['page_number']}.jpg"
        )

    messages.success(request, 'Album Generated Successfully')

    return redirect('view_album', id=album.id)


def view_album(request, id):

    album = Album.objects.get(id=id)

    pages = AlbumPage.objects.filter(album=album).order_by('page_number')

    return render(
        request,
        'photographer/view_album.html',
        {
            'album': album,
            'pages': pages
        }
    )


def delete_album(request, id):

    if request.session.get('user_role') != 'photographer':
        return redirect('login')

    album = Album.objects.get(id=id)

    AlbumPage.objects.filter(
        album=album
    ).delete()

    AlbumPhoto.objects.filter(
        album=album
    ).delete()

    album.delete()

    messages.success(
        request,
        'Album Deleted Successfully'
    )

    return redirect(
        'my_albums'
    )


def get_page_layout(album):
    """
    Returns the album's current page layout as {page_number: photo_count},
    built live from AlbumPhoto rows — never from the stale photos_per_page
    snapshot. This guarantees pages with the same photo count (e.g. two
    pages with 3 photos) stay fully independent, since the key is always
    the page_number, never the count.
    """
    layout = {}

    rows = AlbumPhoto.objects.filter(album=album).values('page_number')

    for row in rows:
        page_no = row['page_number']
        layout[page_no] = layout.get(page_no, 0) + 1

    # returns dict ordered by page_number, e.g. {1: 1, 2: 2, 3: 3, 4: 4, 5: 3, 6: 2, 7: 1}
    return dict(sorted(layout.items()))






def my_albums(request):

    if request.session.get('user_role') != 'photographer':
        return redirect('login')

    albums = Album.objects.filter(
        created_by_id=request.session['user_id']
    ).order_by(
        '-created_at'
    )

    return render(
        request,
        'photographer/my_albums.html',
        {
            'albums': albums
        }
    )

from io import BytesIO
from django.http import HttpResponse
def download_album_pdf(request, id, orientation):

    if request.session.get('user_role') != 'photographer':
        return redirect('login')

    album = Album.objects.get(id=id)

    pages = AlbumPage.objects.filter(album=album).order_by('page_number')

    if not pages:
        messages.warning(request, 'Generate the album before downloading.')
        return redirect('view_album', id=album.id)

    # Target PDF page size — A4-ish ratio at high res, swapped per orientation
    if orientation == 'portrait':
        target_w, target_h = 1500, 2100
    else:
        target_w, target_h = 2100, 1500

    images = []

    for page in pages:

        img = Image.open(page.collage.path)

        if img.mode != "RGB":
            img = img.convert("RGB")

        w, h = img.size

        # Fit the existing collage INSIDE the target page without rotating
        # or cropping it — letterbox with white bars instead.
        scale = min(target_w / w, target_h / h)
        new_w, new_h = int(w * scale), int(h * scale)

        resized = img.resize((new_w, new_h), Image.LANCZOS)

        canvas = Image.new("RGB", (target_w, target_h), "white")
        paste_x = (target_w - new_w) // 2
        paste_y = (target_h - new_h) // 2
        canvas.paste(resized, (paste_x, paste_y))

        images.append(canvas)

    buffer = BytesIO()

    images[0].save(
        buffer,
        format='PDF',
        save_all=True,
        append_images=images[1:],
        quality=95
    )

    buffer.seek(0)

    filename = f"{album.title.replace(' ', '_')}_{orientation}.pdf"

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response


def album_share(request, token):

    album = Album.objects.get(
        share_token=token
    )

    pages = AlbumPage.objects.filter(
        album=album
    ).order_by(
        'page_number'
    )

    return render(
        request,
        'client/album_share.html',
        {
            'album': album,
            'pages': pages
        }
    )










#Client Views



def access_folder(request):

    if request.method == "POST":

        password = request.POST.get('password')

        try:

            folder = PhotoFolder.objects.get(
                password=password
            )

            request.session[
                f'folder_{folder.id}'
            ] = True

            request.session[
                'current_folder_id'
            ] = folder.id

            return redirect(
                'folder_gallery',
                id=folder.id
            )

        except PhotoFolder.DoesNotExist:

            messages.error(
                request,
                "Invalid folder password."
            )

            return redirect(
                'client_dashboard'
            )

    return redirect(
        'client_dashboard'
    )
def folder_gallery(request, id):

    if not request.session.get(f'folder_{id}'):

        messages.error(
            request,
            "Please enter folder password."
        )

        return redirect('user_folders')

    folder = PhotoFolder.objects.get(id=id)

    photos = FolderPhoto.objects.filter(
        folder=folder
    )

    user_id = request.session.get('user_id')

    liked_photos = PhotoLike.objects.filter(
        user_id=user_id,
        photo__folder=folder
    ).values_list(
        'photo_id',
        flat=True
    )

    for photo in photos:
        photo.is_liked = photo.id in liked_photos

    return render(
        request,
        'client/folder_gallery.html',
        {
            'folder': folder,
            'photos': photos
        }
    )


from django.http import JsonResponse
def toggle_like(request, photo_id):

    user_id = request.session.get('user_id')

    photo = FolderPhoto.objects.get(id=photo_id)

    liked = PhotoLike.objects.filter(
        photo=photo,
        user_id=user_id
    ).first()

    if liked:

        liked.delete()

        return JsonResponse({
            'status': 'unliked'
        })

    PhotoLike.objects.create(
        photo=photo,
        user_id=user_id
    )

    return JsonResponse({
        'status': 'liked'
    })

def client_albums(request, folder_id):

    if not request.session.get(
        f'folder_{folder_id}'
    ):

        messages.error(
            request,
            "Please enter folder password."
        )

        return redirect(
            'client_dashboard'
        )

    folder = PhotoFolder.objects.get(
        id=folder_id
    )

    albums = Album.objects.filter(
        folder=folder
    ).order_by(
        '-created_at'
    )

    return render(
        request,
        'client/client_albums.html',
        {
            'folder': folder,
            'albums': albums
        }
    )
def client_view_album(request, id):

    album = Album.objects.get(id=id)

    if not request.session.get(
        f'folder_{album.folder.id}'
    ):

        messages.error(
            request,
            "Please enter folder password."
        )

        return redirect('client_dashboard')

    pages = AlbumPage.objects.filter(
        album=album
    ).order_by('page_number')

    return render(
        request,
        'client/client_view_album.html',
        {
            'album': album,
            'pages': pages
        }
    )
from io import BytesIO
from PIL import Image
from django.http import HttpResponse
from django.contrib import messages

def client_download_album_pdf(
    request,
    id,
    orientation
):

    album = Album.objects.get(
        id=id
    )

    if not request.session.get(
        f'folder_{album.folder.id}'
    ):

        messages.error(
            request,
            "Please enter folder password."
        )

        return redirect(
            'client_dashboard'
        )

    pages = AlbumPage.objects.filter(
        album=album
    ).order_by(
        'page_number'
    )

    if not pages.exists():

        messages.warning(
            request,
            'Album pages not found.'
        )

        return redirect(
            'client_view_album',
            id=album.id
        )

    if orientation == 'portrait':

        target_w = 1500
        target_h = 2100

    else:

        target_w = 2100
        target_h = 1500

    images = []

    for page in pages:

        img = Image.open(
            page.collage.path
        )

        if img.mode != "RGB":

            img = img.convert(
                "RGB"
            )

        w, h = img.size

        scale = min(
            target_w / w,
            target_h / h
        )

        new_w = int(w * scale)
        new_h = int(h * scale)

        resized = img.resize(
            (new_w, new_h),
            Image.LANCZOS
        )

        canvas = Image.new(
            "RGB",
            (target_w, target_h),
            "white"
        )

        paste_x = (
            target_w - new_w
        ) // 2

        paste_y = (
            target_h - new_h
        ) // 2

        canvas.paste(
            resized,
            (paste_x, paste_y)
        )

        images.append(
            canvas
        )

    buffer = BytesIO()

    images[0].save(
        buffer,
        format='PDF',
        save_all=True,
        append_images=images[1:]
    )

    buffer.seek(0)

    filename = (
        f"{album.title}_{orientation}.pdf"
    )

    response = HttpResponse(
        buffer,
        content_type='application/pdf'
    )

    response[
        'Content-Disposition'
    ] = (
        f'attachment; filename="{filename}"'
    )

    return response

def favorite_photos(request):

    folder_id = request.session.get(
        'current_folder_id'
    )

    if not folder_id:

        messages.error(
            request,
            "Please enter folder password."
        )

        return redirect(
            'client_dashboard'
        )

    if not request.session.get(
        f'folder_{folder_id}'
    ):

        messages.error(
            request,
            "Please enter folder password."
        )

        return redirect(
            'client_dashboard'
        )

    user_id = request.session.get(
        'user_id'
    )

    likes = PhotoLike.objects.filter(
        user_id=user_id,
        photo__folder_id=folder_id
    ).select_related(
        'photo'
    )

    return render(
        request,
        'client/favorite_photos.html',
        {
            'likes': likes
        }
    )

def client_profile(request):

    if request.session.get('user_role') != 'client':
        return redirect('login')

    user = UserRegister.objects.get(
        id=request.session['user_id']
    )

    if request.method == "POST":

        user.full_name = request.POST.get(
            'full_name'
        )

        user.email = request.POST.get(
            'email'
        )

        user.phone = request.POST.get(
            'phone'
        )

        user.address = request.POST.get(
            'address'
        )

        user.place = request.POST.get(
            'place'
        )

        if request.FILES.get(
            'profile_pic'
        ):

            user.profile_pic = request.FILES.get(
                'profile_pic'
            )

        user.save()

        messages.success(
            request,
            'Profile Updated Successfully'
        )

        return redirect(
            'client_profile'
        )

    return render(
        request,
        'client/client_profile.html',
        {
            'user': user
        }
    )


#Freelance Views
def freelance_profile(request):

    if request.session.get('user_role') != 'freelance':
        return redirect('login')

    user = UserRegister.objects.get(
        id=request.session.get('user_id')
    )

    return render(
        request,
        'freelance/freelance_profile.html',
        {
            'user': user
        }
    )

def update_freelance_profile(request):

    if request.session.get('user_role') != 'freelance':
        return redirect('login')

    user = UserRegister.objects.get(
        id=request.session.get('user_id')
    )

    if request.method == "POST":

        user.full_name = request.POST.get(
            'full_name'
        )

        user.email = request.POST.get(
            'email'
        )

        user.phone = request.POST.get(
            'phone'
        )

        user.place = request.POST.get(
            'place'
        )

        user.address = request.POST.get(
            'address'
        )

        if request.FILES.get('profile_pic'):

            user.profile_pic = request.FILES.get(
                'profile_pic'
            )

        user.save()

        messages.success(
            request,
            'Profile updated successfully.'
        )

        return redirect(
            'freelance_profile'
        )

    return render(
        request,
        'freelance/update_freelance_profile.html',
        {
            'user': user
        }
    )


def freelance_create_folder(request):

    if request.session.get('user_role') != 'freelance':
        return redirect('login')

    if request.method == "POST":

        folder_id = request.POST.get('folder_id').strip()
        password = request.POST.get('password').strip()

        if FreelancerPhotoFolder.objects.filter(password=password).exists():
            messages.error(request, "Folder password already exists. Please use another password.")
            return redirect('freelance_create_folder')

        FreelancerPhotoFolder.objects.create(
            folder_id=folder_id,
            password=password,
            created_by_id=request.session['user_id']
        )

        messages.success(request, "Folder created successfully.")
        return redirect('freelance_view_folders')

    return render(request, 'freelance/freelance_create_folder.html')

def freelance_view_folders(request):

    if request.session.get('user_role') != 'freelance':
        return redirect('login')

    folders = FreelancerPhotoFolder.objects.filter(
        created_by_id=request.session['user_id']
    ).order_by('-id')

    return render(
        request,
        'freelance/freelance_view_folders.html',
        {'folders': folders}
    )

def freelance_edit_folder(request, id):

    if request.session.get('user_role') != 'freelance':
        return redirect('login')

    folder = FreelancerPhotoFolder.objects.get(id=id)

    if request.method == "POST":

        folder_id = request.POST.get('folder_id').strip()
        password = request.POST.get('password').strip()

        if FreelancerPhotoFolder.objects.filter(password=password).exclude(id=id).exists():
            messages.error(request, "Folder password already exists. Please use another password.")
            return redirect('freelance_edit_folder', id=id)

        folder.folder_id = folder_id
        folder.password = password
        folder.save()

        messages.success(request, "Folder updated successfully.")
        return redirect('freelance_view_folders')

    return render(
        request,
        'freelance/freelance_edit_folder.html',
        {'folder': folder}
    )

def freelance_delete_folder(request, id):

    if request.session.get('user_role') != 'freelance':
        return redirect('login')

    folder = FreelancerPhotoFolder.objects.get(id=id)

    if request.method == "POST":

        password = request.POST.get('password')

        if password == folder.password:

            folder.delete()

            messages.success(
                request,
                "Folder deleted successfully."
            )

        else:

            messages.error(
                request,
                "Incorrect folder password."
            )

        return redirect('freelance_view_folders')

    return redirect('freelance_view_folders')


def freelance_folder_details(request, id):

    if request.session.get('user_role') != 'freelance':
        return redirect('login')

    folder = FreelancerPhotoFolder.objects.get(id=id)

    photos = FreelancerFolderPhoto.objects.filter(
        folder=folder
    ).order_by('id')

    return render(
        request,
        'freelance/freelance_folder_details.html',
        {
            'folder': folder,
            'photos': photos,
        }
    )

def freelance_upload_photos(request, id):

    if request.session.get('user_role') != 'freelance':
        return redirect('login')

    folder = FreelancerPhotoFolder.objects.get(id=id)

    if request.method == "POST":

        photos = request.FILES.getlist('photos')

        for photo in photos:

            FreelancerFolderPhoto.objects.create(
                folder=folder,
                image=photo
            )

        messages.success(
            request,
            "Photos uploaded successfully."
        )

        return redirect(
            'freelance_folder_details',
            id=folder.id
        )

    return render(
        request,
        'freelance/freelance_upload_photos.html',
        {'folder': folder}
    )


def freelance_delete_photo(request, id):

    if request.session.get('user_role') != 'freelance':
        return redirect('login')

    photo = FreelancerFolderPhoto.objects.get(id=id)

    folder_id = photo.folder.id

    photo.delete()

    messages.success(
        request,
        "Photo deleted successfully."
    )

    return redirect(
        'freelance_folder_details',
        id=folder_id
    )

import json

def freelance_create_album(request, folder_id):

    if request.session.get('user_role') != 'freelance':
        return redirect('login')

    folder = FreelancerPhotoFolder.objects.get(id=folder_id)

    photos = FreelancerFolderPhoto.objects.filter(
        folder=folder
    )

    if request.method == "POST":

        title = request.POST.get('title')
        description = request.POST.get('description')
        total_pages = int(request.POST.get('total_pages'))

        ordered_raw = request.POST.get(
            'ordered_photo_ids',
            ''
        )

        selected_photos = [
            pid for pid in ordered_raw.split(',')
            if pid
        ]

        photos_per_page = {}

        for i in range(1, total_pages + 1):

            photos_per_page[str(i)] = int(
                request.POST.get(
                    f'page_{i}',
                    1
                )
            )

        album = FreelancerAlbum.objects.create(
            title=title,
            description=description,
            folder=folder,
            created_by_id=request.session['user_id'],
            total_pages=total_pages,
            photos_per_page=photos_per_page,
            photo_ids=",".join(selected_photos)
        )

        position = 1
        index = 0

        for page_no in range(1, total_pages + 1):

            count = int(
                photos_per_page.get(
                    str(page_no),
                    1
                )
            )

            page_photos = selected_photos[
                index:index + count
            ]

            for photo_id in page_photos:

                FreelancerAlbumPhoto.objects.create(
                    album=album,
                    photo_id=photo_id,
                    page_number=page_no,
                    position=position,
                    rotation=0,
                    crop_x=0,
                    crop_y=0,
                    crop_width=0,
                    crop_height=0
                )

                position += 1

            index += count

        messages.success(
            request,
            "Album Created Successfully"
        )

        return redirect(
            'freelance_album_designer',
            album.id
        )

    return render(
        request,
        'freelance/create_album.html',
        {
            'folder': folder,
            'photos': photos
        }
    )


from .models import (
    FreelancerAlbum,
    FreelancerAlbumPhoto
)

def freelance_album_designer(request, id):

    if request.session.get('user_role') != 'freelance':
        return redirect('login')

    album = FreelancerAlbum.objects.get(id=id)

    album_photos = FreelancerAlbumPhoto.objects.filter(
        album=album
    ).select_related(
        'photo'
    ).order_by(
        'page_number',
        'position'
    )

    pages = {}

    for item in album_photos:
        pages.setdefault(
            item.page_number,
            []
        ).append(item)

    pages = dict(
        sorted(pages.items())
    )

    layout = freelance_get_page_layout(album)

    return render(
        request,
        'freelance/album_designer.html',
        {
            'album': album,
            'pages': pages,
            'layout': layout
        }
    )


def freelance_save_crop(request):
    if request.method != "POST":
        return JsonResponse({'status': 'error'})

    data = json.loads(request.body)
    album_photo = FreelancerAlbumPhoto.objects.get(id=data['id'])

    # Always edit the latest version: edited_image if it exists, else the original
    source_path = (
        album_photo.edited_image.path
        if album_photo.edited_image
        else album_photo.photo.image.path
    )

    img = Image.open(source_path)
    if img.mode != "RGB":
        img = img.convert("RGB")

    rotation = int(data.get('rotation', 0)) % 360
    if rotation:
        img = img.rotate(-rotation, expand=True)

    width = float(data['width'])
    height = float(data['height'])
    if width > 0 and height > 0:
        x, y = float(data['x']), float(data['y'])
        img = img.crop((x, y, x + width, y + height))

    # Overwrite this photo's edited file (one file per AlbumPhoto, not a pile-up)
    edited_name = f"album_photo_{album_photo.id}.jpg"
    edited_rel_path = os.path.join('freelance_edited', edited_name)
    edited_abs_path = os.path.join(settings.MEDIA_ROOT, edited_rel_path)
    os.makedirs(os.path.dirname(edited_abs_path), exist_ok=True)
    img.save(edited_abs_path, quality=95)

    album_photo.edited_image = edited_rel_path
    # Transform already baked into the file — reset so it's never reapplied
    album_photo.rotation = 0
    album_photo.crop_x = 0
    album_photo.crop_y = 0
    album_photo.crop_width = 0
    album_photo.crop_height = 0
    album_photo.save()

    return JsonResponse({
        'status': 'success',
        'image_url': album_photo.edited_image.url
    })

def freelance_rotate_photo(request):

    if request.method != "POST":
        return JsonResponse(
            {'status': 'error'}
        )

    data = json.loads(
        request.body
    )

    album_photo = FreelancerAlbumPhoto.objects.get(
        id=data['id']
    )

    album_photo.rotation = int(
        data['rotation']
    )

    album_photo.save()

    return JsonResponse({
        'status': 'success'
    })

def freelance_update_photo_order(request):
    if request.method != "POST":
        return JsonResponse({'status': 'error'})

    data = json.loads(request.body)

    for item in data:
        FreelancerAlbumPhoto.objects.filter(id=item['id']).update(
            page_number=int(item['page']),
            position=int(item['position'])
        )

    return JsonResponse({'status': 'success'})


def _build_freelance_album_collages(album, output_subfolder):

    layout = freelance_get_page_layout(album)

    temp_folder = os.path.join(settings.MEDIA_ROOT, 'freelance_temp_album')
    os.makedirs(temp_folder, exist_ok=True)

    output_folder = os.path.join(settings.MEDIA_ROOT, output_subfolder)
    os.makedirs(output_folder, exist_ok=True)

    results = []

    for page_no in layout.keys():

        photos = FreelancerAlbumPhoto.objects.filter(
            album=album,
            page_number=page_no
        ).order_by('position')

        photo_paths = []

        for item in photos:

            source_path = (
                item.edited_image.path
                if item.edited_image
                else item.photo.image.path
            )

            img = Image.open(source_path)

            if img.mode != "RGB":
                img = img.convert("RGB")

            temp_name = f"{uuid.uuid4()}.jpg"
            temp_path = os.path.join(temp_folder, temp_name)

            img.save(temp_path, quality=95)

            photo_paths.append(temp_path)

        filename = f'album_{album.id}_page_{page_no}.jpg'

        output_path = os.path.join(
            output_folder,
            filename
        )

        create_collage(
            photo_paths,
            output_path
        )

        # Remove temporary images
        for path in photo_paths:
            if os.path.exists(path):
                os.remove(path)

        results.append({
            'page_number': page_no,
            'url': settings.MEDIA_URL + output_subfolder + '/' + filename
        })

    return results


def freelance_preview_album(request, id):
    """
    Builds the collages fresh from current edits but does NOT save
    FreelancerAlbumPage records — purely a preview.
    """

    if request.session.get('user_role') != 'freelance':
        return redirect('login')

    album = FreelancerAlbum.objects.get(id=id)

    pages = _build_freelance_album_collages(
        album,
        'freelance_album_preview'
    )

    return render(
        request,
        'freelance/preview_album.html',
        {
            'album': album,
            'pages': pages
        }
    )

def freelance_generate_album(request, id):

    if request.session.get('user_role') != 'freelance':
        return redirect('login')

    album = FreelancerAlbum.objects.get(id=id)

    # Remove previously generated pages
    FreelancerAlbumPage.objects.filter(
        album=album
    ).delete()

    # Generate collages
    pages = _build_freelance_album_collages(
        album,
        'freelance_album_pages'
    )

    # Save generated pages
    for page in pages:

        FreelancerAlbumPage.objects.create(
            album=album,
            page_number=page['page_number'],
            collage=(
                f"freelance_album_pages/"
                f"album_{album.id}_page_{page['page_number']}.jpg"
            )
        )

    messages.success(
        request,
        "Album Generated Successfully."
    )

    return redirect(
        'freelance_view_album',
        id=album.id
    )

def freelance_view_album(request, id):

    if request.session.get('user_role') != 'freelance':
        return redirect('login')

    album = FreelancerAlbum.objects.get(
        id=id,
        created_by_id=request.session['user_id']
    )

    pages = FreelancerAlbumPage.objects.filter(
        album=album
    ).order_by(
        'page_number'
    )

    return render(
        request,
        'freelance/view_album.html',
        {
            'album': album,
            'pages': pages
        }
    )


def freelance_my_albums(request):

    if request.session.get('user_role') != 'freelance':
        return redirect('login')

    albums = FreelancerAlbum.objects.filter(
        created_by_id=request.session['user_id']
    ).order_by(
        '-created_at'
    )

    return render(
        request,
        'freelance/my_albums.html',
        {
            'albums': albums
        }
    )


from io import BytesIO
from django.http import HttpResponse
from PIL import Image

def freelance_download_album_pdf(
    request,
    id,
    orientation
):

    if request.session.get('user_role') != 'freelance':
        return redirect('login')

    album = FreelancerAlbum.objects.get(
        id=id
    )

    pages = FreelancerAlbumPage.objects.filter(
        album=album
    ).order_by(
        'page_number'
    )

    if not pages.exists():

        messages.warning(
            request,
            'Generate the album before downloading.'
        )

        return redirect(
            'freelance_view_album',
            id=album.id
        )

    if orientation == 'portrait':

        target_w = 1500
        target_h = 2100

    else:

        target_w = 2100
        target_h = 1500

    images = []

    for page in pages:

        img = Image.open(
            page.collage.path
        )

        if img.mode != "RGB":

            img = img.convert(
                "RGB"
            )

        w, h = img.size

        scale = min(
            target_w / w,
            target_h / h
        )

        new_w = int(w * scale)
        new_h = int(h * scale)

        resized = img.resize(
            (new_w, new_h),
            Image.LANCZOS
        )

        canvas = Image.new(
            "RGB",
            (target_w, target_h),
            "white"
        )

        paste_x = (target_w - new_w) // 2
        paste_y = (target_h - new_h) // 2

        canvas.paste(
            resized,
            (paste_x, paste_y)
        )

        images.append(
            canvas
        )

    buffer = BytesIO()

    images[0].save(
        buffer,
        format='PDF',
        save_all=True,
        append_images=images[1:],
        quality=95
    )

    buffer.seek(0)

    filename = (
        f"{album.title.replace(' ','_')}_{orientation}.pdf"
    )

    response = HttpResponse(
        buffer,
        content_type='application/pdf'
    )

    response['Content-Disposition'] = (
        f'attachment; filename="{filename}"'
    )

    return response


def freelance_album_share(request, token):

    album = FreelancerAlbum.objects.get(
        share_token=token
    )

    pages = FreelancerAlbumPage.objects.filter(
        album=album
    ).order_by(
        'page_number'
    )

    return render(
        request,
        'freelance/album_share.html',
        {
            'album': album,
            'pages': pages
        }
    )


def freelance_delete_album(request, id):

    if request.session.get('user_role') != 'freelance':
        return redirect('login')

    album = FreelancerAlbum.objects.get(id=id)

    FreelancerAlbumPage.objects.filter(
        album=album
    ).delete()

    FreelancerAlbumPhoto.objects.filter(
        album=album
    ).delete()

    album.delete()

    messages.success(
        request,
        'Album Deleted Successfully'
    )

    return redirect(
        'freelance_my_albums'
    )


def freelance_get_page_layout(album):
    """
    Returns the album's current page layout as {page_number: photo_count},
    built live from FreelancerAlbumPhoto rows — never from the stale photos_per_page
    snapshot. This guarantees pages with the same photo count (e.g. two
    pages with 3 photos) stay fully independent, since the key is always
    the page_number, never the count.
    """
    layout = {}

    rows = FreelancerAlbumPhoto.objects.filter(album=album).values('page_number')

    for row in rows:
        page_no = row['page_number']
        layout[page_no] = layout.get(page_no, 0) + 1

    # returns dict ordered by page_number, e.g. {1: 1, 2: 2, 3: 3, 4: 4, 5: 3, 6: 2, 7: 1}
    return dict(sorted(layout.items()))