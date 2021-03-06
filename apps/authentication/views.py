# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

# Create your views here.
import os
from django.http.response import JsonResponse

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm, SignUpForm, UserAuthSignUpForm
from django.contrib.auth.models import User
from apps.app.models import UserAuth
from django.http import QueryDict

import json

def login_view(request):
    form = LoginForm(request.POST, None)
    msg = None

    if request.user.is_authenticated: # Redirect Authenticated User to Home Page
        return redirect("/")

    if request.method == "POST":
        if 'type' in request.POST: # For AJAX calls
            if request.POST['type'] in ["authManual", "authAuto"]: # Check Auth type
                # Data from google (Username, Email and ID_Token)
                google = json.loads(request.POST['google']) 

                # Dict converted to QueryDict for Django Forms input
                userAuthRegistrationData = {
                    "google_id_token": google['id_token'],
                    "manual_user": request.POST['type'] == 'authManual'
                }
                userAuthRegistrationDataQueryDict = QueryDict('', mutable=True)
                userAuthRegistrationDataQueryDict.update(userAuthRegistrationData)

                # Split Google Name by space for first and last name
                google_name = google['username'].split(" ")

                if request.POST['type'] == 'authManual' and form.is_valid(): # Manual Authentication
                    username = form.cleaned_data.get("username")
                    password = form.cleaned_data.get("password")

                    # Check if user with email doesn't already exist
                    if (not User.objects.filter(email=google['email']).exists()):
                        # Dict converted to QueryDict for Django Forms input
                        registrationData = {
                            "username": username,
                            "email": google['email'],
                            "password1": password,
                            "password2": password,
                            "first_name": google_name[0] if len(google_name) > 0 else "",
                            "last_name": google_name[1] if len(google_name) > 1 else ""
                        }
                        registrationDataQueryDict = QueryDict('', mutable=True)
                        registrationDataQueryDict.update(registrationData)

                        # Initialize Forms for Data Entry
                        registrationForm = SignUpForm(registrationData)
                        userAuthRegistrationForm = UserAuthSignUpForm(userAuthRegistrationDataQueryDict)

                        # Check input data validity
                        if registrationForm.is_valid() and userAuthRegistrationForm.is_valid():
                            user = registrationForm.save() # new row in User table

                            userAuth = userAuthRegistrationForm.save(commit=False)
                            userAuth.user = user # Set One-to-One relationship between UserAuth and User
                            userAuth.save() # Save row to UserAuth table

                            # Login new user on success
                            userLogin = authenticate(username=username, password=password)
                            if userLogin is not None:
                                login(request, userLogin)
                        else:
                            # Handle any errors and return appropriate error messages
                            errors = registrationForm.errors.as_json()
                            errors_userAuth = userAuthRegistrationForm.errors.as_json()

                            if "username" in errors: # Username Exists
                                return JsonResponse({"result": "failure", "error_msg": "Username Already Exists!"})
                            elif "password" in errors: # Invalid Password
                                return JsonResponse({"result": "failure", "error_msg": "Incorrect Password!"})
                            elif "google_id_token" in errors_userAuth: # Invalid Token
                                return JsonResponse({"result": "failure", "error_msg": "Invalid Credentials!"})
                    else:
                        # Check if email and username belong to the same account
                        userByNameAndEmail = User.objects.filter(username=username, email=google['email'])

                        if len(userByNameAndEmail) > 0:
                            # Check if the user registered manually
                            if UserAuth.objects.filter(user=userByNameAndEmail[0], manual_user=True).exists():
                                # Login user
                                user = authenticate(username=username, password=password)
                                if user is not None:
                                    login(request, user)
                        else:
                            return JsonResponse({"result": "failure", "error_msg": "Invalid Credentials!"})


                elif request.POST['type'] == 'authAuto': # Google Authentication
                    # Check if user with email doesn't already exist
                    if (not User.objects.filter(email=google['email']).exists()):
                        # Dict converted to QueryDict for Django Forms input
                        registrationData = {
                            "username": google['email'],
                            "email": google['email'],
                            "password1": "google_auth",
                            "password2": "google_auth",
                            "first_name": google_name[0] if len(google_name) > 0 else "",
                            "last_name": google_name[1] if len(google_name) > 1 else ""
                        }
                        registrationDataQueryDict = QueryDict('', mutable=True)
                        registrationDataQueryDict.update(registrationData)

                        # Initialize Forms for Data Entry
                        registrationForm = SignUpForm(registrationData)
                        userAuthRegistrationForm = UserAuthSignUpForm(userAuthRegistrationDataQueryDict)

                        # Check input data validity
                        if registrationForm.is_valid() and userAuthRegistrationForm.is_valid():
                            user = registrationForm.save() # new row in User table

                            userAuth = userAuthRegistrationForm.save(commit=False)
                            userAuth.user = user # Set One-to-One relationship between UserAuth and User
                            userAuth.save() # Save row to UserAuth table

                            # Login new user on success
                            userLogin = authenticate(username=google['email'], password="google_auth")
                            if userLogin is not None:
                                login(request, userLogin)
                        else:
                            # Handle any errors and return appropriate error messages
                            errors = userAuthRegistrationForm.errors.as_json()

                            if "google_id_token" in errors: # Invalid Token
                                return JsonResponse({"result": "failure", "error_msg": "Invalid Credentials!"})
                            elif userAuthRegistrationForm.has_error():
                                return JsonResponse({"result": "failure", "error_msg": "Username Already Exists!"})
                    else:
                        # Check if email and username belong to the same account
                        userByNameAndEmail = User.objects.filter(username=google['email'], email=google['email'])

                        if len(userByNameAndEmail) > 0:
                            # Check if the user registered through google auth
                            if UserAuth.objects.filter(user=userByNameAndEmail[0], manual_user=False).exists():
                                # Login user
                                user = authenticate(username=google['email'], password="google_auth")
                                if user is not None:
                                    login(request, user)
                        else:
                            return JsonResponse({"result": "failure", "error_msg": "Invalid Credentials!"})

                
                return JsonResponse({"result": "success"})
            elif request.POST['type'] == "userCheck":
                # This is to check if a user with a given username already exists or not.
                # The user is automatically logged in if the user exists.
                try:
                    # Check if user exists:
                    checkForUser = User.objects.filter(username=request.POST['username'])

                    if len(checkForUser) > 0:
                        checkForUser[0]
                        if UserAuth.objects.filter(user=checkForUser[0], manual_user=True).exists():
                            user = authenticate(username=request.POST['username'], password=request.POST['password'])
                            if user is None:
                                return JsonResponse({"result": "failure"})
                            else:
                                login(request, user)
                                return JsonResponse({"result": "success"})
                    
                    return JsonResponse({"result": "failure"})

                except:
                    return JsonResponse({"result": "failure"})


        #     # if form.is_valid():
        #     return JsonResponse({"result": "success"})
        # else:
        #         msg = 'Invalid credentials'
        # if "type" in request.POST and request.POST['type'] == 'google_auth':
        #     username = request.POST['username']
        #     email = request.POST['email']

        # else:
        # if form.is_valid():
        #     username = form.cleaned_data.get("username")
        #     password = form.cleaned_data.get("password")
        #     print(username)
        #     print(password)
        #     print(request.POST)
        #     user = authenticate(username=username, password=password)
        #     if user is not None:
        #         login(request, user)
        #         if os.getcwd() != '/Users/elisaaoki/biz_dashboard':
        #             return redirect("/google_oauth/redirect/")
        #         else:
        #             return redirect("/")
        #     else:
        #         msg = 'Invalid credentials'
        # else:
        #     msg = 'Error validating the form'

    return render(request, "accounts/login.html", {"form": form, "msg": msg})

def register_user(request):
    msg = None
    success = False

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(username=username, password=raw_password)

            msg = 'User created - please <a href="/login">login</a>.'
            success = True

            # return redirect("/login/")

        else:
            msg = 'Form is not valid'
    else:
        form = SignUpForm()

    return render(request, "accounts/register.html", {"form": form, "msg": msg, "success": success})

def logout_user(request):
    logout(request)

    return JsonResponse({"result": "success"})