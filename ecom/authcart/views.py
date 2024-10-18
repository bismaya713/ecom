from django.shortcuts import render,redirect,HttpResponse
from django.contrib.auth.models import User
from django.views.generic import View
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode
from .utils import TokenGenerator,generate_token
from django.utils.encoding import force_bytes,force_str,DjangoUnicodeDecodeError
from django.core.mail import EmailMessage
from django.conf import settings
import six
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth import authenticate,login,logout

class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk) + six.text_type(timestamp) + six.text_type(user.is_active)
        )

account_activation_token = AccountActivationTokenGenerator()

def signup(request):
    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['pass1']
        confirm_password = request.POST['pass2']
        if password != confirm_password:
            messages.warning(request, "Password is not matching")
            return render(request, 'signup.html')
        
        try:
            user = User.objects.get(username=email)
            if not user.is_active:
                email_subject = "Activate Your Account"
                message = render_to_string('activate.html', {
                    'user': user,
                    'domain': '127.0.0.1:8000',  # Change to your domain when deployed
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': account_activation_token.make_token(user),
                })
                email_message = EmailMessage(email_subject, message, settings.EMAIL_HOST_USER, [email])
                email_message.send()
                messages.info(request, "Your account is inactive. An activation link has been resent to your email.")
                return render(request, 'signup.html')
            else:
                messages.info(request, "Email is already taken")
                return render(request, 'signup.html')
        except User.DoesNotExist:
            user = User.objects.create_user(email, email, password)
            user.is_active = False
            user.save()
            email_subject = "Activate Your Account"
            message = render_to_string('activate.html', {
                'user': user,
                'domain': '127.0.0.1:8000',  # Change to your domain when deployed
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            email_message = EmailMessage(email_subject, message, settings.EMAIL_HOST_USER, [email])
            email_message.send()
            messages.success(request, "Activate your account by clicking the link in your email.")
            return redirect('/auth/login/')
    return render(request, "signup.html")

class ActivateAccountView(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except Exception:
            user = None
        if user is not None and account_activation_token.check_token(user, token):
            user.is_active = True
            user.save()
            messages.info(request, "Account activated successfully")
            return redirect('/auth/login')
        return render(request, 'activatefail.html')



def handlelogin(request):
    if request.method == "POST":
        username = request.POST['email']
        userpassword = request.POST['pass1']
        myuser = authenticate(request,username = username,password = userpassword)

        if myuser is not None:
            login(request,myuser)
            messages.success(request,"Login Success")
            return redirect('/')
        
        else:
            messages.error(request,"Invalid Credentials")
            return redirect('/login')
    return render(request,"login.html")


def handlelogout(request):
    logout(request)
    messages.info(request,"Logout Success")
    return render(request,"login.html")