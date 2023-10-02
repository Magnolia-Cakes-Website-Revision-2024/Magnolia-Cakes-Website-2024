from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login as django_login
from django.contrib.auth.forms import AuthenticationForm

# import view sets from the REST framework
from rest_framework import viewsets

# import the TodoSerializer from the serializer file
from .serializers import *

# import the Todo model from the models file
from .models import *

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from .forms import ContactForm, FavourServingsForm, NewUserForm

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication

# Email AUTH
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage, send_mail, BadHeaderError
from .tokens import account_activation_token
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.conf import settings


# create a class for the Todo model viewsets
class MagnoliaCakesAndCupcakesView(viewsets.ModelViewSet):
    # create a serializer class and
    # assign it to the TodoSerializer class
    serializer_class = MagnoliaCakesAndCupcakesSerializer

    # define a variable and populate it
    # with the Todo list objects
    queryset = MagnoliaCakesAndCupcakes.objects.all()


@api_view(["POST"])
@permission_classes(
    [AllowAny]
)  ###### Add this to allow users to access despite not being logged in
def register(request):
    if request.method == "POST":
        form = NewUserForm(request.data)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.is_active = False
            user.save()
            return activateEmail(request, user, form.cleaned_data.get("username"))
        return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)


@permission_classes(
    [AllowAny]
)  ###### Add this to allow users to access despite not being logged in
def activateEmail(request, user, to_email):

    mail_subject = "Activate your user account."

    context = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "domain": get_current_site(request).domain,
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": account_activation_token.make_token(user),
            "protocol": "https" if request.is_secure() else "http",
    }

    message = render_to_string("template_activate_account.html", context)

    email = EmailMessage(mail_subject, message, to=[to_email])
    try:
        if email.send():
            return Response(
                {
                    "message": "User registered successfully. Please complete verification by clicking the link sent to your email."
                },
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {
                    "message": "Problem sending confirmation email. Please contact an administrator."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
    except Exception as error:
        print(error)
        return Response(
            {
                "message": "Problem sending confirmation email. Please contact an administrator."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

from django.shortcuts import redirect

@permission_classes(
    [AllowAny]
)  ###### Add this to allow users to access despite not being logged in
def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        return redirect(f"{settings.FRONTEND_APP_URL}/login/?success=true")

    return redirect(f"{settings.FRONTEND_APP_URL}/login/?success=false")


@api_view(["POST"])
@permission_classes(
    [AllowAny]
)  ###### Add this to allow users to access despite not being logged in
def login(request):
    if request.method == "POST":
        form = AuthenticationForm(request._request, data=request.data)
        print("form ", form.error_messages)

        if form.is_valid():
            username = request.data.get("username").lower()
            password = request.data.get("password")

            user = authenticate(request._request, username=username, password=password)
            if user is not None:
                django_login(
                    request._request, user
                )  # Use django_login instead of login
                return Response(
                    {"message": "Login successful"}, status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {
                        "message": "Login failed",
                        "error_messages": "user does not exist",
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )
        else:
            return Response(
                {"message": "Login failed", "error_messages": form.error_messages},
                status=status.HTTP_400_BAD_REQUEST,
            )


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT"])
@permission_classes(
    [AllowAny]
)  ###### Add this to allow users to access despite not being logged in
def terms_and_conditions(request):
    if request.method == "GET":
        terms = TermsAndCondition.objects.all()
        serializer = TermsAndConditionsSerializer(terms, many=True)
        return Response(serializer.data)

    elif request.method == "PUT":
        terms = TermsAndCondition.objects.first()
        serializer = TermsAndConditionsSerializer(terms, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Terms & Conditions updated"}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "POST"])
@permission_classes(
    [AllowAny]
)  ###### Add this to allow users to access despite not being logged in
def contact(request):
    if request.method == "GET":
        form = ContactForm()
    else:
        form = ContactForm(request.POST, request.FILES)
        if form.is_valid():
            user_email = form.cleaned_data["email"]
            subject = form.cleaned_data["subject"]
            message = form.cleaned_data["message"]
            file = request.FILES.getlist("file")

            admin_email = ContactUsEmail.objects.first()

            email = EmailMessage(
                subject, message, to=[admin_email.your_email], cc=[user_email]
            )

            for f in file:
                email.attach(f.name, f.read(), f.content_type)

            try:
                email.send()
            except Exception as error:
                return Response(
                    {
                        "message": "Problem sending email. Please contact an administrator."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(
                "Success! Request for quote submitted.", status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"message": "Contact failed"},
                status=status.HTTP_400_BAD_REQUEST,
            )
    return render(request, "email.html", {"form": form})


@api_view(["GET"])
@permission_classes(
    [AllowAny]
)  ###### Add this to allow users to access despite not being logged in
def cakes_list(request):
    if request.method == "GET":
        cakes = Cake.objects.all()
        serializer = CakeSerializer(cakes, many=True)

        # Create a list to store the updated cake data with image URLs
        cakes_with_image_urls = []

        for cake_data in serializer.data:
            cake = Cake.objects.get(id=cake_data["id"])
            # Add the image URL to the cake data
            cake_data["image"] = cake.picture.url
            cakes_with_image_urls.append(cake_data)

        return Response(cakes_with_image_urls, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes(
    [AllowAny]
)  ###### Add this to allow users to access despite not being logged in
def slider_images(request):
    if request.method == "GET":
        images = SliderImage.objects.all()
        serializer = SliderImageSerializer(images, many=True)

        # Create a list to store the updated cake data with image URLs
        images_with_urls = []

        for image_data in serializer.data:
            imageObject = SliderImage.objects.get(id=image_data["id"])
            # Add the image URL to the cake data
            image_data["image"] = imageObject.image.url
            images_with_urls.append(image_data)

        return Response(images_with_urls, status=status.HTTP_200_OK)


@api_view(["GET", "PUT"])
@permission_classes(
    [AllowAny]
)  ###### Add this to allow users to access despite not being logged in
def flavours_and_servings(request):
    if request.method == "GET":
        flavours_servings_lists = FlavoursAndServings.objects.all()
        serializer = FlavoursAndServingsSerializer(flavours_servings_lists, many=True)
        return Response(serializer.data)

    if request.method == "POST":
        form = FavourServingsForm(request.data)
        if form.is_valid():
            flavours_servings_list = form.save(commit=False)
            flavours_servings_list.title = flavours_servings_list.title
            flavours_servings_list.list = flavours_servings_list.list
            flavours_servings_list.save()
            return Response(
                {"message": "Flavours & Servings updated"}, status=status.HTTP_200_OK
            )
        return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT"])
@permission_classes(
    [AllowAny]
)  ###### Add this to allow users to access despite not being logged in
def about_us(request):
    if request.method == "GET":
        about_us = AboutUs.objects.first()
        serializer = AboutUsSerializer(about_us)
        return Response(serializer.data)

    elif request.method == "PUT":
        about_us = AboutUs.objects.first()
        serializer = AboutUsSerializer(about_us, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "About Us updated"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT"])
@permission_classes(
    [AllowAny]
)  ###### Add this to allow users to access despite not being logged in
def faq_categories_list(request):
    if request.method == "GET":
        categories = FAQCategory.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

@api_view(["GET"])
@permission_classes(
    [AllowAny]
)  ###### Add this to allow users to access despite not being logged in
def faq_questions_list(request):
    if request.method == "GET":
        questions = Question.objects.all()
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data)


@api_view(["GET"])
@permission_classes(
    [AllowAny]
)  ###### Add this to allow users to access despite not being logged in
def footer_location(request):
    if request.method == "GET":
        footer_location = FooterLocation.objects.first()
        serializer = FooterLocationSerializer(footer_location)
        return Response(serializer.data)


@api_view(["GET"])
@permission_classes(
    [AllowAny]
)  ###### Add this to allow users to access despite not being logged in
def footer_contact_us(request):
    if request.method == "GET":
        footer_contact = FooterContactUs.objects.first()
        serializer = FooterContactUsSerializer(footer_contact)
        return Response(serializer.data)


@api_view(["GET"])
@permission_classes(
    [AllowAny]
)  ###### Add this to allow users to access despite not being logged in
def footer_business_hrs(request):
    if request.method == "GET":
        footer_bushrs = FooterBusinessHours.objects.first()
        serializer = FooterBusinessHoursSerializer(footer_bushrs)
        return Response(serializer.data)


@api_view(["GET"])
@permission_classes(
    [AllowAny]
)  ###### Add this to allow users to access despite not being logged in
def social_medias(request):
    if request.method == "GET":
        social_media_accounts = SocialMedias.objects.all()
        serializer = SocialMediasSerializer(social_media_accounts, many=True)
        return Response(serializer.data)


@api_view(["GET"])
@permission_classes(
    [AllowAny]
)  ###### Add this to allow users to access despite not being logged in
def flavours_and_servings_info(request):
    if request.method == "GET":
        flavours_servings_info = FlavoursAndServingsInfo.objects.first()
        serializer = FlavoursAndServingsInfoSerializer(flavours_servings_info)
        return Response(serializer.data)


@api_view(["GET"])
def get_user(request):
    if request.method == "GET":
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)


@api_view(["POST"])
def reset_names(request):
    if request.method == 'POST':
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        
        if not (first_name and last_name):
            return Response({'error': 'Both first_name and last_name are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Assuming you have an authenticated user, you can access it using request.user
        user = request.user
        
        try:
            # Update the first_name and last_name fields of the user
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            
            # Return a JSON response indicating success
            return Response({'message': 'Name updated successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            # Return an error response if any exception occurs during the update
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        # Return an error response for unsupported methods
        return Response({'error': 'Invalid request method'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(["GET", "PUT"])
@permission_classes([AllowAny])
def gallery_categories_list(request):
    if request.method == "GET":
        categories = CakeCategory.objects.all()
        serializer = CakeCategorySerializer(categories, many=True)
        return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def gallery_items_list(request):
    if request.method == "GET":
        items = GalleryItem.objects.all()
        serializer = GalleryItemSerializer(items, many=True)
        return Response(serializer.data)


@api_view(["GET"])
@permission_classes(
    [AllowAny]
)  ###### Add this to allow users to access despite not being logged in
def location_page_content(request):
    if request.method == "GET":
        location_page_content = LocationPageContent.objects.first()
        serializer = LocationPageContentSerializer(location_page_content)
        return Response(serializer.data)


@api_view(["GET"])
@permission_classes(
    [AllowAny]
)  ###### Add this to allow users to access despite not being logged in
def welcome_section(request):
    if request.method == "GET":
        content = HomepageWelcomeSection.objects.first()
        serializer = WelcomeSectionContentSerializer(content)
        return Response(serializer.data)


@api_view(["GET"])
@permission_classes(
    [AllowAny]
)  ###### Add this to allow users to access despite not being logged in
def about_us_section(request):
    if request.method == "GET":
        content = HomepageAboutUsSection.objects.first()
        serializer = AboutUsSectionContentSerializer(content)
        return Response(serializer.data)


@api_view(["GET"])
@permission_classes(
    [AllowAny]
)  ###### Add this to allow users to access despite not being logged in
def gallery_section(request):
    if request.method == "GET":
        content = HomepageGallerySection.objects.first()
        serializer = GallerySectionContentSerializer(content)
        return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def video(request):
    if request.method == "GET":
        items = Video.objects.all()
        serializer = VideoSerializer(items, many=True)
        return Response(serializer.data)
