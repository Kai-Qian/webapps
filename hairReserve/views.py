# coding=utf-8
from django.core import serializers
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect, render_to_response, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.core.urlresolvers import reverse
# Decorator to use built-in authentication system
from django.contrib.auth.decorators import login_required
import json
# Used to create and manually log in a user
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.template import RequestContext
from django.template.context_processors import csrf
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from hairReserve.s3 import s3_upload, s3_delete
from hairReserve.models import *
from hairReserve.forms import *
import datetime


# from hairReserve.s3 import s3_upload, s3_delete

@login_required
def home(request):
    context = {}
    context['search_form'] = SearchForm()
    results = []
    print request.user
    user = User.objects.get(username=request.user)
    address = Address.objects.get(user=user)
    city = address.city
    barbershops = Barbershop.objects.all()
    # bs = Barbershop.objects.get(name='Nice')
    # for barbershop in barbershops:
    #     if barbershop.address.city == city:
    #         results.append(barbershop)
    # results.append(bs)
    context['results'] = barbershops
    # postings = Posting.objects.order_by('-dateAndTime')
    # context['postings'] = postings
    return render(request, 'home.html', context)


def getallcomments(request):
    context = {}
    barbershop_name = request.POST['barbershop_name']
    barbershop = Barbershop.objects.get(name=barbershop_name)
    comments = Comments.objects.filter(barbershop=barbershop)
    # print barbershop
    # print comments
    context['comments'] = comments
    return render(request, 'comment.html', context)  # , content_type='application/xml')


def postcomment(request):
    c = {}
    c.update(csrf(request))
    context = {}
    print request.POST
    if request.method == 'POST':
        text = request.POST['comment']
        rating = request.POST['rating']
        rating = float(rating)
        barbershop = request.POST['barbershop']
        barbershop_object = Barbershop.objects.get(name=barbershop)
        barbershop_object.number_of_comments += 1
        tmp = float(barbershop_object.total_rating)
        tmp = tmp + rating
        barbershop_object.total_rating = str(tmp)
        barbershop_object.save()
        barbershop_object.rating = str(float(barbershop_object.total_rating) / barbershop_object.number_of_comments)
        barbershop_object.save()
        print barbershop_object.rating
        # context['barbershop'] = barbershop_object
        comment = Comments(user=request.user, text=text, barbershop=barbershop_object,
                           rating=rating)  # don't use objects.create, otherwise it will call get /home?....
        comment.save()
        comments = Comments.objects.filter(barbershop=barbershop_object)
        context['comments'] = comments
        print comments
        return render(request, 'comment.html', context)


@login_required
@transaction.atomic
def profile(request):
    # postings = Posting.objects.filter(user=request.user)
    user = User.objects.get(username=request.user)
    user_form = UserProfileForm(instance=user)  # if you use instance, the content will be shown in the form
    try:
        up = Profile.objects.get(user=user)
    except:
        up = None
    address = Address.objects.get(user=user)
    address_form = AddressForm(instance=address)
    profile_form = ExtraUserProfileForm(instance=up)
    reservations = Reservations.objects.filter(user=user)
    favorites, flag = Favorites.objects.get_or_create(user=user)
    print favorites
    context = {'user_form': user_form, 'profile_form': profile_form, 'address_form': address_form, 'profile': up}
    if not flag:
        barbershops = favorites.barbershop.all()
        context['barbershops'] = barbershops
    now = datetime.datetime.now()
    today = now.date()
    time = now.time()

    upcoming_reservations = []
    past_reservations = []
    for reservation in reservations:
        if reservation.start_date >= today:
            if reservation.start_date > today:
                upcoming_reservations.append(reservation)
            elif reservation.start_date == today:
                if reservation.start_time >= str(time):
                    upcoming_reservations.append(reservation)
                elif reservation.start_time < str(time):
                    past_reservations.append(reservation)
        elif reservation.start_date < today:
            past_reservations.append(reservation)
    context['upcoming_reservations'] = upcoming_reservations
    context['past_reservations'] = past_reservations
    # context['reservations'] = reservations

    return render(request, 'profile.html', context)


@login_required
@transaction.atomic
def post(request):
    context = {}
    errors = []
    postings = request.POST['post']
    if not postings:
        errors.append("There is no post!")
        context['errors'] = errors
        return render(request, 'home.html', context)
    # p = postings.split()
    length = len(postings)
    print length
    if length > 160:
        print 11111111
        errors.append("There should only be 160 words.")
        context['errors'] = errors
        # context['active'] = "active"
        return render(request, 'home.html', context)
    elif 0 <= length <= 160:
        print 22222222222
        # posting = Posting.objects.create(text=postings, user=request.user)
        # posting.save()
        return redirect(reverse('home'))


@transaction.atomic
def register(request):
    context = {}
    if request.method == 'GET':  # when the register page is loaded, it will first send the GET request to load the page
        context['user_form'] = UserForm()
        return render(request, 'register.html', context)
    # user = User()
    user_form = UserForm(
        request.POST)  # , instance=user)#I try to use instance to create the object, but the authenticate failed, so i have to use old method.
    profile_form = ExtraUserProfileForm()  # maybe it is better to use old method, ie create the object through cleaned_data,  for register

    if not user_form.is_valid():
        context['user_form'] = user_form
        return render(request, 'register.html', context)
    context['user_form'] = user_form
    print user_form.cleaned_data['password']  # after run user_form.is_valid() then you can have cleaned_data
    new_user = User.objects.create_user(username=user_form.cleaned_data['username'],
                                        password=user_form.cleaned_data['password'],
                                        first_name=user_form.cleaned_data['first_name'],
                                        last_name=user_form.cleaned_data['last_name'],
                                        email=user_form.cleaned_data['email'])
    new_user.save()

    # user_form.save()  # only after form save, the user has object

    new_address = Address.objects.create(user=new_user,
                                         address='',
                                         city=user_form.cleaned_data['city'],
                                         state='',
                                         zip='')
    new_address.save()
    profile = profile_form.save(commit=False)
    profile.user = new_user  # link the user
    profile.address = new_address  # link the user
    profile.primaryCity = user_form.cleaned_data['city']
    profile.save()

    # Mark the user as inactive to prevent login before email confirmation.
    new_user.is_active = False
    new_user.save()

    # Generate a one-time use token and an email message body
    token = default_token_generator.make_token(new_user)

    email_body = """
Welcome to Connection.  Please click the link below to
verify your email address and complete the registration of your account:

  http://{}{}
""".format(request.get_host(),
           reverse('confirm', args=(new_user.username,
                                    token)))  # we will see http://127.0.0.1:8000/addrbook/confirm-registration/e/49p-73613b0f9d5718672e05, the addrbook is got from reverse
    print request.get_host()  # it is only 127.0.0.1:8000

    send_mail(subject="Verify your email address",
              message=email_body,
              from_email="kaiq@andrew.cmu.edu",
              recipient_list=[new_user.email])

    context['email'] = user_form.cleaned_data['email']
    return render(request, 'needs-confirmation.html', context)
    # Logs in the new user and redirects to his/her todo list
    # user = authenticate(username=user_form.cleaned_data['username'],
    #                     password=user_form.cleaned_data['password'])
    # # user.backend = 'django.contrib.auth.backends.ModelBackend'
    # login(request, user)
    # return redirect(reverse('home'))


@transaction.atomic
def register_as_barbershop(request):
    context = {}
    if request.method == 'GET':  # when the register page is loaded, it will first send the GET request to load the page
        context['user_form'] = UserForm()
        context['address_form'] = AddressForm()
        context['barbershop_form'] = BarbershopForm()
        return render(request, 'registerAsBarbershop.html', context)
    # user = User()
    user_form = UserForm(
        request.POST)  # , instance=user)#I try to use instance to create the object, but the authenticate failed, so i have to use old method.
    address_form = AddressForm(request.POST)
    barbershop_form = BarbershopForm(
        request.POST)  # maybe it is better to use old method, ie create the object through cleaned_data,  for register

    if not user_form.is_valid() or not address_form.is_valid() or not barbershop_form.is_valid():
        context['user_form'] = user_form
        context['address_form'] = address_form
        context['barbershop_form'] = barbershop_form
        return render(request, 'registerAsBarbershop.html', context)
    context['user_form'] = user_form
    context['address_form'] = address_form
    context['barbershop_form'] = barbershop_form
    print user_form.cleaned_data['password']  # after run user_form.is_valid() then you can have cleaned_data

    new_user = User.objects.create_user(username=user_form.cleaned_data['username'],
                                        password=user_form.cleaned_data['password'],
                                        first_name=user_form.cleaned_data['first_name'],
                                        last_name=user_form.cleaned_data['last_name'],
                                        email=user_form.cleaned_data['email'])
    new_user.save()

    # user_form.save()  # only after form save, the user has object

    new_address = Address.objects.create(user=new_user,
                                         address=address_form.cleaned_data['address'],
                                         city=address_form.cleaned_data['city'],
                                         state=address_form.cleaned_data['state'],
                                         zip=address_form.cleaned_data['zip'])
    new_address.save()

    barbershop = barbershop_form.save(commit=False)
    barbershop.user = new_user  # link the user
    barbershop.address = new_address  # link the user
    barbershop.save()

    # Mark the user as inactive to prevent login before email confirmation.
    new_user.is_active = False
    new_user.save()

    # Generate a one-time use token and an email message body
    token = default_token_generator.make_token(new_user)

    email_body = """
Welcome to Connection.  Please click the link below to
verify your email address and complete the registration of your account:

  http://{}{}
""".format(request.get_host(),
           reverse('confirm', args=(new_user.username,
                                    token)))  # we will see http://127.0.0.1:8000/addrbook/confirm-registration/e/49p-73613b0f9d5718672e05, the addrbook is got from reverse
    print request.get_host()  # it is only 127.0.0.1:8000

    send_mail(subject="Verify your email address",
              message=email_body,
              from_email="kaiq@andrew.cmu.edu",
              recipient_list=[new_user.email])

    context['email'] = user_form.cleaned_data['email']
    return render(request, 'needs-confirmation.html', context)


def sendReminder(request):
    reservations = Reservations.objects.all()
    now = datetime.datetime.now()
    today = now.date()
    time1 = datetime.time(01, 00, 00)
    time2 = datetime.time(01, 01, 00)
    yesterday = today - datetime.timedelta(1)
    tomorrow = today + datetime.timedelta(1)
    time = now.time()
    upcoming_reservations = []
    past_reservations = []
    for reservation in reservations:
        if reservation.start_date == tomorrow:
            upcoming_reservations.append(reservation)
        elif reservation.start_date == yesterday:
            past_reservations.append(reservation)
    if time1 <= time <= time2:
        for reservation in upcoming_reservations:
            user = reservation.user
            barbershop = reservation.barbershop
            email_body_tomorrow = "You have a reservation in " + barbershop.name + " at " +reservation.start_time + " tomorrow. Please come to enjoy the service."
            send_mail(subject="Upcoming reservation reminder",
                      message=email_body_tomorrow,
                      from_email="kaiq@andrew.cmu.edu",
                      recipient_list=[user.email])

        for reservation in past_reservations:
            user = reservation.user
            barbershop = reservation.barbershop
            email_body_yesterday = """
                Thank you for coming to . We really appreciate your feedback. If it does not bother you, please click the link below to review the barbershop. Thank you very much.

                  http://{}{}
                """.format(request.get_host(), reverse('follow2', args=(barbershop.name,))) # need to put a "," here
            # print email_body_yesterday
            send_mail(subject="Barbershop review",
                      message=email_body_yesterday,
                      from_email="kaiq@andrew.cmu.edu",
                      recipient_list=[user.email])
    return HttpResponse()


@transaction.atomic
def confirm_registration(request, username, token):  # username and token are in the url, so you need to write them here
    user = get_object_or_404(User, username=username)

    # Send 404 error if token is invalid
    if not default_token_generator.check_token(user, token):
        raise Http404

    # Otherwise token was valid, activate the user.
    user.is_active = True
    user.save()
    return redirect(reverse('login'))
    # return render(request, 'confirmed.html', {})


@login_required
@transaction.atomic
def editprofile(request):
    context = {}
    errors = []
    user = User.objects.get(username=request.user)
    reservations = Reservations.objects.filter(user=user)
    context['reservations'] = reservations
    favorites, flag = Favorites.objects.get_or_create(user=user)
    print favorites
    if not flag:
        barbershops = favorites.barbershop.all()
        context['barbershops'] = barbershops
    email = request.POST['email']
    print request.user.email
    print email
    if not request.user.email == email:
        if User.objects.filter(email__exact=email):
            errors.append('Email has already been used.')
            try:
                up = Profile.objects.get(user=user)
            except:
                up = None
            user_form = UserProfileForm(request.POST, instance=user)
            profile_form = ExtraUserProfileForm(request.POST, request.FILES, instance=up)
            address = Address.objects.get(user=user)
            address_form = AddressForm(request.POST, instance=address)
            if not user_form.is_valid() or not profile_form.is_valid() or not address_form.is_valid():
                profile = Profile.objects.get(user=user)
                context['user_form'] = user_form
                context['profile_form'] = profile_form
                context['address_form'] = address_form
                context['errors'] = errors
                context['profile'] = profile
                return render(request, 'profile.html', context)
            profile = Profile.objects.get(user=user)  # need to declare again, same reason as below
            context['user_form'] = user_form
            context['profile_form'] = profile_form
            context['address_form'] = address_form
            context['errors'] = errors
            context['profile'] = profile
            return render(request, 'profile.html', context)
    user_form = UserProfileForm(request.POST, instance=user)
    try:
        up = Profile.objects.get(user=user)
    except:
        up = None
    print request.POST
    print request.FILES
    profile_form = ExtraUserProfileForm(request.POST, request.FILES, instance=up)
    address = Address.objects.get(user=user)
    address_form = AddressForm(request.POST, instance=address)

    if not user_form.is_valid() or not profile_form.is_valid() or not address_form.is_valid():
        profile = Profile.objects.get(user=user)
        context['user_form'] = user_form
        context['profile_form'] = profile_form
        context['address_form'] = address_form
        context['profile'] = profile
        return render(request, 'profile.html', context)
    print profile_form.cleaned_data['picture']
    profile = profile_form.save(commit=False)
    profile.user = user
    profile.address = address
    if profile_form.cleaned_data['picture']:
        url = s3_upload(profile_form.cleaned_data['picture'], profile.id)
        print url
        profile.picture_url = url
        profile.save()
    # if 'picture' in request.FILES:
    #     profile.picture = request.FILES['picture']
    context['user_form'] = user_form
    context['profile_form'] = profile_form
    context['address_form'] = address_form
    context['profile'] = profile
    message = 'Profile updated successfully!'
    context['message'] = message
    user_form.save()
    profile_form.save()
    address_form.save()
    profile.save()
    reservations = Reservations.objects.filter(user=user)
    context['reservations'] = reservations
    return render(request, 'profile.html', context)


# follow(request, username)'s content is mainly cite from "Learning Djngo Web Development", have some modifications
# https://books.google.com/books?id=Xs_2CQAAQBAJ&pg=PA146&lpg=PA146&dq=django+follow+unfollow&source=bl&ots=tKwWI68tcK&sig=h5Nc7ny6vT6MLJFPjZS2bN2C6n0&hl=zh-CN&sa=X&ved=0ahUKEwin5s-6j_jKAhWPsh4KHYzxBvI4ChDoAQgpMAI#v=onepage&q&f=false
@login_required
@transaction.atomic
def follow(request, barbershopname):
    if request.method == 'GET':
        context = {}
        barbershop = Barbershop.objects.get(name=barbershopname)
        comments = Comments.objects.filter(barbershop=barbershop)
        barbershop_user = User.objects.get(username=barbershop.user)
        add = Address.objects.get(user=barbershop_user)
        ave = add.address
        cit = add.city
        state = add.state
        ave.replace(" ", "+")
        result = ave + "+" + cit + "+" + state
        context['result'] = result
        context['barbershop'] = barbershop
        context['comments'] = comments
        context['search_form'] = SearchForm()
        userProfile = User.objects.get(
            username=request.user.username)  # First get the request user, ie the logged in user
        try:
            userFollowing, status = Favorites.objects.get_or_create(
                user=userProfile)  # use the user to get the Followings object
            print userFollowing
            print barbershopname
            if userFollowing.barbershop.filter(
                    name=barbershopname).exists():  # use Followings object to get the followings field, then you can treate it as a field, use all or filter ans so on
                print 1
                context["following"] = True
            else:
                print 2
                context["following"] = False
        except:
            userFollower = []

        return render(request, 'otherProfile.html', context)

    if request.method == 'POST':
        context = {}
        barbershopname = request.POST['barbershopname']
        barbershop = Barbershop.objects.get(name=barbershopname)
        context['barbershop'] = barbershop
        print barbershop
        follow = request.POST['follow']
        print follow
        user = User.objects.get(username=request.user)
        userFollowing, status = Favorites.objects.get_or_create(user=user)
        if follow == 'true':
            # follow user
            userFollowing.countForFavorites += 1
            userFollowing.barbershop.add(barbershop)  # add and remove can deal with object i the field
            context["following"] = True
        else:
            # unfollow user
            userFollowing.countForFavorites -= 1
            userFollowing.barbershop.remove(barbershop)
            context["following"] = False
        userFollowing.save()
        print "aaaaaaaaaa"
        return render(request, "followOrUnfollow.html", context)
        # return HttpResponse(json.dumps(""), content_type="application/json")


# @login_required
# @transaction.atomic
# def followerStream(request):
#     context = {}
#     postings = []
#     user = User.objects.get(username=request.user.username)  # myself
#     print user
#     print user.followings.all()  # from the user side, it shows the followers
#     # following, status = Followings.objects.get_or_create(user=user)
#     # print following.followings.all()  # from the Followings side, it shows the followings
#     # for usr in following.followings.all():
#     # posting = Posting.objects.filter(user=usr).order_by('-dateAndTime')
#     #     for i in posting:
#     #         postings.append(i)
#     # context['postings'] = postings
#     return render(request, 'followings.html', context)


@login_required
@transaction.atomic
def searchBarbershop(request):
    context = {}
    barbershopsSearchResult = []
    barbershops = Barbershop.objects.all()
    if request.method == 'GET':  # when the register page is loaded, it will first send the GET request to load the page
        context['search_form'] = SearchForm(request.GET)
        return render(request, 'searchBarbershopResult.html', context)
    print request.POST
    context['search_form'] = SearchForm(request.POST)
    service_type = request.POST['service_type']
    date = request.POST['date']
    time = request.POST['time']
    city = request.POST['city']
    context['date'] = date
    context['time'] = time
    context['city'] = city
    context['service_type'] = service_type

    for barbershop in barbershops:
        print str(barbershop.start_date) + "hahahha"
        if barbershop.address.city == city:
            print 111111111111
            if str(barbershop.start_date) <= date <= str(barbershop.end_date):
                print 222222222222
                if barbershop.service_type.find(service_type) != -1:
                    print barbershop.operation_start_time
                    print barbershop.operation_end_time
                    print time
                    if barbershop.operation_start_time <= time <= barbershop.operation_end_time:
                        barbershopsSearchResult.append(barbershop)
                        print 444444444

    context['barbershopsSearchResult'] = barbershopsSearchResult
    return render(request, 'searchBarbershopResult.html', context)


@login_required
@transaction.atomic
def reserveBarbershop(request):
    context = {}
    results = []
    # barbershops = []
    if request.method == 'GET':  # when the register page is loaded, it will first send the GET request to load the page
        service_type = request.GET['service_type']
        date = request.GET['date']
        time = request.GET['time']
        city = request.GET['city']
        print 11111
        print city
        barbershop = request.GET['barbershop']
        barbershop_object = Barbershop.objects.get(name=barbershop)
        if not city:
            city = barbershop_object.address.city
        print barbershop
        context['date'] = date
        context['time'] = time
        context['city'] = city
        context['service_type'] = service_type
        context['barbershop'] = barbershop_object
        return render(request, 'reservationConfirmation.html', context)
    print request.POST
    user = User.objects.get(username=request.user)
    service_type = request.POST['service_type']
    date = request.POST['date']
    time = request.POST['time']
    city = request.POST['city']
    barbershop = request.POST['barbershop']
    barbershop_object = Barbershop.objects.get(name=barbershop)
    start_date = barbershop_object.start_date
    end_date = barbershop_object.end_date
    operation_start_time = barbershop_object.operation_start_time
    operation_end_time = barbershop_object.operation_end_time
    flag = False
    if not str(start_date) <= date <= str(end_date):
        flag = True
        results.append('The barbershop does not work on ' + date + '.')
    if not str(operation_start_time) <= time <= str(operation_end_time):
        flag = True
        results.append('The barbershop does not work at ' + time + '.')
    barbershop_user = User.objects.get(username=barbershop_object.user)
    # address = barbershop_object.address
    add = Address.objects.get(user=barbershop_user)
    print add.address
    ave = add.address
    cit = add.city
    state = add.state
    ave.replace(" ", "+")
    result = ave + "+" + cit + "+" + state

    end_time = ''
    if service_type == 'Cutting':
        tmp = time
        tmp = tmp.replace(':', '')
        num = int(tmp) + 30
        tmp = str(num)
        if len(tmp) == 2:
            tmp = '00' + tmp
        elif len(tmp) == 3:
            tmp = '0' + tmp
        end_time = tmp[:-2] + ':' + tmp[-2:]
    elif service_type == 'Coloring':
        tmp = time
        tmp = tmp.replace(':', '')
        num = int(tmp) + 200
        tmp = str(num)
        if len(tmp) == 3:
            tmp = '0' + tmp
        end_time = tmp[:-2] + ':' + tmp[-2:]
    elif service_type == 'Waving':
        tmp = time
        tmp = tmp.replace(':', '')
        num = int(tmp) + 400
        tmp = str(num)
        if len(tmp) == 3:
            tmp = '0' + tmp
        end_time = tmp[:-2] + ':' + tmp[-2:]

    if not str(operation_start_time) <= end_time <= str(operation_end_time):
        flag = True
        results.append(
            'The time duration of the service ' + service_type + ' will exceed the barbershop operation time does not work at')

    if barbershop_object.service_type.find(service_type) == -1:
        flag = True
        results.append('Sorry, the barbershop does not provide the ' + service_type + ' service.')


    if flag == True:
        context['results'] = results
        context['date'] = date
        context['time'] = time
        context['city'] = city
        context['service_type'] = service_type
        return render(request, 'reserveNotSucceed.html', context)

    context['result'] = result
    context['barbershop'] = barbershop_object
    context['date'] = date
    context['time'] = time
    context['city'] = city
    context['service_type'] = service_type
    new_reservation = Reservations(user=user, service_type=service_type, start_date=date, start_time=time,
                                   end_time=end_time,
                                   barbershop=barbershop_object)
    new_reservation.save()
    return render(request, 'afterReservationConfirmation.html', context)


@login_required
@transaction.atomic
def reserveThroughFavorites(request):
    context = {}
    context['search_form'] = SearchForm()
    barbershop = request.POST['barbershop']
    city = request.POST['city']
    context['city'] = city
    barbershop_object = Barbershop.objects.get(name=barbershop)
    context['barbershop'] = barbershop_object
    # postings = Posting.objects.order_by('-dateAndTime')
    # context['postings'] = postings
    return render(request, 'reserveThroughFavorites.html', context)


# @login_required
# def CreateCalEvent(request):
#    try:
#        import argparse
#        flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
#    except ImportError:
#        flags = None

#    SCOPES = 'https://www.googleapis.com/auth/calendar'
#    store = file.Storage('storage.json')
#    creds = store.get()
#    if not creds or creds.invalid:
#        flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
#        creds = tools.run_flow(flow, store, flags) \
#            if flags else tools.run(flow, store)
#                CAL = build('calendar', 'v3', http=creds.authorize(Http()))

#    GMT_OFF = '-07:00'      # PDT/MST/GMT-7
#    EVENT = {
#        'summary': 'Dinner with friends',
#        'start':  {'dateTime': '2015-09-15T19:00:00%s' % GMT_OFF},
#        'end':    {'dateTime': '2015-09-15T22:00:00%s' % GMT_OFF},
#        'attendees': [
#            {'email': 'friend1@example.com'},
#            {'email': 'friend2@example.com'},
#        ],
#    }

@login_required
def barbershopMgmtBoard(request):
    if request.method == 'GET':  # when the register page is loaded, it will first send the GET request to load the page
        return render(request, 'barbershopMgmt.html')


# @login_required
def barbershopLogin(request):
    context = {}
    error = []
    print 11111111111
    if request.method == 'GET':
        context['loginForm'] = LoginUserForm
        return render(request, 'barbershopLogin.html', context)
    else:
        username = request.POST['username']
        password = request.POST['password']
        barbershop_name = request.POST['name']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                barbershops = Barbershop.objects.filter(user=user)
                for barbershop in barbershops:
                    if barbershop.name == barbershop_name:
                        # barbershop = Barbershop.objects.get(name=barbershop_name)
                        login(request, user)
                        # context['barbershop'] = barbershop
                        # context['user'] = user
                        # return render(request, 'barbershopMgmt.html', context)
                        return redirect(reverse('redirectToMgmt',
                                                kwargs={'barbershop_name': barbershop_name, 'user_name': username}))
                error.append("User and barbershop doesn't match.")
                context['loginForm'] = LoginUserForm
                context['errors'] = error
                return render(request, 'barbershopLogin.html', context)
            else:
                error.append("The user is disabled.")
                context['loginForm'] = LoginUserForm
                context['errors'] = error
                return render(request, 'barbershopLogin.html', context)
        # Return a 'disabled account' error message
        else:
            error.append("The user doesn't exist.")
            context['loginForm'] = LoginUserForm
            context['errors'] = error
            return render(request, 'barbershopLogin.html', context)
            # Return an 'invalid login' error message.


def returnToMgmt(request):
    username = request.user
    barbershop_name = request.GET['barbershop']
    return redirect(reverse('redirectToMgmt',
                            kwargs={'barbershop_name': barbershop_name, 'user_name': username}))


def redirectToMgmt(request, barbershop_name, user_name):
    context = {}
    all_reservations = []
    all_reservations_yesterday = []
    all_reservations_tomorrow = []

    dict_r0000_0030 = {}
    dict_r0000_0030['key1'] = '0000'
    dict_r0030_0100 = {}
    dict_r0030_0100['key1'] = '0030'
    dict_r0100_0130 = {}
    dict_r0100_0130['key1'] = '0100'
    dict_r0130_0200 = {}
    dict_r0130_0200['key1'] = '0130'
    dict_r0200_0230 = {}
    dict_r0200_0230['key1'] = '0200'
    dict_r0230_0300 = {}
    dict_r0230_0300['key1'] = '0230'
    dict_r0300_0330 = {}
    dict_r0300_0330['key1'] = '0300'
    dict_r0330_0400 = {}
    dict_r0330_0400['key1'] = '0330'
    dict_r0400_0430 = {}
    dict_r0400_0430['key1'] = '0400'
    dict_r0430_0500 = {}
    dict_r0430_0500['key1'] = '0430'
    dict_r0500_0530 = {}
    dict_r0500_0530['key1'] = '0500'
    dict_r0530_0600 = {}
    dict_r0530_0600['key1'] = '0530'
    dict_r0600_0630 = {}
    dict_r0600_0630['key1'] = '0600'
    dict_r0630_0700 = {}
    dict_r0630_0700['key1'] = '0630'
    dict_r0700_0730 = {}
    dict_r0700_0730['key1'] = '0700'
    dict_r0730_0800 = {}
    dict_r0730_0800['key1'] = '0730'
    dict_r0800_0830 = {}
    dict_r0800_0830['key1'] = '0800'
    dict_r0830_0900 = {}
    dict_r0830_0900['key1'] = '0830'
    dict_r0900_0930 = {}
    dict_r0900_0930['key1'] = '0900'
    dict_r0930_1000 = {}
    dict_r0930_1000['key1'] = '0930'
    dict_r1000_1030 = {}
    dict_r1000_1030['key1'] = '1000'
    dict_r1030_1100 = {}
    dict_r1030_1100['key1'] = '1030'
    dict_r1100_1130 = {}
    dict_r1100_1130['key1'] = '1100'
    dict_r1130_1200 = {}
    dict_r1130_1200['key1'] = '1130'
    dict_r1200_1230 = {}
    dict_r1200_1230['key1'] = '1200'
    dict_r1230_1300 = {}
    dict_r1230_1300['key1'] = '1230'
    dict_r1300_1330 = {}
    dict_r1300_1330['key1'] = '1300'
    dict_r1330_1400 = {}
    dict_r1330_1400['key1'] = '1330'
    dict_r1400_1430 = {}
    dict_r1400_1430['key1'] = '1400'
    dict_r1430_1500 = {}
    dict_r1430_1500['key1'] = '1430'
    dict_r1500_1530 = {}
    dict_r1500_1530['key1'] = '1500'
    dict_r1530_1600 = {}
    dict_r1530_1600['key1'] = '1530'
    dict_r1600_1630 = {}
    dict_r1600_1630['key1'] = '1600'
    dict_r1630_1700 = {}
    dict_r1630_1700['key1'] = '1630'
    dict_r1700_1730 = {}
    dict_r1700_1730['key1'] = '1700'
    dict_r1730_1800 = {}
    dict_r1730_1800['key1'] = '1730'
    dict_r1800_1830 = {}
    dict_r1800_1830['key1'] = '1800'
    dict_r1830_1900 = {}
    dict_r1830_1900['key1'] = '1830'
    dict_r1900_1930 = {}
    dict_r1900_1930['key1'] = '1900'
    dict_r1930_2000 = {}
    dict_r1930_2000['key1'] = '1930'
    dict_r2000_2030 = {}
    dict_r2000_2030['key1'] = '2000'
    dict_r2030_2100 = {}
    dict_r2030_2100['key1'] = '2030'
    dict_r2100_2130 = {}
    dict_r2100_2130['key1'] = '2100'
    dict_r2130_2200 = {}
    dict_r2130_2200['key1'] = '2130'
    dict_r2200_2230 = {}
    dict_r2200_2230['key1'] = '2200'
    dict_r2230_2300 = {}
    dict_r2230_2300['key1'] = '2230'
    dict_r2300_2330 = {}
    dict_r2300_2330['key1'] = '2300'
    dict_r2330_0000 = {}
    dict_r2330_0000['key1'] = '2330'

    r0000_0030 = []
    r0030_0100 = []
    r0100_0130 = []
    r0130_0200 = []
    r0200_0230 = []
    r0230_0300 = []
    r0300_0330 = []
    r0330_0400 = []
    r0400_0430 = []
    r0430_0500 = []
    r0500_0530 = []
    r0530_0600 = []
    r0600_0630 = []
    r0630_0700 = []
    r0700_0730 = []
    r0730_0800 = []
    r0800_0830 = []
    r0830_0900 = []
    r0900_0930 = []
    r0930_1000 = []
    r1000_1030 = []
    r1030_1100 = []
    r1100_1130 = []
    r1130_1200 = []
    r1200_1230 = []
    r1230_1300 = []
    r1300_1330 = []
    r1330_1400 = []
    r1400_1430 = []
    r1430_1500 = []
    r1500_1530 = []
    r1530_1600 = []
    r1600_1630 = []
    r1630_1700 = []
    r1700_1730 = []
    r1730_1800 = []
    r1800_1830 = []
    r1830_1900 = []
    r1900_1930 = []
    r1930_2000 = []
    r2000_2030 = []
    r2030_2100 = []
    r2100_2130 = []
    r2130_2200 = []
    r2200_2230 = []
    r2230_2300 = []
    r2300_2330 = []
    r2330_0000 = []

    dict_r0000_0030_yesterday = {}
    dict_r0000_0030_yesterday['key1'] = '0000_yesterday'
    dict_r0030_0100_yesterday = {}
    dict_r0030_0100_yesterday['key1'] = '0030_yesterday'
    dict_r0100_0130_yesterday = {}
    dict_r0100_0130_yesterday['key1'] = '0100_yesterday'
    dict_r0130_0200_yesterday = {}
    dict_r0130_0200_yesterday['key1'] = '0130_yesterday'
    dict_r0200_0230_yesterday = {}
    dict_r0200_0230_yesterday['key1'] = '0200_yesterday'
    dict_r0230_0300_yesterday = {}
    dict_r0230_0300_yesterday['key1'] = '0230_yesterday'
    dict_r0300_0330_yesterday = {}
    dict_r0300_0330_yesterday['key1'] = '0300_yesterday'
    dict_r0330_0400_yesterday = {}
    dict_r0330_0400_yesterday['key1'] = '0330_yesterday'
    dict_r0400_0430_yesterday = {}
    dict_r0400_0430_yesterday['key1'] = '0400_yesterday'
    dict_r0430_0500_yesterday = {}
    dict_r0430_0500_yesterday['key1'] = '0430_yesterday'
    dict_r0500_0530_yesterday = {}
    dict_r0500_0530_yesterday['key1'] = '0500_yesterday'
    dict_r0530_0600_yesterday = {}
    dict_r0530_0600_yesterday['key1'] = '0530_yesterday'
    dict_r0600_0630_yesterday = {}
    dict_r0600_0630_yesterday['key1'] = '0600_yesterday'
    dict_r0630_0700_yesterday = {}
    dict_r0630_0700_yesterday['key1'] = '0630_yesterday'
    dict_r0700_0730_yesterday = {}
    dict_r0700_0730_yesterday['key1'] = '0700_yesterday'
    dict_r0730_0800_yesterday = {}
    dict_r0730_0800_yesterday['key1'] = '0730_yesterday'
    dict_r0800_0830_yesterday = {}
    dict_r0800_0830_yesterday['key1'] = '0800_yesterday'
    dict_r0830_0900_yesterday = {}
    dict_r0830_0900_yesterday['key1'] = '0830_yesterday'
    dict_r0900_0930_yesterday = {}
    dict_r0900_0930_yesterday['key1'] = '0900_yesterday'
    dict_r0930_1000_yesterday = {}
    dict_r0930_1000_yesterday['key1'] = '0930_yesterday'
    dict_r1000_1030_yesterday = {}
    dict_r1000_1030_yesterday['key1'] = '1000_yesterday'
    dict_r1030_1100_yesterday = {}
    dict_r1030_1100_yesterday['key1'] = '1030_yesterday'
    dict_r1100_1130_yesterday = {}
    dict_r1100_1130_yesterday['key1'] = '1100_yesterday'
    dict_r1130_1200_yesterday = {}
    dict_r1130_1200_yesterday['key1'] = '1130_yesterday'
    dict_r1200_1230_yesterday = {}
    dict_r1200_1230_yesterday['key1'] = '1200_yesterday'
    dict_r1230_1300_yesterday = {}
    dict_r1230_1300_yesterday['key1'] = '1230_yesterday'
    dict_r1300_1330_yesterday = {}
    dict_r1300_1330_yesterday['key1'] = '1300_yesterday'
    dict_r1330_1400_yesterday = {}
    dict_r1330_1400_yesterday['key1'] = '1330_yesterday'
    dict_r1400_1430_yesterday = {}
    dict_r1400_1430_yesterday['key1'] = '1400_yesterday'
    dict_r1430_1500_yesterday = {}
    dict_r1430_1500_yesterday['key1'] = '1430_yesterday'
    dict_r1500_1530_yesterday = {}
    dict_r1500_1530_yesterday['key1'] = '1500_yesterday'
    dict_r1530_1600_yesterday = {}
    dict_r1530_1600_yesterday['key1'] = '1530_yesterday'
    dict_r1600_1630_yesterday = {}
    dict_r1600_1630_yesterday['key1'] = '1600_yesterday'
    dict_r1630_1700_yesterday = {}
    dict_r1630_1700_yesterday['key1'] = '1630_yesterday'
    dict_r1700_1730_yesterday = {}
    dict_r1700_1730_yesterday['key1'] = '1700_yesterday'
    dict_r1730_1800_yesterday = {}
    dict_r1730_1800_yesterday['key1'] = '1730_yesterday'
    dict_r1800_1830_yesterday = {}
    dict_r1800_1830_yesterday['key1'] = '1800_yesterday'
    dict_r1830_1900_yesterday = {}
    dict_r1830_1900_yesterday['key1'] = '1830_yesterday'
    dict_r1900_1930_yesterday = {}
    dict_r1900_1930_yesterday['key1'] = '1900_yesterday'
    dict_r1930_2000_yesterday = {}
    dict_r1930_2000_yesterday['key1'] = '1930_yesterday'
    dict_r2000_2030_yesterday = {}
    dict_r2000_2030_yesterday['key1'] = '2000_yesterday'
    dict_r2030_2100_yesterday = {}
    dict_r2030_2100_yesterday['key1'] = '2030_yesterday'
    dict_r2100_2130_yesterday = {}
    dict_r2100_2130_yesterday['key1'] = '2100_yesterday'
    dict_r2130_2200_yesterday = {}
    dict_r2130_2200_yesterday['key1'] = '2130_yesterday'
    dict_r2200_2230_yesterday = {}
    dict_r2200_2230_yesterday['key1'] = '2200_yesterday'
    dict_r2230_2300_yesterday = {}
    dict_r2230_2300_yesterday['key1'] = '2230_yesterday'
    dict_r2300_2330_yesterday = {}
    dict_r2300_2330_yesterday['key1'] = '2300_yesterday'
    dict_r2330_0000_yesterday = {}
    dict_r2330_0000_yesterday['key1'] = '2330_yesterday'

    r0000_0030_yesterday = []
    r0030_0100_yesterday = []
    r0100_0130_yesterday = []
    r0130_0200_yesterday = []
    r0200_0230_yesterday = []
    r0230_0300_yesterday = []
    r0300_0330_yesterday = []
    r0330_0400_yesterday = []
    r0400_0430_yesterday = []
    r0430_0500_yesterday = []
    r0500_0530_yesterday = []
    r0530_0600_yesterday = []
    r0600_0630_yesterday = []
    r0630_0700_yesterday = []
    r0700_0730_yesterday = []
    r0730_0800_yesterday = []
    r0800_0830_yesterday = []
    r0830_0900_yesterday = []
    r0900_0930_yesterday = []
    r0930_1000_yesterday = []
    r1000_1030_yesterday = []
    r1030_1100_yesterday = []
    r1100_1130_yesterday = []
    r1130_1200_yesterday = []
    r1200_1230_yesterday = []
    r1230_1300_yesterday = []
    r1300_1330_yesterday = []
    r1330_1400_yesterday = []
    r1400_1430_yesterday = []
    r1430_1500_yesterday = []
    r1500_1530_yesterday = []
    r1530_1600_yesterday = []
    r1600_1630_yesterday = []
    r1630_1700_yesterday = []
    r1700_1730_yesterday = []
    r1730_1800_yesterday = []
    r1800_1830_yesterday = []
    r1830_1900_yesterday = []
    r1900_1930_yesterday = []
    r1930_2000_yesterday = []
    r2000_2030_yesterday = []
    r2030_2100_yesterday = []
    r2100_2130_yesterday = []
    r2130_2200_yesterday = []
    r2200_2230_yesterday = []
    r2230_2300_yesterday = []
    r2300_2330_yesterday = []
    r2330_0000_yesterday = []

    dict_r0000_0030_tomorrow = {}
    dict_r0000_0030_tomorrow['key1'] = '0000_tomorrow'
    dict_r0030_0100_tomorrow = {}
    dict_r0030_0100_tomorrow['key1'] = '0030_tomorrow'
    dict_r0100_0130_tomorrow = {}
    dict_r0100_0130_tomorrow['key1'] = '0100_tomorrow'
    dict_r0130_0200_tomorrow = {}
    dict_r0130_0200_tomorrow['key1'] = '0130_tomorrow'
    dict_r0200_0230_tomorrow = {}
    dict_r0200_0230_tomorrow['key1'] = '0200_tomorrow'
    dict_r0230_0300_tomorrow = {}
    dict_r0230_0300_tomorrow['key1'] = '0230_tomorrow'
    dict_r0300_0330_tomorrow = {}
    dict_r0300_0330_tomorrow['key1'] = '0300_tomorrow'
    dict_r0330_0400_tomorrow = {}
    dict_r0330_0400_tomorrow['key1'] = '0330_tomorrow'
    dict_r0400_0430_tomorrow = {}
    dict_r0400_0430_tomorrow['key1'] = '0400_tomorrow'
    dict_r0430_0500_tomorrow = {}
    dict_r0430_0500_tomorrow['key1'] = '0430_tomorrow'
    dict_r0500_0530_tomorrow = {}
    dict_r0500_0530_tomorrow['key1'] = '0500_tomorrow'
    dict_r0530_0600_tomorrow = {}
    dict_r0530_0600_tomorrow['key1'] = '0530_tomorrow'
    dict_r0600_0630_tomorrow = {}
    dict_r0600_0630_tomorrow['key1'] = '0600_tomorrow'
    dict_r0630_0700_tomorrow = {}
    dict_r0630_0700_tomorrow['key1'] = '0630_tomorrow'
    dict_r0700_0730_tomorrow = {}
    dict_r0700_0730_tomorrow['key1'] = '0700_tomorrow'
    dict_r0730_0800_tomorrow = {}
    dict_r0730_0800_tomorrow['key1'] = '0730_tomorrow'
    dict_r0800_0830_tomorrow = {}
    dict_r0800_0830_tomorrow['key1'] = '0800_tomorrow'
    dict_r0830_0900_tomorrow = {}
    dict_r0830_0900_tomorrow['key1'] = '0830_tomorrow'
    dict_r0900_0930_tomorrow = {}
    dict_r0900_0930_tomorrow['key1'] = '0900_tomorrow'
    dict_r0930_1000_tomorrow = {}
    dict_r0930_1000_tomorrow['key1'] = '0930_tomorrow'
    dict_r1000_1030_tomorrow = {}
    dict_r1000_1030_tomorrow['key1'] = '1000_tomorrow'
    dict_r1030_1100_tomorrow = {}
    dict_r1030_1100_tomorrow['key1'] = '1030_tomorrow'
    dict_r1100_1130_tomorrow = {}
    dict_r1100_1130_tomorrow['key1'] = '1100_tomorrow'
    dict_r1130_1200_tomorrow = {}
    dict_r1130_1200_tomorrow['key1'] = '1130_tomorrow'
    dict_r1200_1230_tomorrow = {}
    dict_r1200_1230_tomorrow['key1'] = '1200_tomorrow'
    dict_r1230_1300_tomorrow = {}
    dict_r1230_1300_tomorrow['key1'] = '1230_tomorrow'
    dict_r1300_1330_tomorrow = {}
    dict_r1300_1330_tomorrow['key1'] = '1300_tomorrow'
    dict_r1330_1400_tomorrow = {}
    dict_r1330_1400_tomorrow['key1'] = '1330_tomorrow'
    dict_r1400_1430_tomorrow = {}
    dict_r1400_1430_tomorrow['key1'] = '1400_tomorrow'
    dict_r1430_1500_tomorrow = {}
    dict_r1430_1500_tomorrow['key1'] = '1430_tomorrow'
    dict_r1500_1530_tomorrow = {}
    dict_r1500_1530_tomorrow['key1'] = '1500_tomorrow'
    dict_r1530_1600_tomorrow = {}
    dict_r1530_1600_tomorrow['key1'] = '1530_tomorrow'
    dict_r1600_1630_tomorrow = {}
    dict_r1600_1630_tomorrow['key1'] = '1600_tomorrow'
    dict_r1630_1700_tomorrow = {}
    dict_r1630_1700_tomorrow['key1'] = '1630_tomorrow'
    dict_r1700_1730_tomorrow = {}
    dict_r1700_1730_tomorrow['key1'] = '1700_tomorrow'
    dict_r1730_1800_tomorrow = {}
    dict_r1730_1800_tomorrow['key1'] = '1730_tomorrow'
    dict_r1800_1830_tomorrow = {}
    dict_r1800_1830_tomorrow['key1'] = '1800_tomorrow'
    dict_r1830_1900_tomorrow = {}
    dict_r1830_1900_tomorrow['key1'] = '1830_tomorrow'
    dict_r1900_1930_tomorrow = {}
    dict_r1900_1930_tomorrow['key1'] = '1900_tomorrow'
    dict_r1930_2000_tomorrow = {}
    dict_r1930_2000_tomorrow['key1'] = '1930_tomorrow'
    dict_r2000_2030_tomorrow = {}
    dict_r2000_2030_tomorrow['key1'] = '2000_tomorrow'
    dict_r2030_2100_tomorrow = {}
    dict_r2030_2100_tomorrow['key1'] = '2030_tomorrow'
    dict_r2100_2130_tomorrow = {}
    dict_r2100_2130_tomorrow['key1'] = '2100_tomorrow'
    dict_r2130_2200_tomorrow = {}
    dict_r2130_2200_tomorrow['key1'] = '2130_tomorrow'
    dict_r2200_2230_tomorrow = {}
    dict_r2200_2230_tomorrow['key1'] = '2200_tomorrow'
    dict_r2230_2300_tomorrow = {}
    dict_r2230_2300_tomorrow['key1'] = '2230_tomorrow'
    dict_r2300_2330_tomorrow = {}
    dict_r2300_2330_tomorrow['key1'] = '2300_tomorrow'
    dict_r2330_0000_tomorrow = {}
    dict_r2330_0000_tomorrow['key1'] = '2330_tomorrow'

    r0000_0030_tomorrow = []
    r0030_0100_tomorrow = []
    r0100_0130_tomorrow = []
    r0130_0200_tomorrow = []
    r0200_0230_tomorrow = []
    r0230_0300_tomorrow = []
    r0300_0330_tomorrow = []
    r0330_0400_tomorrow = []
    r0400_0430_tomorrow = []
    r0430_0500_tomorrow = []
    r0500_0530_tomorrow = []
    r0530_0600_tomorrow = []
    r0600_0630_tomorrow = []
    r0630_0700_tomorrow = []
    r0700_0730_tomorrow = []
    r0730_0800_tomorrow = []
    r0800_0830_tomorrow = []
    r0830_0900_tomorrow = []
    r0900_0930_tomorrow = []
    r0930_1000_tomorrow = []
    r1000_1030_tomorrow = []
    r1030_1100_tomorrow = []
    r1100_1130_tomorrow = []
    r1130_1200_tomorrow = []
    r1200_1230_tomorrow = []
    r1230_1300_tomorrow = []
    r1300_1330_tomorrow = []
    r1330_1400_tomorrow = []
    r1400_1430_tomorrow = []
    r1430_1500_tomorrow = []
    r1500_1530_tomorrow = []
    r1530_1600_tomorrow = []
    r1600_1630_tomorrow = []
    r1630_1700_tomorrow = []
    r1700_1730_tomorrow = []
    r1730_1800_tomorrow = []
    r1800_1830_tomorrow = []
    r1830_1900_tomorrow = []
    r1900_1930_tomorrow = []
    r1930_2000_tomorrow = []
    r2000_2030_tomorrow = []
    r2030_2100_tomorrow = []
    r2100_2130_tomorrow = []
    r2130_2200_tomorrow = []
    r2200_2230_tomorrow = []
    r2230_2300_tomorrow = []
    r2300_2330_tomorrow = []
    r2330_0000_tomorrow = []

    # print request.GET
    barbershop_name = barbershop_name
    username = user_name
    # username = request.GET['user_name']
    user = User.objects.get(username=username)
    barbershops = Barbershop.objects.filter(user=user)
    # barbershop_name = request.GET['barbershop_name']
    # barbershops = Barbershop.objects.filter(user=user)
    for barbershop in barbershops:
        if barbershop.name == barbershop_name:
            barbershop = Barbershop.objects.get(name=barbershop_name)
            now = datetime.datetime.now()
            today = now.date()
            yesterday = today - datetime.timedelta(1)
            tomorrow = today + datetime.timedelta(1)
            start_date = barbershop.start_date
            end_date = barbershop.end_date

            print yesterday
            print today
            print tomorrow
            reservations = Reservations.objects.filter(barbershop=barbershop, start_date=today)
            reservations_yesterday = Reservations.objects.filter(barbershop=barbershop, start_date=yesterday)
            reservations_tomorrow = Reservations.objects.filter(barbershop=barbershop, start_date=tomorrow)
            for reservation in reservations:
                if '00:00' <= reservation.start_time < '00:30':
                    r0000_0030.append(reservation)
                if '00:00' < reservation.end_time <= '00:30' or reservation.start_time < '00:30' < reservation.end_time:
                    if r0000_0030.count(reservation) == 0:
                        r0000_0030.append(reservation)
                if '00:30' <= reservation.start_time < '01:00':
                    r0030_0100.append(reservation)
                if '00:30' < reservation.end_time <= '01:00' or reservation.start_time < '01:00' < reservation.end_time:
                    if r0030_0100.count(reservation) == 0:
                        r0030_0100.append(reservation)
                if '01:00' <= reservation.start_time < '01:30':
                    r0100_0130.append(reservation)
                if '01:00' < reservation.end_time <= '01:30' or reservation.start_time < '01:30' < reservation.end_time:
                    if r0100_0130.count(reservation) == 0:
                        r0100_0130.append(reservation)
                if '01:30' <= reservation.start_time < '02:00':
                    r0130_0200.append(reservation)
                if '01:30' < reservation.end_time <= '02:00' or reservation.start_time < '02:00' < reservation.end_time:
                    if r0130_0200.count(reservation) == 0:
                        r0130_0200.append(reservation)
                if '02:00' <= reservation.start_time < '02:30':
                    r0200_0230.append(reservation)
                if '02:00' < reservation.end_time <= '02:30' or reservation.start_time < '02:30' < reservation.end_time:
                    if r0200_0230.count(reservation) == 0:
                        r0200_0230.append(reservation)
                if '02:30' <= reservation.start_time < '03:00':
                    r0230_0300.append(reservation)
                if '02:30' < reservation.end_time <= '03:00' or reservation.start_time < '03:00' < reservation.end_time:
                    if r0230_0300.count(reservation) == 0:
                        r0230_0300.append(reservation)
                if '03:00' <= reservation.start_time < '03:30':
                    r0300_0330.append(reservation)
                if '03:00' < reservation.end_time <= '03:30' or reservation.start_time < '03:30' < reservation.end_time:
                    if r0300_0330.count(reservation) == 0:
                        r0300_0330.append(reservation)
                if '03:30' <= reservation.start_time < '04:00':
                    r0330_0400.append(reservation)
                if '03:30' < reservation.end_time <= '04:00' or reservation.start_time < '04:00' < reservation.end_time:
                    if r0330_0400.count(reservation) == 0:
                        r0330_0400.append(reservation)
                if '04:00' <= reservation.start_time < '04:30':
                    r0400_0430.append(reservation)
                if '04:00' < reservation.end_time <= '04:30' or reservation.start_time < '04:30' < reservation.end_time:
                    if r0400_0430.count(reservation) == 0:
                        r0400_0430.append(reservation)
                if '04:30' <= reservation.start_time < '05:00':
                    r0430_0500.append(reservation)
                if '04:30' < reservation.end_time <= '05:00' or reservation.start_time < '05:00' < reservation.end_time:
                    if r0430_0500.count(reservation) == 0:
                        r0430_0500.append(reservation)
                if '05:00' <= reservation.start_time < '05:30':
                    r0500_0530.append(reservation)
                if '05:00' < reservation.end_time <= '05:30' or reservation.start_time < '05:30' < reservation.end_time:
                    if r0500_0530.count(reservation) == 0:
                        r0500_0530.append(reservation)
                if '05:30' <= reservation.start_time < '06:00':
                    r0530_0600.append(reservation)
                if '05:30' < reservation.end_time <= '06:00' or reservation.start_time < '06:00' < reservation.end_time:
                    if r0530_0600.count(reservation) == 0:
                        r0530_0600.append(reservation)
                if '06:00' <= reservation.start_time < '06:30':
                    r0600_0630.append(reservation)
                if '06:00' < reservation.end_time <= '06:30' or reservation.start_time < '06:30' < reservation.end_time:
                    if r0600_0630.count(reservation) == 0:
                        r0600_0630.append(reservation)
                if '06:30' <= reservation.start_time < '07:00':
                    r0630_0700.append(reservation)
                if '06:30' < reservation.end_time <= '07:00' or reservation.start_time < '07:00' < reservation.end_time:
                    if r0630_0700.count(reservation) == 0:
                        r0630_0700.append(reservation)
                if '07:00' <= reservation.start_time < '07:30':
                    r0700_0730.append(reservation)
                if '07:00' < reservation.end_time <= '07:30' or reservation.start_time < '07:30' < reservation.end_time:
                    if r0700_0730.count(reservation) == 0:
                        r0700_0730.append(reservation)

                if '07:30' <= reservation.start_time < '08:00':
                    r0730_0800.append(reservation)
                if '07:30' < reservation.end_time <= '08:00' or reservation.start_time < '08:00' < reservation.end_time:
                    if r0730_0800.count(reservation) == 0:
                        r0730_0800.append(reservation)
                if '08:00' <= reservation.start_time < '08:30':
                    r0800_0830.append(reservation)
                if '08:00' < reservation.end_time <= '08:30' or reservation.start_time < '08:30' < reservation.end_time:
                    if r0800_0830.count(reservation) == 0:
                        r0800_0830.append(reservation)
                if '08:30' <= reservation.start_time < '09:00':
                    r0830_0900.append(reservation)
                if '08:30' < reservation.end_time <= '09:00' or reservation.start_time < '09:00' < reservation.end_time:
                    if r0830_0900.count(reservation) == 0:
                        r0830_0900.append(reservation)
                if '09:00' <= reservation.start_time < '09:30':
                    r0900_0930.append(reservation)
                if '09:00' < reservation.end_time <= '09:30' or reservation.start_time < '09:30' < reservation.end_time:
                    if r0900_0930.count(reservation) == 0:
                        r0900_0930.append(reservation)
                if '09:30' <= reservation.start_time < '10:00':
                    r0930_1000.append(reservation)
                if '09:30' < reservation.end_time <= '10:00' or reservation.start_time < '10:00' < reservation.end_time:
                    if r0930_1000.count(reservation) == 0:
                        r0930_1000.append(reservation)
                if '10:00' <= reservation.start_time < '10:30':
                    r1000_1030.append(reservation)
                if '10:00' < reservation.end_time <= '10:30' or reservation.start_time < '10:30' < reservation.end_time:
                    if r1000_1030.count(reservation) == 0:
                        r1000_1030.append(reservation)
                if '10:30' <= reservation.start_time < '11:00':
                    r1030_1100.append(reservation)
                if '10:30' < reservation.end_time <= '11:00' or reservation.start_time < '11:00' < reservation.end_time:
                    if r1030_1100.count(reservation) == 0:
                        r1030_1100.append(reservation)

                if '11:00' <= reservation.start_time < '11:30':
                    r1100_1130.append(reservation)
                if '11:00' < reservation.end_time <= '11:30' or reservation.start_time < '11:30' < reservation.end_time:
                    if r1100_1130.count(reservation) == 0:
                        r1100_1130.append(reservation)
                if '11:30' <= reservation.start_time < '12:00':
                    r1130_1200.append(reservation)
                if '11:30' < reservation.end_time <= '12:00' or reservation.start_time < '12:00' < reservation.end_time:
                    if r1130_1200.count(reservation) == 0:
                        r1130_1200.append(reservation)
                if '12:00' <= reservation.start_time < '12:30':
                    r1200_1230.append(reservation)
                if '12:00' < reservation.end_time <= '12:30' or reservation.start_time < '12:30' < reservation.end_time:
                    if r1200_1230.count(reservation) == 0:
                        r1200_1230.append(reservation)
                if '12:30' <= reservation.start_time < '13:00':
                    r1230_1300.append(reservation)
                if '12:30' < reservation.end_time <= '13:00' or reservation.start_time < '13:00' < reservation.end_time:
                    if r1230_1300.count(reservation) == 0:
                        r1230_1300.append(reservation)
                if '13:00' <= reservation.start_time < '13:30':
                    r1300_1330.append(reservation)
                if '13:00' < reservation.end_time <= '13:30' or reservation.start_time < '13:30' < reservation.end_time:
                    if r1300_1330.count(reservation) == 0:
                        r1300_1330.append(reservation)
                if '13:30' <= reservation.start_time < '14:00':
                    r1330_1400.append(reservation)
                if '13:30' < reservation.end_time <= '14:00' or reservation.start_time < '14:00' < reservation.end_time:
                    if r1330_1400.count(reservation) == 0:
                        r1330_1400.append(reservation)
                if '14:00' <= reservation.start_time < '14:30':
                    r1400_1430.append(reservation)
                if '14:00' < reservation.end_time <= '14:30' or reservation.start_time < '14:30' < reservation.end_time:
                    if r1400_1430.count(reservation) == 0:
                        r1400_1430.append(reservation)

                if '14:30' <= reservation.start_time < '15:00':
                    r1430_1500.append(reservation)
                if '14:30' < reservation.end_time <= '15:00' or reservation.start_time < '15:00' < reservation.end_time:
                    if r1430_1500.count(reservation) == 0:
                        r1430_1500.append(reservation)
                if '15:00' <= reservation.start_time < '15:30':
                    r1500_1530.append(reservation)
                if '15:00' < reservation.end_time <= '15:30' or reservation.start_time < '15:30' < reservation.end_time:
                    if r1500_1530.count(reservation) == 0:
                        r1500_1530.append(reservation)
                if '15:30' <= reservation.start_time < '16:00':
                    r1530_1600.append(reservation)
                if '15:30' < reservation.end_time <= '16:00' or reservation.start_time < '16:00' < reservation.end_time:
                    if r1530_1600.count(reservation) == 0:
                        r1530_1600.append(reservation)
                if '16:00' <= reservation.start_time < '16:30':
                    r1600_1630.append(reservation)
                if '16:00' < reservation.end_time <= '16:30' or reservation.start_time < '16:30' < reservation.end_time:
                    if r1600_1630.count(reservation) == 0:
                        r1600_1630.append(reservation)
                if '16:30' <= reservation.start_time < '17:00':
                    r1630_1700.append(reservation)
                if '16:30' < reservation.end_time <= '17:00' or reservation.start_time < '17:00' < reservation.end_time:
                    if r1630_1700.count(reservation) == 0:
                        r1630_1700.append(reservation)
                if '17:00' <= reservation.start_time < '17:30':
                    r1700_1730.append(reservation)
                if '17:00' < reservation.end_time <= '17:30' or reservation.start_time < '17:30' < reservation.end_time:
                    if r1700_1730.count(reservation) == 0:
                        r1700_1730.append(reservation)
                if '17:30' <= reservation.start_time < '18:00':
                    r1730_1800.append(reservation)
                if '17:30' < reservation.end_time <= '18:00' or reservation.start_time < '18:00' < reservation.end_time:
                    if r1730_1800.count(reservation) == 0:
                        r1730_1800.append(reservation)
                if '18:00' <= reservation.start_time < '18:30':
                    r1800_1830.append(reservation)
                if '18:00' < reservation.end_time <= '18:30' or reservation.start_time < '18:30' < reservation.end_time:
                    if r1800_1830.count(reservation) == 0:
                        r1800_1830.append(reservation)

                if '18:30' <= reservation.start_time < '19:00':
                    r1830_1900.append(reservation)
                if '18:30' < reservation.end_time <= '19:00' or reservation.start_time < '19:00' < reservation.end_time:
                    if r1830_1900.count(reservation) == 0:
                        r1830_1900.append(reservation)
                if '19:00' <= reservation.start_time < '19:30':
                    r1900_1930.append(reservation)
                if '19:00' < reservation.end_time <= '19:30' or reservation.start_time < '19:30' < reservation.end_time:
                    if r1900_1930.count(reservation) == 0:
                        r1900_1930.append(reservation)
                if '19:30' <= reservation.start_time < '20:00':
                    r1930_2000.append(reservation)
                if '19:30' < reservation.end_time <= '20:00' or reservation.start_time < '20:00' < reservation.end_time:
                    if r1930_2000.count(reservation) == 0:
                        r1930_2000.append(reservation)
                if '20:00' <= reservation.start_time < '20:30':
                    r2000_2030.append(reservation)
                if '20:00' < reservation.end_time <= '20:30' or reservation.start_time < '20:30' < reservation.end_time:
                    if r2000_2030.count(reservation) == 0:
                        r2000_2030.append(reservation)
                if '20:30' <= reservation.start_time < '21:00':
                    r2030_2100.append(reservation)
                if '20:30' < reservation.end_time <= '21:00' or reservation.start_time < '21:00' < reservation.end_time:
                    if r2030_2100.count(reservation) == 0:
                        r2030_2100.append(reservation)
                if '21:00' <= reservation.start_time < '21:30':
                    r2100_2130.append(reservation)
                if '21:00' < reservation.end_time <= '21:30' or reservation.start_time < '21:30' < reservation.end_time:
                    if r2100_2130.count(reservation) == 0:
                        r2100_2130.append(reservation)
                if '21:30' <= reservation.start_time < '22:00':
                    r2130_2200.append(reservation)
                if '21:30' < reservation.end_time <= '22:00' or reservation.start_time < '22:00' < reservation.end_time:
                    if r2130_2200.count(reservation) == 0:
                        r2130_2200.append(reservation)
                if '22:00' <= reservation.start_time < '22:30':
                    r2200_2230.append(reservation)
                if '22:00' < reservation.end_time <= '22:30' or reservation.start_time < '22:30' < reservation.end_time:
                    if r2200_2230.count(reservation) == 0:
                        r2200_2230.append(reservation)
                if '22:30' <= reservation.start_time < '23:00':
                    r2230_2300.append(reservation)
                if '22:30' < reservation.end_time <= '23:00' or reservation.start_time < '23:00' < reservation.end_time:
                    if r2230_2300.count(reservation) == 0:
                        r2230_2300.append(reservation)
                if '23:00' <= reservation.start_time < '23:30':
                    r2300_2330.append(reservation)
                if '23:00' < reservation.end_time <= '23:30' or reservation.start_time < '23:30' < reservation.end_time:
                    if r2300_2330.count(reservation) == 0:
                        r2300_2330.append(reservation)
                if '23:30' <= reservation.start_time < '00:00':
                    r2330_0000.append(reservation)
                if '23:30' < reservation.end_time <= '00:00' or reservation.start_time < '00:00' < reservation.end_time:
                    if r2330_0000.count(reservation) == 0:
                        r2330_0000.append(reservation)

            dict_r0000_0030['key2'] = r0000_0030
            dict_r0030_0100['key2'] = r0030_0100
            dict_r0100_0130['key2'] = r0100_0130
            dict_r0130_0200['key2'] = r0130_0200
            dict_r0200_0230['key2'] = r0200_0230
            dict_r0230_0300['key2'] = r0230_0300
            dict_r0300_0330['key2'] = r0300_0330
            dict_r0330_0400['key2'] = r0330_0400
            dict_r0400_0430['key2'] = r0400_0430
            dict_r0430_0500['key2'] = r0430_0500
            dict_r0500_0530['key2'] = r0500_0530
            dict_r0530_0600['key2'] = r0530_0600
            dict_r0600_0630['key2'] = r0600_0630
            dict_r0630_0700['key2'] = r0630_0700
            dict_r0700_0730['key2'] = r0700_0730
            dict_r0730_0800['key2'] = r0730_0800
            dict_r0800_0830['key2'] = r0800_0830
            dict_r0830_0900['key2'] = r0830_0900
            dict_r0900_0930['key2'] = r0900_0930
            dict_r0930_1000['key2'] = r0930_1000
            dict_r1000_1030['key2'] = r1000_1030
            dict_r1030_1100['key2'] = r1030_1100
            dict_r1100_1130['key2'] = r1100_1130
            dict_r1130_1200['key2'] = r1130_1200
            dict_r1200_1230['key2'] = r1200_1230
            dict_r1230_1300['key2'] = r1230_1300
            dict_r1300_1330['key2'] = r1300_1330
            dict_r1330_1400['key2'] = r1330_1400
            dict_r1400_1430['key2'] = r1400_1430
            dict_r1430_1500['key2'] = r1430_1500
            dict_r1500_1530['key2'] = r1500_1530
            dict_r1530_1600['key2'] = r1530_1600
            dict_r1600_1630['key2'] = r1600_1630
            dict_r1630_1700['key2'] = r1630_1700
            dict_r1700_1730['key2'] = r1700_1730
            dict_r1730_1800['key2'] = r1730_1800
            dict_r1800_1830['key2'] = r1800_1830
            dict_r1830_1900['key2'] = r1830_1900
            dict_r1900_1930['key2'] = r1900_1930
            dict_r1930_2000['key2'] = r1930_2000
            dict_r2000_2030['key2'] = r2000_2030
            dict_r2030_2100['key2'] = r2030_2100
            dict_r2100_2130['key2'] = r2100_2130
            dict_r2130_2200['key2'] = r2130_2200
            dict_r2200_2230['key2'] = r2200_2230
            dict_r2230_2300['key2'] = r2230_2300
            dict_r2300_2330['key2'] = r2300_2330
            dict_r2330_0000['key2'] = r2330_0000

            dict_r0000_0030['key3'] = len(r0000_0030)
            dict_r0030_0100['key3'] = len(r0030_0100)
            dict_r0100_0130['key3'] = len(r0100_0130)
            dict_r0130_0200['key3'] = len(r0130_0200)
            dict_r0200_0230['key3'] = len(r0200_0230)
            dict_r0230_0300['key3'] = len(r0230_0300)
            dict_r0300_0330['key3'] = len(r0300_0330)
            dict_r0330_0400['key3'] = len(r0330_0400)
            dict_r0400_0430['key3'] = len(r0400_0430)
            dict_r0430_0500['key3'] = len(r0430_0500)
            dict_r0500_0530['key3'] = len(r0500_0530)
            dict_r0530_0600['key3'] = len(r0530_0600)
            dict_r0600_0630['key3'] = len(r0600_0630)
            dict_r0630_0700['key3'] = len(r0630_0700)
            dict_r0700_0730['key3'] = len(r0700_0730)
            dict_r0730_0800['key3'] = len(r0730_0800)
            dict_r0800_0830['key3'] = len(r0800_0830)
            dict_r0830_0900['key3'] = len(r0830_0900)
            dict_r0900_0930['key3'] = len(r0900_0930)
            dict_r0930_1000['key3'] = len(r0930_1000)
            dict_r1000_1030['key3'] = len(r1000_1030)
            dict_r1030_1100['key3'] = len(r1030_1100)
            dict_r1100_1130['key3'] = len(r1100_1130)
            dict_r1130_1200['key3'] = len(r1130_1200)
            dict_r1200_1230['key3'] = len(r1200_1230)
            dict_r1230_1300['key3'] = len(r1230_1300)
            dict_r1300_1330['key3'] = len(r1300_1330)
            dict_r1330_1400['key3'] = len(r1330_1400)
            dict_r1400_1430['key3'] = len(r1400_1430)
            dict_r1430_1500['key3'] = len(r1430_1500)
            dict_r1500_1530['key3'] = len(r1500_1530)
            dict_r1530_1600['key3'] = len(r1530_1600)
            dict_r1600_1630['key3'] = len(r1600_1630)
            dict_r1630_1700['key3'] = len(r1630_1700)
            dict_r1700_1730['key3'] = len(r1700_1730)
            dict_r1730_1800['key3'] = len(r1730_1800)
            dict_r1800_1830['key3'] = len(r1800_1830)
            dict_r1830_1900['key3'] = len(r1830_1900)
            dict_r1900_1930['key3'] = len(r1900_1930)
            dict_r1930_2000['key3'] = len(r1930_2000)
            dict_r2000_2030['key3'] = len(r2000_2030)
            dict_r2030_2100['key3'] = len(r2030_2100)
            dict_r2100_2130['key3'] = len(r2100_2130)
            dict_r2130_2200['key3'] = len(r2130_2200)
            dict_r2200_2230['key3'] = len(r2200_2230)
            dict_r2230_2300['key3'] = len(r2230_2300)
            dict_r2300_2330['key3'] = len(r2300_2330)
            dict_r2330_0000['key3'] = len(r2330_0000)

            dict_r0000_0030['key4'] = '00:00 - 00:30'
            dict_r0030_0100['key4'] = '00:30 - 01:00'
            dict_r0100_0130['key4'] = '01:00 - 01:30'
            dict_r0130_0200['key4'] = '01:30 - 02:00'
            dict_r0200_0230['key4'] = '02:00 - 02:30'
            dict_r0230_0300['key4'] = '02:30 - 03:00'
            dict_r0300_0330['key4'] = '03:00 - 03:30'
            dict_r0330_0400['key4'] = '03:30 - 04:00'
            dict_r0400_0430['key4'] = '04:00 - 04:30'
            dict_r0430_0500['key4'] = '04:30 - 05:00'
            dict_r0500_0530['key4'] = '05:00 - 05:30'
            dict_r0530_0600['key4'] = '05:30 - 06:00'
            dict_r0600_0630['key4'] = '06:00 - 06:30'
            dict_r0630_0700['key4'] = '06:30 - 07:00'
            dict_r0700_0730['key4'] = '07:00 - 07:30'
            dict_r0730_0800['key4'] = '07:30 - 08:00'
            dict_r0800_0830['key4'] = '08:00 - 08:30'
            dict_r0830_0900['key4'] = '08:30 - 09:00'
            dict_r0900_0930['key4'] = '09:00 - 09:30'
            dict_r0930_1000['key4'] = '09:30 - 10:00'
            dict_r1000_1030['key4'] = '10:00 - 10:30'
            dict_r1030_1100['key4'] = '10:30 - 11:00'
            dict_r1100_1130['key4'] = '11:00 - 11:30'
            dict_r1130_1200['key4'] = '11:30 - 12:00'
            dict_r1200_1230['key4'] = '12:00 - 12:30'
            dict_r1230_1300['key4'] = '12:30 - 13:00'
            dict_r1300_1330['key4'] = '13:00 - 13:30'
            dict_r1330_1400['key4'] = '13:30 - 14:00'
            dict_r1400_1430['key4'] = '14:00 - 14:30'
            dict_r1430_1500['key4'] = '14:30 - 15:00'
            dict_r1500_1530['key4'] = '15:00 - 15:30'
            dict_r1530_1600['key4'] = '15:30 - 16:00'
            dict_r1600_1630['key4'] = '16:00 - 16:30'
            dict_r1630_1700['key4'] = '16:30 - 17:00'
            dict_r1700_1730['key4'] = '17:00 - 17:30'
            dict_r1730_1800['key4'] = '17:30 - 18:00'
            dict_r1800_1830['key4'] = '18:00 - 18:30'
            dict_r1830_1900['key4'] = '18:30 - 19:00'
            dict_r1900_1930['key4'] = '19:00 - 19:30'
            dict_r1930_2000['key4'] = '19:30 - 20:00'
            dict_r2000_2030['key4'] = '20:00 - 20:30'
            dict_r2030_2100['key4'] = '20:30 - 21:00'
            dict_r2100_2130['key4'] = '21:00 - 21:30'
            dict_r2130_2200['key4'] = '21:30 - 22:00'
            dict_r2200_2230['key4'] = '22:00 - 22:30'
            dict_r2230_2300['key4'] = '22:30 - 23:00'
            dict_r2300_2330['key4'] = '23:00 - 23:30'
            dict_r2330_0000['key4'] = '23:30 - 00:00'

            all_reservations.append(dict_r0000_0030)
            all_reservations.append(dict_r0030_0100)
            all_reservations.append(dict_r0100_0130)
            all_reservations.append(dict_r0130_0200)
            all_reservations.append(dict_r0200_0230)
            all_reservations.append(dict_r0230_0300)
            all_reservations.append(dict_r0300_0330)
            all_reservations.append(dict_r0330_0400)
            all_reservations.append(dict_r0400_0430)
            all_reservations.append(dict_r0430_0500)
            all_reservations.append(dict_r0500_0530)
            all_reservations.append(dict_r0530_0600)
            all_reservations.append(dict_r0600_0630)
            all_reservations.append(dict_r0630_0700)
            all_reservations.append(dict_r0700_0730)
            all_reservations.append(dict_r0730_0800)
            all_reservations.append(dict_r0800_0830)
            all_reservations.append(dict_r0830_0900)
            all_reservations.append(dict_r0900_0930)
            all_reservations.append(dict_r0930_1000)
            all_reservations.append(dict_r1000_1030)
            all_reservations.append(dict_r1030_1100)
            all_reservations.append(dict_r1100_1130)
            all_reservations.append(dict_r1130_1200)
            all_reservations.append(dict_r1200_1230)
            all_reservations.append(dict_r1230_1300)
            all_reservations.append(dict_r1300_1330)
            all_reservations.append(dict_r1330_1400)
            all_reservations.append(dict_r1400_1430)
            all_reservations.append(dict_r1430_1500)
            all_reservations.append(dict_r1500_1530)
            all_reservations.append(dict_r1530_1600)
            all_reservations.append(dict_r1600_1630)
            all_reservations.append(dict_r1630_1700)
            all_reservations.append(dict_r1700_1730)
            all_reservations.append(dict_r1730_1800)
            all_reservations.append(dict_r1800_1830)
            all_reservations.append(dict_r1830_1900)
            all_reservations.append(dict_r1900_1930)
            all_reservations.append(dict_r1930_2000)
            all_reservations.append(dict_r2000_2030)
            all_reservations.append(dict_r2030_2100)
            all_reservations.append(dict_r2100_2130)
            all_reservations.append(dict_r2130_2200)
            all_reservations.append(dict_r2200_2230)
            all_reservations.append(dict_r2230_2300)
            all_reservations.append(dict_r2300_2330)
            all_reservations.append(dict_r2330_0000)
            context['all_reservations'] = all_reservations

            for reservation in reservations_yesterday:
                if '00:00' <= reservation.start_time < '00:30':
                    r0000_0030_yesterday.append(reservation)
                if '00:00' < reservation.end_time <= '00:30' or reservation.start_time < '00:30' < reservation.end_time:
                    if r0000_0030_yesterday.count(reservation) == 0:
                        r0000_0030_yesterday.append(reservation)
                if '00:30' <= reservation.start_time < '01:00':
                    r0030_0100_yesterday.append(reservation)
                if '00:30' < reservation.end_time <= '01:00' or reservation.start_time < '01:00' < reservation.end_time:
                    if r0030_0100_yesterday.count(reservation) == 0:
                        r0030_0100_yesterday.append(reservation)
                if '01:00' <= reservation.start_time < '01:30':
                    r0100_0130_yesterday.append(reservation)
                if '01:00' < reservation.end_time <= '01:30' or reservation.start_time < '01:30' < reservation.end_time:
                    if r0100_0130_yesterday.count(reservation) == 0:
                        r0100_0130_yesterday.append(reservation)
                if '01:30' <= reservation.start_time < '02:00':
                    r0130_0200_yesterday.append(reservation)
                if '01:30' < reservation.end_time <= '02:00' or reservation.start_time < '02:00' < reservation.end_time:
                    if r0130_0200_yesterday.count(reservation) == 0:
                        r0130_0200_yesterday.append(reservation)
                if '02:00' <= reservation.start_time < '02:30':
                    r0200_0230_yesterday.append(reservation)
                if '02:00' < reservation.end_time <= '02:30' or reservation.start_time < '02:30' < reservation.end_time:
                    if r0200_0230_yesterday.count(reservation) == 0:
                        r0200_0230_yesterday.append(reservation)
                if '02:30' <= reservation.start_time < '03:00':
                    r0230_0300_yesterday.append(reservation)
                if '02:30' < reservation.end_time <= '03:00' or reservation.start_time < '03:00' < reservation.end_time:
                    if r0230_0300_yesterday.count(reservation) == 0:
                        r0230_0300_yesterday.append(reservation)
                if '03:00' <= reservation.start_time < '03:30':
                    r0300_0330_yesterday.append(reservation)
                if '03:00' < reservation.end_time <= '03:30' or reservation.start_time < '03:30' < reservation.end_time:
                    if r0300_0330_yesterday.count(reservation) == 0:
                        r0300_0330_yesterday.append(reservation)
                if '03:30' <= reservation.start_time < '04:00':
                    r0330_0400_yesterday.append(reservation)
                if '03:30' < reservation.end_time <= '04:00' or reservation.start_time < '04:00' < reservation.end_time:
                    if r0330_0400_yesterday.count(reservation) == 0:
                        r0330_0400_yesterday.append(reservation)
                if '04:00' <= reservation.start_time < '04:30':
                    r0400_0430_yesterday.append(reservation)
                if '04:00' < reservation.end_time <= '04:30' or reservation.start_time < '04:30' < reservation.end_time:
                    if r0400_0430_yesterday.count(reservation) == 0:
                        r0400_0430_yesterday.append(reservation)
                if '04:30' <= reservation.start_time < '05:00':
                    r0430_0500_yesterday.append(reservation)
                if '04:30' < reservation.end_time <= '05:00' or reservation.start_time < '05:00' < reservation.end_time:
                    if r0430_0500_yesterday.count(reservation) == 0:
                        r0430_0500_yesterday.append(reservation)
                if '05:00' <= reservation.start_time < '05:30':
                    r0500_0530_yesterday.append(reservation)
                if '05:00' < reservation.end_time <= '05:30' or reservation.start_time < '05:30' < reservation.end_time:
                    if r0500_0530_yesterday.count(reservation) == 0:
                        r0500_0530_yesterday.append(reservation)
                if '05:30' <= reservation.start_time < '06:00':
                    r0530_0600_yesterday.append(reservation)
                if '05:30' < reservation.end_time <= '06:00' or reservation.start_time < '06:00' < reservation.end_time:
                    if r0530_0600_yesterday.count(reservation) == 0:
                        r0530_0600_yesterday.append(reservation)
                if '06:00' <= reservation.start_time < '06:30':
                    r0600_0630_yesterday.append(reservation)
                if '06:00' < reservation.end_time <= '06:30' or reservation.start_time < '06:30' < reservation.end_time:
                    if r0600_0630_yesterday.count(reservation) == 0:
                        r0600_0630_yesterday.append(reservation)
                if '06:30' <= reservation.start_time < '07:00':
                    r0630_0700_yesterday.append(reservation)
                if '06:30' < reservation.end_time <= '07:00' or reservation.start_time < '07:00' < reservation.end_time:
                    if r0630_0700_yesterday.count(reservation) == 0:
                        r0630_0700_yesterday.append(reservation)
                if '07:00' <= reservation.start_time < '07:30':
                    r0700_0730_yesterday.append(reservation)
                if '07:00' < reservation.end_time <= '07:30' or reservation.start_time < '07:30' < reservation.end_time:
                    if r0700_0730_yesterday.count(reservation) == 0:
                        r0700_0730_yesterday.append(reservation)

                if '07:30' <= reservation.start_time < '08:00':
                    r0730_0800_yesterday.append(reservation)
                if '07:30' < reservation.end_time <= '08:00' or reservation.start_time < '08:00' < reservation.end_time:
                    if r0730_0800_yesterday.count(reservation) == 0:
                        r0730_0800_yesterday.append(reservation)
                if '08:00' <= reservation.start_time < '08:30':
                    r0800_0830_yesterday.append(reservation)
                if '08:00' < reservation.end_time <= '08:30' or reservation.start_time < '08:30' < reservation.end_time:
                    if r0800_0830_yesterday.count(reservation) == 0:
                        r0800_0830_yesterday.append(reservation)
                if '08:30' <= reservation.start_time < '09:00':
                    r0830_0900_yesterday.append(reservation)
                if '08:30' < reservation.end_time <= '09:00' or reservation.start_time < '09:00' < reservation.end_time:
                    if r0830_0900_yesterday.count(reservation) == 0:
                        r0830_0900_yesterday.append(reservation)
                if '09:00' <= reservation.start_time < '09:30':
                    r0900_0930_yesterday.append(reservation)
                if '09:00' < reservation.end_time <= '09:30' or reservation.start_time < '09:30' < reservation.end_time:
                    if r0900_0930_yesterday.count(reservation) == 0:
                        r0900_0930_yesterday.append(reservation)
                if '09:30' <= reservation.start_time < '10:00':
                    r0930_1000_yesterday.append(reservation)
                if '09:30' < reservation.end_time <= '10:00' or reservation.start_time < '10:00' < reservation.end_time:
                    if r0930_1000_yesterday.count(reservation) == 0:
                        r0930_1000_yesterday.append(reservation)
                if '10:00' <= reservation.start_time < '10:30':
                    r1000_1030_yesterday.append(reservation)
                if '10:00' < reservation.end_time <= '10:30' or reservation.start_time < '10:30' < reservation.end_time:
                    if r1000_1030_yesterday.count(reservation) == 0:
                        r1000_1030_yesterday.append(reservation)
                if '10:30' <= reservation.start_time < '11:00':
                    r1030_1100_yesterday.append(reservation)
                if '10:30' < reservation.end_time <= '11:00' or reservation.start_time < '11:00' < reservation.end_time:
                    if r1030_1100_yesterday.count(reservation) == 0:
                        r1030_1100_yesterday.append(reservation)

                if '11:00' <= reservation.start_time < '11:30':
                    r1100_1130_yesterday.append(reservation)
                if '11:00' < reservation.end_time <= '11:30' or reservation.start_time < '11:30' < reservation.end_time:
                    if r1100_1130_yesterday.count(reservation) == 0:
                        r1100_1130_yesterday.append(reservation)
                if '11:30' <= reservation.start_time < '12:00':
                    r1130_1200_yesterday.append(reservation)
                if '11:30' < reservation.end_time <= '12:00' or reservation.start_time < '12:00' < reservation.end_time:
                    if r1130_1200_yesterday.count(reservation) == 0:
                        r1130_1200_yesterday.append(reservation)
                if '12:00' <= reservation.start_time < '12:30':
                    r1200_1230_yesterday.append(reservation)
                if '12:00' < reservation.end_time <= '12:30' or reservation.start_time < '12:30' < reservation.end_time:
                    if r1200_1230_yesterday.count(reservation) == 0:
                        r1200_1230_yesterday.append(reservation)
                if '12:30' <= reservation.start_time < '13:00':
                    r1230_1300_yesterday.append(reservation)
                if '12:30' < reservation.end_time <= '13:00' or reservation.start_time < '13:00' < reservation.end_time:
                    if r1230_1300_yesterday.count(reservation) == 0:
                        r1230_1300_yesterday.append(reservation)
                if '13:00' <= reservation.start_time < '13:30':
                    r1300_1330_yesterday.append(reservation)
                if '13:00' < reservation.end_time <= '13:30' or reservation.start_time < '13:30' < reservation.end_time:
                    if r1300_1330_yesterday.count(reservation) == 0:
                        r1300_1330_yesterday.append(reservation)
                if '13:30' <= reservation.start_time < '14:00':
                    r1330_1400_yesterday.append(reservation)
                if '13:30' < reservation.end_time <= '14:00' or reservation.start_time < '14:00' < reservation.end_time:
                    if r1330_1400_yesterday.count(reservation) == 0:
                        r1330_1400_yesterday.append(reservation)
                if '14:00' <= reservation.start_time < '14:30':
                    r1400_1430_yesterday.append(reservation)
                if '14:00' < reservation.end_time <= '14:30' or reservation.start_time < '14:30' < reservation.end_time:
                    if r1400_1430_yesterday.count(reservation) == 0:
                        r1400_1430_yesterday.append(reservation)

                if '14:30' <= reservation.start_time < '15:00':
                    r1430_1500_yesterday.append(reservation)
                if '14:30' < reservation.end_time <= '15:00' or reservation.start_time < '15:00' < reservation.end_time:
                    if r1430_1500_yesterday.count(reservation) == 0:
                        r1430_1500_yesterday.append(reservation)
                if '15:00' <= reservation.start_time < '15:30':
                    r1500_1530_yesterday.append(reservation)
                if '15:00' < reservation.end_time <= '15:30' or reservation.start_time < '15:30' < reservation.end_time:
                    if r1500_1530_yesterday.count(reservation) == 0:
                        r1500_1530_yesterday.append(reservation)
                if '15:30' <= reservation.start_time < '16:00':
                    r1530_1600_yesterday.append(reservation)
                if '15:30' < reservation.end_time <= '16:00' or reservation.start_time < '16:00' < reservation.end_time:
                    if r1530_1600_yesterday.count(reservation) == 0:
                        r1530_1600_yesterday.append(reservation)
                if '16:00' <= reservation.start_time < '16:30':
                    r1600_1630_yesterday.append(reservation)
                if '16:00' < reservation.end_time <= '16:30' or reservation.start_time < '16:30' < reservation.end_time:
                    if r1600_1630_yesterday.count(reservation) == 0:
                        r1600_1630_yesterday.append(reservation)
                if '16:30' <= reservation.start_time < '17:00':
                    r1630_1700_yesterday.append(reservation)
                if '16:30' < reservation.end_time <= '17:00' or reservation.start_time < '17:00' < reservation.end_time:
                    if r1630_1700_yesterday.count(reservation) == 0:
                        r1630_1700_yesterday.append(reservation)
                if '17:00' <= reservation.start_time < '17:30':
                    r1700_1730_yesterday.append(reservation)
                if '17:00' < reservation.end_time <= '17:30' or reservation.start_time < '17:30' < reservation.end_time:
                    if r1700_1730_yesterday.count(reservation) == 0:
                        r1700_1730_yesterday.append(reservation)
                if '17:30' <= reservation.start_time < '18:00':
                    r1730_1800_yesterday.append(reservation)
                if '17:30' < reservation.end_time <= '18:00' or reservation.start_time < '18:00' < reservation.end_time:
                    if r1730_1800_yesterday.count(reservation) == 0:
                        r1730_1800_yesterday.append(reservation)
                if '18:00' <= reservation.start_time < '18:30':
                    r1800_1830_yesterday.append(reservation)
                if '18:00' < reservation.end_time <= '18:30' or reservation.start_time < '18:30' < reservation.end_time:
                    if r1800_1830_yesterday.count(reservation) == 0:
                        r1800_1830_yesterday.append(reservation)

                if '18:30' <= reservation.start_time < '19:00':
                    r1830_1900_yesterday.append(reservation)
                if '18:30' < reservation.end_time <= '19:00' or reservation.start_time < '19:00' < reservation.end_time:
                    if r1830_1900_yesterday.count(reservation) == 0:
                        r1830_1900_yesterday.append(reservation)
                if '19:00' <= reservation.start_time < '19:30':
                    r1900_1930_yesterday.append(reservation)
                if '19:00' < reservation.end_time <= '19:30' or reservation.start_time < '19:30' < reservation.end_time:
                    if r1900_1930_yesterday.count(reservation) == 0:
                        r1900_1930_yesterday.append(reservation)
                if '19:30' <= reservation.start_time < '20:00':
                    r1930_2000_yesterday.append(reservation)
                if '19:30' < reservation.end_time <= '20:00' or reservation.start_time < '20:00' < reservation.end_time:
                    if r1930_2000_yesterday.count(reservation) == 0:
                        r1930_2000_yesterday.append(reservation)
                if '20:00' <= reservation.start_time < '20:30':
                    r2000_2030_yesterday.append(reservation)
                if '20:00' < reservation.end_time <= '20:30' or reservation.start_time < '20:30' < reservation.end_time:
                    if r2000_2030_yesterday.count(reservation) == 0:
                        r2000_2030_yesterday.append(reservation)
                if '20:30' <= reservation.start_time < '21:00':
                    r2030_2100_yesterday.append(reservation)
                if '20:30' < reservation.end_time <= '21:00' or reservation.start_time < '21:00' < reservation.end_time:
                    if r2030_2100_yesterday.count(reservation) == 0:
                        r2030_2100_yesterday.append(reservation)
                if '21:00' <= reservation.start_time < '21:30':
                    r2100_2130_yesterday.append(reservation)
                if '21:00' < reservation.end_time <= '21:30' or reservation.start_time < '21:30' < reservation.end_time:
                    if r2100_2130_yesterday.count(reservation) == 0:
                        r2100_2130_yesterday.append(reservation)
                if '21:30' <= reservation.start_time < '22:00':
                    r2130_2200_yesterday.append(reservation)
                if '21:30' < reservation.end_time <= '22:00' or reservation.start_time < '22:00' < reservation.end_time:
                    if r2130_2200_yesterday.count(reservation) == 0:
                        r2130_2200_yesterday.append(reservation)
                if '22:00' <= reservation.start_time < '22:30':
                    r2200_2230_yesterday.append(reservation)
                if '22:00' < reservation.end_time <= '22:30' or reservation.start_time < '22:30' < reservation.end_time:
                    if r2200_2230_yesterday.count(reservation) == 0:
                        r2200_2230_yesterday.append(reservation)
                if '22:30' <= reservation.start_time < '23:00':
                    r2230_2300_yesterday.append(reservation)
                if '22:30' < reservation.end_time <= '23:00' or reservation.start_time < '23:00' < reservation.end_time:
                    if r2230_2300_yesterday.count(reservation) == 0:
                        r2230_2300_yesterday.append(reservation)
                if '23:00' <= reservation.start_time < '23:30':
                    r2300_2330_yesterday.append(reservation)
                if '23:00' < reservation.end_time <= '23:30' or reservation.start_time < '23:30' < reservation.end_time:
                    if r2300_2330_yesterday.count(reservation) == 0:
                        r2300_2330_yesterday.append(reservation)
                if '23:30' <= reservation.start_time < '00:00':
                    r2330_0000_yesterday.append(reservation)
                if '23:30' < reservation.end_time <= '00:00' or reservation.start_time < '00:00' < reservation.end_time:
                    if r2330_0000_yesterday.count(reservation) == 0:
                        r2330_0000_yesterday.append(reservation)

            dict_r0000_0030_yesterday['key2'] = r0000_0030_yesterday
            dict_r0030_0100_yesterday['key2'] = r0030_0100_yesterday
            dict_r0100_0130_yesterday['key2'] = r0100_0130_yesterday
            dict_r0130_0200_yesterday['key2'] = r0130_0200_yesterday
            dict_r0200_0230_yesterday['key2'] = r0200_0230_yesterday
            dict_r0230_0300_yesterday['key2'] = r0230_0300_yesterday
            dict_r0300_0330_yesterday['key2'] = r0300_0330_yesterday
            dict_r0330_0400_yesterday['key2'] = r0330_0400_yesterday
            dict_r0400_0430_yesterday['key2'] = r0400_0430_yesterday
            dict_r0430_0500_yesterday['key2'] = r0430_0500_yesterday
            dict_r0500_0530_yesterday['key2'] = r0500_0530_yesterday
            dict_r0530_0600_yesterday['key2'] = r0530_0600_yesterday
            dict_r0600_0630_yesterday['key2'] = r0600_0630_yesterday
            dict_r0630_0700_yesterday['key2'] = r0630_0700_yesterday
            dict_r0700_0730_yesterday['key2'] = r0700_0730_yesterday
            dict_r0730_0800_yesterday['key2'] = r0730_0800_yesterday
            dict_r0800_0830_yesterday['key2'] = r0800_0830_yesterday
            dict_r0830_0900_yesterday['key2'] = r0830_0900_yesterday
            dict_r0900_0930_yesterday['key2'] = r0900_0930_yesterday
            dict_r0930_1000_yesterday['key2'] = r0930_1000_yesterday
            dict_r1000_1030_yesterday['key2'] = r1000_1030_yesterday
            dict_r1030_1100_yesterday['key2'] = r1030_1100_yesterday
            dict_r1100_1130_yesterday['key2'] = r1100_1130_yesterday
            dict_r1130_1200_yesterday['key2'] = r1130_1200_yesterday
            dict_r1200_1230_yesterday['key2'] = r1200_1230_yesterday
            dict_r1230_1300_yesterday['key2'] = r1230_1300_yesterday
            dict_r1300_1330_yesterday['key2'] = r1300_1330_yesterday
            dict_r1330_1400_yesterday['key2'] = r1330_1400_yesterday
            dict_r1400_1430_yesterday['key2'] = r1400_1430_yesterday
            dict_r1430_1500_yesterday['key2'] = r1430_1500_yesterday
            dict_r1500_1530_yesterday['key2'] = r1500_1530_yesterday
            dict_r1530_1600_yesterday['key2'] = r1530_1600_yesterday
            dict_r1600_1630_yesterday['key2'] = r1600_1630_yesterday
            dict_r1630_1700_yesterday['key2'] = r1630_1700_yesterday
            dict_r1700_1730_yesterday['key2'] = r1700_1730_yesterday
            dict_r1730_1800_yesterday['key2'] = r1730_1800_yesterday
            dict_r1800_1830_yesterday['key2'] = r1800_1830_yesterday
            dict_r1830_1900_yesterday['key2'] = r1830_1900_yesterday
            dict_r1900_1930_yesterday['key2'] = r1900_1930_yesterday
            dict_r1930_2000_yesterday['key2'] = r1930_2000_yesterday
            dict_r2000_2030_yesterday['key2'] = r2000_2030_yesterday
            dict_r2030_2100_yesterday['key2'] = r2030_2100_yesterday
            dict_r2100_2130_yesterday['key2'] = r2100_2130_yesterday
            dict_r2130_2200_yesterday['key2'] = r2130_2200_yesterday
            dict_r2200_2230_yesterday['key2'] = r2200_2230_yesterday
            dict_r2230_2300_yesterday['key2'] = r2230_2300_yesterday
            dict_r2300_2330_yesterday['key2'] = r2300_2330_yesterday
            dict_r2330_0000_yesterday['key2'] = r2330_0000_yesterday

            dict_r0000_0030_yesterday['key3'] = len(r0000_0030_yesterday)
            dict_r0030_0100_yesterday['key3'] = len(r0030_0100_yesterday)
            dict_r0100_0130_yesterday['key3'] = len(r0100_0130_yesterday)
            dict_r0130_0200_yesterday['key3'] = len(r0130_0200_yesterday)
            dict_r0200_0230_yesterday['key3'] = len(r0200_0230_yesterday)
            dict_r0230_0300_yesterday['key3'] = len(r0230_0300_yesterday)
            dict_r0300_0330_yesterday['key3'] = len(r0300_0330_yesterday)
            dict_r0330_0400_yesterday['key3'] = len(r0330_0400_yesterday)
            dict_r0400_0430_yesterday['key3'] = len(r0400_0430_yesterday)
            dict_r0430_0500_yesterday['key3'] = len(r0430_0500_yesterday)
            dict_r0500_0530_yesterday['key3'] = len(r0500_0530_yesterday)
            dict_r0530_0600_yesterday['key3'] = len(r0530_0600_yesterday)
            dict_r0600_0630_yesterday['key3'] = len(r0600_0630_yesterday)
            dict_r0630_0700_yesterday['key3'] = len(r0630_0700_yesterday)
            dict_r0700_0730_yesterday['key3'] = len(r0700_0730_yesterday)
            dict_r0730_0800_yesterday['key3'] = len(r0730_0800_yesterday)
            dict_r0800_0830_yesterday['key3'] = len(r0800_0830_yesterday)
            dict_r0830_0900_yesterday['key3'] = len(r0830_0900_yesterday)
            dict_r0900_0930_yesterday['key3'] = len(r0900_0930_yesterday)
            dict_r0930_1000_yesterday['key3'] = len(r0930_1000_yesterday)
            dict_r1000_1030_yesterday['key3'] = len(r1000_1030_yesterday)
            dict_r1030_1100_yesterday['key3'] = len(r1030_1100_yesterday)
            dict_r1100_1130_yesterday['key3'] = len(r1100_1130_yesterday)
            dict_r1130_1200_yesterday['key3'] = len(r1130_1200_yesterday)
            dict_r1200_1230_yesterday['key3'] = len(r1200_1230_yesterday)
            dict_r1230_1300_yesterday['key3'] = len(r1230_1300_yesterday)
            dict_r1300_1330_yesterday['key3'] = len(r1300_1330_yesterday)
            dict_r1330_1400_yesterday['key3'] = len(r1330_1400_yesterday)
            dict_r1400_1430_yesterday['key3'] = len(r1400_1430_yesterday)
            dict_r1430_1500_yesterday['key3'] = len(r1430_1500_yesterday)
            dict_r1500_1530_yesterday['key3'] = len(r1500_1530_yesterday)
            dict_r1530_1600_yesterday['key3'] = len(r1530_1600_yesterday)
            dict_r1600_1630_yesterday['key3'] = len(r1600_1630_yesterday)
            dict_r1630_1700_yesterday['key3'] = len(r1630_1700_yesterday)
            dict_r1700_1730_yesterday['key3'] = len(r1700_1730_yesterday)
            dict_r1730_1800_yesterday['key3'] = len(r1730_1800_yesterday)
            dict_r1800_1830_yesterday['key3'] = len(r1800_1830_yesterday)
            dict_r1830_1900_yesterday['key3'] = len(r1830_1900_yesterday)
            dict_r1900_1930_yesterday['key3'] = len(r1900_1930_yesterday)
            dict_r1930_2000_yesterday['key3'] = len(r1930_2000_yesterday)
            dict_r2000_2030_yesterday['key3'] = len(r2000_2030_yesterday)
            dict_r2030_2100_yesterday['key3'] = len(r2030_2100_yesterday)
            dict_r2100_2130_yesterday['key3'] = len(r2100_2130_yesterday)
            dict_r2130_2200_yesterday['key3'] = len(r2130_2200_yesterday)
            dict_r2200_2230_yesterday['key3'] = len(r2200_2230_yesterday)
            dict_r2230_2300_yesterday['key3'] = len(r2230_2300_yesterday)
            dict_r2300_2330_yesterday['key3'] = len(r2300_2330_yesterday)
            dict_r2330_0000_yesterday['key3'] = len(r2330_0000_yesterday)

            dict_r0000_0030_yesterday['key4'] = '00:00 - 00:30'
            dict_r0030_0100_yesterday['key4'] = '00:30 - 01:00'
            dict_r0100_0130_yesterday['key4'] = '01:00 - 01:30'
            dict_r0130_0200_yesterday['key4'] = '01:30 - 02:00'
            dict_r0200_0230_yesterday['key4'] = '02:00 - 02:30'
            dict_r0230_0300_yesterday['key4'] = '02:30 - 03:00'
            dict_r0300_0330_yesterday['key4'] = '03:00 - 03:30'
            dict_r0330_0400_yesterday['key4'] = '03:30 - 04:00'
            dict_r0400_0430_yesterday['key4'] = '04:00 - 04:30'
            dict_r0430_0500_yesterday['key4'] = '04:30 - 05:00'
            dict_r0500_0530_yesterday['key4'] = '05:00 - 05:30'
            dict_r0530_0600_yesterday['key4'] = '05:30 - 06:00'
            dict_r0600_0630_yesterday['key4'] = '06:00 - 06:30'
            dict_r0630_0700_yesterday['key4'] = '06:30 - 07:00'
            dict_r0700_0730_yesterday['key4'] = '07:00 - 07:30'
            dict_r0730_0800_yesterday['key4'] = '07:30 - 08:00'
            dict_r0800_0830_yesterday['key4'] = '08:00 - 08:30'
            dict_r0830_0900_yesterday['key4'] = '08:30 - 09:00'
            dict_r0900_0930_yesterday['key4'] = '09:00 - 09:30'
            dict_r0930_1000_yesterday['key4'] = '09:30 - 10:00'
            dict_r1000_1030_yesterday['key4'] = '10:00 - 10:30'
            dict_r1030_1100_yesterday['key4'] = '10:30 - 11:00'
            dict_r1100_1130_yesterday['key4'] = '11:00 - 11:30'
            dict_r1130_1200_yesterday['key4'] = '11:30 - 12:00'
            dict_r1200_1230_yesterday['key4'] = '12:00 - 12:30'
            dict_r1230_1300_yesterday['key4'] = '12:30 - 13:00'
            dict_r1300_1330_yesterday['key4'] = '13:00 - 13:30'
            dict_r1330_1400_yesterday['key4'] = '13:30 - 14:00'
            dict_r1400_1430_yesterday['key4'] = '14:00 - 14:30'
            dict_r1430_1500_yesterday['key4'] = '14:30 - 15:00'
            dict_r1500_1530_yesterday['key4'] = '15:00 - 15:30'
            dict_r1530_1600_yesterday['key4'] = '15:30 - 16:00'
            dict_r1600_1630_yesterday['key4'] = '16:00 - 16:30'
            dict_r1630_1700_yesterday['key4'] = '16:30 - 17:00'
            dict_r1700_1730_yesterday['key4'] = '17:00 - 17:30'
            dict_r1730_1800_yesterday['key4'] = '17:30 - 18:00'
            dict_r1800_1830_yesterday['key4'] = '18:00 - 18:30'
            dict_r1830_1900_yesterday['key4'] = '18:30 - 19:00'
            dict_r1900_1930_yesterday['key4'] = '19:00 - 19:30'
            dict_r1930_2000_yesterday['key4'] = '19:30 - 20:00'
            dict_r2000_2030_yesterday['key4'] = '20:00 - 20:30'
            dict_r2030_2100_yesterday['key4'] = '20:30 - 21:00'
            dict_r2100_2130_yesterday['key4'] = '21:00 - 21:30'
            dict_r2130_2200_yesterday['key4'] = '21:30 - 22:00'
            dict_r2200_2230_yesterday['key4'] = '22:00 - 22:30'
            dict_r2230_2300_yesterday['key4'] = '22:30 - 23:00'
            dict_r2300_2330_yesterday['key4'] = '23:00 - 23:30'
            dict_r2330_0000_yesterday['key4'] = '23:30 - 00:00'

            all_reservations_yesterday.append(dict_r0000_0030_yesterday)
            all_reservations_yesterday.append(dict_r0030_0100_yesterday)
            all_reservations_yesterday.append(dict_r0100_0130_yesterday)
            all_reservations_yesterday.append(dict_r0130_0200_yesterday)
            all_reservations_yesterday.append(dict_r0200_0230_yesterday)
            all_reservations_yesterday.append(dict_r0230_0300_yesterday)
            all_reservations_yesterday.append(dict_r0300_0330_yesterday)
            all_reservations_yesterday.append(dict_r0330_0400_yesterday)
            all_reservations_yesterday.append(dict_r0400_0430_yesterday)
            all_reservations_yesterday.append(dict_r0430_0500_yesterday)
            all_reservations_yesterday.append(dict_r0500_0530_yesterday)
            all_reservations_yesterday.append(dict_r0530_0600_yesterday)
            all_reservations_yesterday.append(dict_r0600_0630_yesterday)
            all_reservations_yesterday.append(dict_r0630_0700_yesterday)
            all_reservations_yesterday.append(dict_r0700_0730_yesterday)
            all_reservations_yesterday.append(dict_r0730_0800_yesterday)
            all_reservations_yesterday.append(dict_r0800_0830_yesterday)
            all_reservations_yesterday.append(dict_r0830_0900_yesterday)
            all_reservations_yesterday.append(dict_r0900_0930_yesterday)
            all_reservations_yesterday.append(dict_r0930_1000_yesterday)
            all_reservations_yesterday.append(dict_r1000_1030_yesterday)
            all_reservations_yesterday.append(dict_r1030_1100_yesterday)
            all_reservations_yesterday.append(dict_r1100_1130_yesterday)
            all_reservations_yesterday.append(dict_r1130_1200_yesterday)
            all_reservations_yesterday.append(dict_r1200_1230_yesterday)
            all_reservations_yesterday.append(dict_r1230_1300_yesterday)
            all_reservations_yesterday.append(dict_r1300_1330_yesterday)
            all_reservations_yesterday.append(dict_r1330_1400_yesterday)
            all_reservations_yesterday.append(dict_r1400_1430_yesterday)
            all_reservations_yesterday.append(dict_r1430_1500_yesterday)
            all_reservations_yesterday.append(dict_r1500_1530_yesterday)
            all_reservations_yesterday.append(dict_r1530_1600_yesterday)
            all_reservations_yesterday.append(dict_r1600_1630_yesterday)
            all_reservations_yesterday.append(dict_r1630_1700_yesterday)
            all_reservations_yesterday.append(dict_r1700_1730_yesterday)
            all_reservations_yesterday.append(dict_r1730_1800_yesterday)
            all_reservations_yesterday.append(dict_r1800_1830_yesterday)
            all_reservations_yesterday.append(dict_r1830_1900_yesterday)
            all_reservations_yesterday.append(dict_r1900_1930_yesterday)
            all_reservations_yesterday.append(dict_r1930_2000_yesterday)
            all_reservations_yesterday.append(dict_r2000_2030_yesterday)
            all_reservations_yesterday.append(dict_r2030_2100_yesterday)
            all_reservations_yesterday.append(dict_r2100_2130_yesterday)
            all_reservations_yesterday.append(dict_r2130_2200_yesterday)
            all_reservations_yesterday.append(dict_r2200_2230_yesterday)
            all_reservations_yesterday.append(dict_r2230_2300_yesterday)
            all_reservations_yesterday.append(dict_r2300_2330_yesterday)
            all_reservations_yesterday.append(dict_r2330_0000_yesterday)
            context['all_reservations_yesterday'] = all_reservations_yesterday

            for reservation in reservations_tomorrow:
                if '00:00' <= reservation.start_time < '00:30':
                    r0000_0030_tomorrow.append(reservation)
                if '00:00' < reservation.end_time <= '00:30' or reservation.start_time < '00:30' < reservation.end_time:
                    if r0000_0030_tomorrow.count(reservation) == 0:
                        r0000_0030_tomorrow.append(reservation)
                if '00:30' <= reservation.start_time < '01:00':
                    r0030_0100_tomorrow.append(reservation)
                if '00:30' < reservation.end_time <= '01:00' or reservation.start_time < '01:00' < reservation.end_time:
                    if r0030_0100_tomorrow.count(reservation) == 0:
                        r0030_0100_tomorrow.append(reservation)
                if '01:00' <= reservation.start_time < '01:30':
                    r0100_0130_tomorrow.append(reservation)
                if '01:00' < reservation.end_time <= '01:30' or reservation.start_time < '01:30' < reservation.end_time:
                    if r0100_0130_tomorrow.count(reservation) == 0:
                        r0100_0130_tomorrow.append(reservation)
                if '01:30' <= reservation.start_time < '02:00':
                    r0130_0200_tomorrow.append(reservation)
                if '01:30' < reservation.end_time <= '02:00' or reservation.start_time < '02:00' < reservation.end_time:
                    if r0130_0200_tomorrow.count(reservation) == 0:
                        r0130_0200_tomorrow.append(reservation)
                if '02:00' <= reservation.start_time < '02:30':
                    r0200_0230_tomorrow.append(reservation)
                if '02:00' < reservation.end_time <= '02:30' or reservation.start_time < '02:30' < reservation.end_time:
                    if r0200_0230_tomorrow.count(reservation) == 0:
                        r0200_0230_tomorrow.append(reservation)
                if '02:30' <= reservation.start_time < '03:00':
                    r0230_0300_tomorrow.append(reservation)
                if '02:30' < reservation.end_time <= '03:00' or reservation.start_time < '03:00' < reservation.end_time:
                    if r0230_0300_tomorrow.count(reservation) == 0:
                        r0230_0300_tomorrow.append(reservation)
                if '03:00' <= reservation.start_time < '03:30':
                    r0300_0330_tomorrow.append(reservation)
                if '03:00' < reservation.end_time <= '03:30' or reservation.start_time < '03:30' < reservation.end_time:
                    if r0300_0330_tomorrow.count(reservation) == 0:
                        r0300_0330_tomorrow.append(reservation)
                if '03:30' <= reservation.start_time < '04:00':
                    r0330_0400_tomorrow.append(reservation)
                if '03:30' < reservation.end_time <= '04:00' or reservation.start_time < '04:00' < reservation.end_time:
                    if r0330_0400_tomorrow.count(reservation) == 0:
                        r0330_0400_tomorrow.append(reservation)
                if '04:00' <= reservation.start_time < '04:30':
                    r0400_0430_tomorrow.append(reservation)
                if '04:00' < reservation.end_time <= '04:30' or reservation.start_time < '04:30' < reservation.end_time:
                    if r0400_0430_tomorrow.count(reservation) == 0:
                        r0400_0430_tomorrow.append(reservation)
                if '04:30' <= reservation.start_time < '05:00':
                    r0430_0500_tomorrow.append(reservation)
                if '04:30' < reservation.end_time <= '05:00' or reservation.start_time < '05:00' < reservation.end_time:
                    if r0430_0500_tomorrow.count(reservation) == 0:
                        r0430_0500_tomorrow.append(reservation)
                if '05:00' <= reservation.start_time < '05:30':
                    r0500_0530_tomorrow.append(reservation)
                if '05:00' < reservation.end_time <= '05:30' or reservation.start_time < '05:30' < reservation.end_time:
                    if r0500_0530_tomorrow.count(reservation) == 0:
                        r0500_0530_tomorrow.append(reservation)
                if '05:30' <= reservation.start_time < '06:00':
                    r0530_0600_tomorrow.append(reservation)
                if '05:30' < reservation.end_time <= '06:00' or reservation.start_time < '06:00' < reservation.end_time:
                    if r0530_0600_tomorrow.count(reservation) == 0:
                        r0530_0600_tomorrow.append(reservation)
                if '06:00' <= reservation.start_time < '06:30':
                    r0600_0630_tomorrow.append(reservation)
                if '06:00' < reservation.end_time <= '06:30' or reservation.start_time < '06:30' < reservation.end_time:
                    if r0600_0630_tomorrow.count(reservation) == 0:
                        r0600_0630_tomorrow.append(reservation)
                if '06:30' <= reservation.start_time < '07:00':
                    r0630_0700_tomorrow.append(reservation)
                if '06:30' < reservation.end_time <= '07:00' or reservation.start_time < '07:00' < reservation.end_time:
                    if r0630_0700_tomorrow.count(reservation) == 0:
                        r0630_0700_tomorrow.append(reservation)
                if '07:00' <= reservation.start_time < '07:30':
                    r0700_0730_tomorrow.append(reservation)
                if '07:00' < reservation.end_time <= '07:30' or reservation.start_time < '07:30' < reservation.end_time:
                    if r0700_0730_tomorrow.count(reservation) == 0:
                        r0700_0730_tomorrow.append(reservation)

                if '07:30' <= reservation.start_time < '08:00':
                    r0730_0800_tomorrow.append(reservation)
                if '07:30' < reservation.end_time <= '08:00' or reservation.start_time < '08:00' < reservation.end_time:
                    if r0730_0800_tomorrow.count(reservation) == 0:
                        r0730_0800_tomorrow.append(reservation)
                if '08:00' <= reservation.start_time < '08:30':
                    r0800_0830_tomorrow.append(reservation)
                if '08:00' < reservation.end_time <= '08:30' or reservation.start_time < '08:30' < reservation.end_time:
                    if r0800_0830_tomorrow.count(reservation) == 0:
                        r0800_0830_tomorrow.append(reservation)
                if '08:30' <= reservation.start_time < '09:00':
                    r0830_0900_tomorrow.append(reservation)
                if '08:30' < reservation.end_time <= '09:00' or reservation.start_time < '09:00' < reservation.end_time:
                    if r0830_0900_tomorrow.count(reservation) == 0:
                        r0830_0900_tomorrow.append(reservation)
                if '09:00' <= reservation.start_time < '09:30':
                    r0900_0930_tomorrow.append(reservation)
                if '09:00' < reservation.end_time <= '09:30' or reservation.start_time < '09:30' < reservation.end_time:
                    if r0900_0930_tomorrow.count(reservation) == 0:
                        r0900_0930_tomorrow.append(reservation)
                if '09:30' <= reservation.start_time < '10:00':
                    r0930_1000_tomorrow.append(reservation)
                if '09:30' < reservation.end_time <= '10:00' or reservation.start_time < '10:00' < reservation.end_time:
                    if r0930_1000_tomorrow.count(reservation) == 0:
                        r0930_1000_tomorrow.append(reservation)
                if '10:00' <= reservation.start_time < '10:30':
                    r1000_1030_tomorrow.append(reservation)
                if '10:00' < reservation.end_time <= '10:30' or reservation.start_time < '10:30' < reservation.end_time:
                    if r1000_1030_tomorrow.count(reservation) == 0:
                        r1000_1030_tomorrow.append(reservation)
                if '10:30' <= reservation.start_time < '11:00':
                    r1030_1100_tomorrow.append(reservation)
                if '10:30' < reservation.end_time <= '11:00' or reservation.start_time < '11:00' < reservation.end_time:
                    if r1030_1100_tomorrow.count(reservation) == 0:
                        r1030_1100_tomorrow.append(reservation)

                if '11:00' <= reservation.start_time < '11:30':
                    r1100_1130_tomorrow.append(reservation)
                if '11:00' < reservation.end_time <= '11:30' or reservation.start_time < '11:30' < reservation.end_time:
                    if r1100_1130_tomorrow.count(reservation) == 0:
                        r1100_1130_tomorrow.append(reservation)
                if '11:30' <= reservation.start_time < '12:00':
                    r1130_1200_tomorrow.append(reservation)
                if '11:30' < reservation.end_time <= '12:00' or reservation.start_time < '12:00' < reservation.end_time:
                    if r1130_1200_tomorrow.count(reservation) == 0:
                        r1130_1200_tomorrow.append(reservation)
                if '12:00' <= reservation.start_time < '12:30':
                    r1200_1230_tomorrow.append(reservation)
                if '12:00' < reservation.end_time <= '12:30' or reservation.start_time < '12:30' < reservation.end_time:
                    if r1200_1230_tomorrow.count(reservation) == 0:
                        r1200_1230_tomorrow.append(reservation)
                if '12:30' <= reservation.start_time < '13:00':
                    r1230_1300_tomorrow.append(reservation)
                if '12:30' < reservation.end_time <= '13:00' or reservation.start_time < '13:00' < reservation.end_time:
                    if r1230_1300_tomorrow.count(reservation) == 0:
                        r1230_1300_tomorrow.append(reservation)
                if '13:00' <= reservation.start_time < '13:30':
                    r1300_1330_tomorrow.append(reservation)
                if '13:00' < reservation.end_time <= '13:30' or reservation.start_time < '13:30' < reservation.end_time:
                    if r1300_1330_tomorrow.count(reservation) == 0:
                        r1300_1330_tomorrow.append(reservation)
                if '13:30' <= reservation.start_time < '14:00':
                    r1330_1400_tomorrow.append(reservation)
                if '13:30' < reservation.end_time <= '14:00' or reservation.start_time < '14:00' < reservation.end_time:
                    if r1330_1400_tomorrow.count(reservation) == 0:
                        r1330_1400_tomorrow.append(reservation)
                if '14:00' <= reservation.start_time < '14:30':
                    r1400_1430_tomorrow.append(reservation)
                if '14:00' < reservation.end_time <= '14:30' or reservation.start_time < '14:30' < reservation.end_time:
                    if r1400_1430_tomorrow.count(reservation) == 0:
                        r1400_1430_tomorrow.append(reservation)

                if '14:30' <= reservation.start_time < '15:00':
                    r1430_1500_tomorrow.append(reservation)
                if '14:30' < reservation.end_time <= '15:00' or reservation.start_time < '15:00' < reservation.end_time:
                    if r1430_1500_tomorrow.count(reservation) == 0:
                        r1430_1500_tomorrow.append(reservation)
                if '15:00' <= reservation.start_time < '15:30':
                    r1500_1530_tomorrow.append(reservation)
                if '15:00' < reservation.end_time <= '15:30' or reservation.start_time < '15:30' < reservation.end_time:
                    if r1500_1530_tomorrow.count(reservation) == 0:
                        r1500_1530_tomorrow.append(reservation)
                if '15:30' <= reservation.start_time < '16:00':
                    r1530_1600_tomorrow.append(reservation)
                if '15:30' < reservation.end_time <= '16:00' or reservation.start_time < '16:00' < reservation.end_time:
                    if r1530_1600_tomorrow.count(reservation) == 0:
                        r1530_1600_tomorrow.append(reservation)
                if '16:00' <= reservation.start_time < '16:30':
                    r1600_1630_tomorrow.append(reservation)
                if '16:00' < reservation.end_time <= '16:30' or reservation.start_time < '16:30' < reservation.end_time:
                    if r1600_1630_tomorrow.count(reservation) == 0:
                        r1600_1630_tomorrow.append(reservation)
                if '16:30' <= reservation.start_time < '17:00':
                    r1630_1700_tomorrow.append(reservation)
                if '16:30' < reservation.end_time <= '17:00' or reservation.start_time < '17:00' < reservation.end_time:
                    if r1630_1700_tomorrow.count(reservation) == 0:
                        r1630_1700_tomorrow.append(reservation)
                if '17:00' <= reservation.start_time < '17:30':
                    r1700_1730_tomorrow.append(reservation)
                if '17:00' < reservation.end_time <= '17:30' or reservation.start_time < '17:30' < reservation.end_time:
                    if r1700_1730_tomorrow.count(reservation) == 0:
                        r1700_1730_tomorrow.append(reservation)
                if '17:30' <= reservation.start_time < '18:00':
                    r1730_1800_tomorrow.append(reservation)
                if '17:30' < reservation.end_time <= '18:00' or reservation.start_time < '18:00' < reservation.end_time:
                    if r1730_1800_tomorrow.count(reservation) == 0:
                        r1730_1800_tomorrow.append(reservation)
                if '18:00' <= reservation.start_time < '18:30':
                    r1800_1830_tomorrow.append(reservation)
                if '18:00' < reservation.end_time <= '18:30' or reservation.start_time < '18:30' < reservation.end_time:
                    if r1800_1830_tomorrow.count(reservation) == 0:
                        r1800_1830_tomorrow.append(reservation)

                if '18:30' <= reservation.start_time < '19:00':
                    r1830_1900_tomorrow.append(reservation)
                if '18:30' < reservation.end_time <= '19:00' or reservation.start_time < '19:00' < reservation.end_time:
                    if r1830_1900_tomorrow.count(reservation) == 0:
                        r1830_1900_tomorrow.append(reservation)
                if '19:00' <= reservation.start_time < '19:30':
                    r1900_1930_tomorrow.append(reservation)
                if '19:00' < reservation.end_time <= '19:30' or reservation.start_time < '19:30' < reservation.end_time:
                    if r1900_1930_tomorrow.count(reservation) == 0:
                        r1900_1930_tomorrow.append(reservation)
                if '19:30' <= reservation.start_time < '20:00':
                    r1930_2000_tomorrow.append(reservation)
                if '19:30' < reservation.end_time <= '20:00' or reservation.start_time < '20:00' < reservation.end_time:
                    if r1930_2000_tomorrow.count(reservation) == 0:
                        r1930_2000_tomorrow.append(reservation)
                if '20:00' <= reservation.start_time < '20:30':
                    r2000_2030_tomorrow.append(reservation)
                if '20:00' < reservation.end_time <= '20:30' or reservation.start_time < '20:30' < reservation.end_time:
                    if r2000_2030_tomorrow.count(reservation) == 0:
                        r2000_2030_tomorrow.append(reservation)
                if '20:30' <= reservation.start_time < '21:00':
                    r2030_2100_tomorrow.append(reservation)
                if '20:30' < reservation.end_time <= '21:00' or reservation.start_time < '21:00' < reservation.end_time:
                    if r2030_2100_tomorrow.count(reservation) == 0:
                        r2030_2100_tomorrow.append(reservation)
                if '21:00' <= reservation.start_time < '21:30':
                    r2100_2130_tomorrow.append(reservation)
                if '21:00' < reservation.end_time <= '21:30' or reservation.start_time < '21:30' < reservation.end_time:
                    if r2100_2130_tomorrow.count(reservation) == 0:
                        r2100_2130_tomorrow.append(reservation)
                if '21:30' <= reservation.start_time < '22:00':
                    r2130_2200_tomorrow.append(reservation)
                if '21:30' < reservation.end_time <= '22:00' or reservation.start_time < '22:00' < reservation.end_time:
                    if r2130_2200_tomorrow.count(reservation) == 0:
                        r2130_2200_tomorrow.append(reservation)
                if '22:00' <= reservation.start_time < '22:30':
                    r2200_2230_tomorrow.append(reservation)
                if '22:00' < reservation.end_time <= '22:30' or reservation.start_time < '22:30' < reservation.end_time:
                    if r2200_2230_tomorrow.count(reservation) == 0:
                        r2200_2230_tomorrow.append(reservation)
                if '22:30' <= reservation.start_time < '23:00':
                    r2230_2300_tomorrow.append(reservation)
                if '22:30' < reservation.end_time <= '23:00' or reservation.start_time < '23:00' < reservation.end_time:
                    if r2230_2300_tomorrow.count(reservation) == 0:
                        r2230_2300_tomorrow.append(reservation)
                if '23:00' <= reservation.start_time < '23:30':
                    r2300_2330_tomorrow.append(reservation)
                if '23:00' < reservation.end_time <= '23:30' or reservation.start_time < '23:30' < reservation.end_time:
                    if r2300_2330_tomorrow.count(reservation) == 0:
                        r2300_2330_tomorrow.append(reservation)
                if '23:30' <= reservation.start_time < '00:00':
                    r2330_0000_tomorrow.append(reservation)
                if '23:30' < reservation.end_time <= '00:00' or reservation.start_time < '00:00' < reservation.end_time:
                    if r2330_0000_tomorrow.count(reservation) == 0:
                        r2330_0000_tomorrow.append(reservation)

            dict_r0000_0030_tomorrow['key2'] = r0000_0030_tomorrow
            dict_r0030_0100_tomorrow['key2'] = r0030_0100_tomorrow
            dict_r0100_0130_tomorrow['key2'] = r0100_0130_tomorrow
            dict_r0130_0200_tomorrow['key2'] = r0130_0200_tomorrow
            dict_r0200_0230_tomorrow['key2'] = r0200_0230_tomorrow
            dict_r0230_0300_tomorrow['key2'] = r0230_0300_tomorrow
            dict_r0300_0330_tomorrow['key2'] = r0300_0330_tomorrow
            dict_r0330_0400_tomorrow['key2'] = r0330_0400_tomorrow
            dict_r0400_0430_tomorrow['key2'] = r0400_0430_tomorrow
            dict_r0430_0500_tomorrow['key2'] = r0430_0500_tomorrow
            dict_r0500_0530_tomorrow['key2'] = r0500_0530_tomorrow
            dict_r0530_0600_tomorrow['key2'] = r0530_0600_tomorrow
            dict_r0600_0630_tomorrow['key2'] = r0600_0630_tomorrow
            dict_r0630_0700_tomorrow['key2'] = r0630_0700_tomorrow
            dict_r0700_0730_tomorrow['key2'] = r0700_0730_tomorrow
            dict_r0730_0800_tomorrow['key2'] = r0730_0800_tomorrow
            dict_r0800_0830_tomorrow['key2'] = r0800_0830_tomorrow
            dict_r0830_0900_tomorrow['key2'] = r0830_0900_tomorrow
            dict_r0900_0930_tomorrow['key2'] = r0900_0930_tomorrow
            dict_r0930_1000_tomorrow['key2'] = r0930_1000_tomorrow
            dict_r1000_1030_tomorrow['key2'] = r1000_1030_tomorrow
            dict_r1030_1100_tomorrow['key2'] = r1030_1100_tomorrow
            dict_r1100_1130_tomorrow['key2'] = r1100_1130_tomorrow
            dict_r1130_1200_tomorrow['key2'] = r1130_1200_tomorrow
            dict_r1200_1230_tomorrow['key2'] = r1200_1230_tomorrow
            dict_r1230_1300_tomorrow['key2'] = r1230_1300_tomorrow
            dict_r1300_1330_tomorrow['key2'] = r1300_1330_tomorrow
            dict_r1330_1400_tomorrow['key2'] = r1330_1400_tomorrow
            dict_r1400_1430_tomorrow['key2'] = r1400_1430_tomorrow
            dict_r1430_1500_tomorrow['key2'] = r1430_1500_tomorrow
            dict_r1500_1530_tomorrow['key2'] = r1500_1530_tomorrow
            dict_r1530_1600_tomorrow['key2'] = r1530_1600_tomorrow
            dict_r1600_1630_tomorrow['key2'] = r1600_1630_tomorrow
            dict_r1630_1700_tomorrow['key2'] = r1630_1700_tomorrow
            dict_r1700_1730_tomorrow['key2'] = r1700_1730_tomorrow
            dict_r1730_1800_tomorrow['key2'] = r1730_1800_tomorrow
            dict_r1800_1830_tomorrow['key2'] = r1800_1830_tomorrow
            dict_r1830_1900_tomorrow['key2'] = r1830_1900_tomorrow
            dict_r1900_1930_tomorrow['key2'] = r1900_1930_tomorrow
            dict_r1930_2000_tomorrow['key2'] = r1930_2000_tomorrow
            dict_r2000_2030_tomorrow['key2'] = r2000_2030_tomorrow
            dict_r2030_2100_tomorrow['key2'] = r2030_2100_tomorrow
            dict_r2100_2130_tomorrow['key2'] = r2100_2130_tomorrow
            dict_r2130_2200_tomorrow['key2'] = r2130_2200_tomorrow
            dict_r2200_2230_tomorrow['key2'] = r2200_2230_tomorrow
            dict_r2230_2300_tomorrow['key2'] = r2230_2300_tomorrow
            dict_r2300_2330_tomorrow['key2'] = r2300_2330_tomorrow
            dict_r2330_0000_tomorrow['key2'] = r2330_0000_tomorrow

            dict_r0000_0030_tomorrow['key3'] = len(r0000_0030_tomorrow)
            dict_r0030_0100_tomorrow['key3'] = len(r0030_0100_tomorrow)
            dict_r0100_0130_tomorrow['key3'] = len(r0100_0130_tomorrow)
            dict_r0130_0200_tomorrow['key3'] = len(r0130_0200_tomorrow)
            dict_r0200_0230_tomorrow['key3'] = len(r0200_0230_tomorrow)
            dict_r0230_0300_tomorrow['key3'] = len(r0230_0300_tomorrow)
            dict_r0300_0330_tomorrow['key3'] = len(r0300_0330_tomorrow)
            dict_r0330_0400_tomorrow['key3'] = len(r0330_0400_tomorrow)
            dict_r0400_0430_tomorrow['key3'] = len(r0400_0430_tomorrow)
            dict_r0430_0500_tomorrow['key3'] = len(r0430_0500_tomorrow)
            dict_r0500_0530_tomorrow['key3'] = len(r0500_0530_tomorrow)
            dict_r0530_0600_tomorrow['key3'] = len(r0530_0600_tomorrow)
            dict_r0600_0630_tomorrow['key3'] = len(r0600_0630_tomorrow)
            dict_r0630_0700_tomorrow['key3'] = len(r0630_0700_tomorrow)
            dict_r0700_0730_tomorrow['key3'] = len(r0700_0730_tomorrow)
            dict_r0730_0800_tomorrow['key3'] = len(r0730_0800_tomorrow)
            dict_r0800_0830_tomorrow['key3'] = len(r0800_0830_tomorrow)
            dict_r0830_0900_tomorrow['key3'] = len(r0830_0900_tomorrow)
            dict_r0900_0930_tomorrow['key3'] = len(r0900_0930_tomorrow)
            dict_r0930_1000_tomorrow['key3'] = len(r0930_1000_tomorrow)
            dict_r1000_1030_tomorrow['key3'] = len(r1000_1030_tomorrow)
            dict_r1030_1100_tomorrow['key3'] = len(r1030_1100_tomorrow)
            dict_r1100_1130_tomorrow['key3'] = len(r1100_1130_tomorrow)
            dict_r1130_1200_tomorrow['key3'] = len(r1130_1200_tomorrow)
            dict_r1200_1230_tomorrow['key3'] = len(r1200_1230_tomorrow)
            dict_r1230_1300_tomorrow['key3'] = len(r1230_1300_tomorrow)
            dict_r1300_1330_tomorrow['key3'] = len(r1300_1330_tomorrow)
            dict_r1330_1400_tomorrow['key3'] = len(r1330_1400_tomorrow)
            dict_r1400_1430_tomorrow['key3'] = len(r1400_1430_tomorrow)
            dict_r1430_1500_tomorrow['key3'] = len(r1430_1500_tomorrow)
            dict_r1500_1530_tomorrow['key3'] = len(r1500_1530_tomorrow)
            dict_r1530_1600_tomorrow['key3'] = len(r1530_1600_tomorrow)
            dict_r1600_1630_tomorrow['key3'] = len(r1600_1630_tomorrow)
            dict_r1630_1700_tomorrow['key3'] = len(r1630_1700_tomorrow)
            dict_r1700_1730_tomorrow['key3'] = len(r1700_1730_tomorrow)
            dict_r1730_1800_tomorrow['key3'] = len(r1730_1800_tomorrow)
            dict_r1800_1830_tomorrow['key3'] = len(r1800_1830_tomorrow)
            dict_r1830_1900_tomorrow['key3'] = len(r1830_1900_tomorrow)
            dict_r1900_1930_tomorrow['key3'] = len(r1900_1930_tomorrow)
            dict_r1930_2000_tomorrow['key3'] = len(r1930_2000_tomorrow)
            dict_r2000_2030_tomorrow['key3'] = len(r2000_2030_tomorrow)
            dict_r2030_2100_tomorrow['key3'] = len(r2030_2100_tomorrow)
            dict_r2100_2130_tomorrow['key3'] = len(r2100_2130_tomorrow)
            dict_r2130_2200_tomorrow['key3'] = len(r2130_2200_tomorrow)
            dict_r2200_2230_tomorrow['key3'] = len(r2200_2230_tomorrow)
            dict_r2230_2300_tomorrow['key3'] = len(r2230_2300_tomorrow)
            dict_r2300_2330_tomorrow['key3'] = len(r2300_2330_tomorrow)
            dict_r2330_0000_tomorrow['key3'] = len(r2330_0000_tomorrow)

            dict_r0000_0030_tomorrow['key4'] = '00:00 - 00:30'
            dict_r0030_0100_tomorrow['key4'] = '00:30 - 01:00'
            dict_r0100_0130_tomorrow['key4'] = '01:00 - 01:30'
            dict_r0130_0200_tomorrow['key4'] = '01:30 - 02:00'
            dict_r0200_0230_tomorrow['key4'] = '02:00 - 02:30'
            dict_r0230_0300_tomorrow['key4'] = '02:30 - 03:00'
            dict_r0300_0330_tomorrow['key4'] = '03:00 - 03:30'
            dict_r0330_0400_tomorrow['key4'] = '03:30 - 04:00'
            dict_r0400_0430_tomorrow['key4'] = '04:00 - 04:30'
            dict_r0430_0500_tomorrow['key4'] = '04:30 - 05:00'
            dict_r0500_0530_tomorrow['key4'] = '05:00 - 05:30'
            dict_r0530_0600_tomorrow['key4'] = '05:30 - 06:00'
            dict_r0600_0630_tomorrow['key4'] = '06:00 - 06:30'
            dict_r0630_0700_tomorrow['key4'] = '06:30 - 07:00'
            dict_r0700_0730_tomorrow['key4'] = '07:00 - 07:30'
            dict_r0730_0800_tomorrow['key4'] = '07:30 - 08:00'
            dict_r0800_0830_tomorrow['key4'] = '08:00 - 08:30'
            dict_r0830_0900_tomorrow['key4'] = '08:30 - 09:00'
            dict_r0900_0930_tomorrow['key4'] = '09:00 - 09:30'
            dict_r0930_1000_tomorrow['key4'] = '09:30 - 10:00'
            dict_r1000_1030_tomorrow['key4'] = '10:00 - 10:30'
            dict_r1030_1100_tomorrow['key4'] = '10:30 - 11:00'
            dict_r1100_1130_tomorrow['key4'] = '11:00 - 11:30'
            dict_r1130_1200_tomorrow['key4'] = '11:30 - 12:00'
            dict_r1200_1230_tomorrow['key4'] = '12:00 - 12:30'
            dict_r1230_1300_tomorrow['key4'] = '12:30 - 13:00'
            dict_r1300_1330_tomorrow['key4'] = '13:00 - 13:30'
            dict_r1330_1400_tomorrow['key4'] = '13:30 - 14:00'
            dict_r1400_1430_tomorrow['key4'] = '14:00 - 14:30'
            dict_r1430_1500_tomorrow['key4'] = '14:30 - 15:00'
            dict_r1500_1530_tomorrow['key4'] = '15:00 - 15:30'
            dict_r1530_1600_tomorrow['key4'] = '15:30 - 16:00'
            dict_r1600_1630_tomorrow['key4'] = '16:00 - 16:30'
            dict_r1630_1700_tomorrow['key4'] = '16:30 - 17:00'
            dict_r1700_1730_tomorrow['key4'] = '17:00 - 17:30'
            dict_r1730_1800_tomorrow['key4'] = '17:30 - 18:00'
            dict_r1800_1830_tomorrow['key4'] = '18:00 - 18:30'
            dict_r1830_1900_tomorrow['key4'] = '18:30 - 19:00'
            dict_r1900_1930_tomorrow['key4'] = '19:00 - 19:30'
            dict_r1930_2000_tomorrow['key4'] = '19:30 - 20:00'
            dict_r2000_2030_tomorrow['key4'] = '20:00 - 20:30'
            dict_r2030_2100_tomorrow['key4'] = '20:30 - 21:00'
            dict_r2100_2130_tomorrow['key4'] = '21:00 - 21:30'
            dict_r2130_2200_tomorrow['key4'] = '21:30 - 22:00'
            dict_r2200_2230_tomorrow['key4'] = '22:00 - 22:30'
            dict_r2230_2300_tomorrow['key4'] = '22:30 - 23:00'
            dict_r2300_2330_tomorrow['key4'] = '23:00 - 23:30'
            dict_r2330_0000_tomorrow['key4'] = '23:30 - 00:00'

            all_reservations_tomorrow.append(dict_r0000_0030_tomorrow)
            all_reservations_tomorrow.append(dict_r0030_0100_tomorrow)
            all_reservations_tomorrow.append(dict_r0100_0130_tomorrow)
            all_reservations_tomorrow.append(dict_r0130_0200_tomorrow)
            all_reservations_tomorrow.append(dict_r0200_0230_tomorrow)
            all_reservations_tomorrow.append(dict_r0230_0300_tomorrow)
            all_reservations_tomorrow.append(dict_r0300_0330_tomorrow)
            all_reservations_tomorrow.append(dict_r0330_0400_tomorrow)
            all_reservations_tomorrow.append(dict_r0400_0430_tomorrow)
            all_reservations_tomorrow.append(dict_r0430_0500_tomorrow)
            all_reservations_tomorrow.append(dict_r0500_0530_tomorrow)
            all_reservations_tomorrow.append(dict_r0530_0600_tomorrow)
            all_reservations_tomorrow.append(dict_r0600_0630_tomorrow)
            all_reservations_tomorrow.append(dict_r0630_0700_tomorrow)
            all_reservations_tomorrow.append(dict_r0700_0730_tomorrow)
            all_reservations_tomorrow.append(dict_r0730_0800_tomorrow)
            all_reservations_tomorrow.append(dict_r0800_0830_tomorrow)
            all_reservations_tomorrow.append(dict_r0830_0900_tomorrow)
            all_reservations_tomorrow.append(dict_r0900_0930_tomorrow)
            all_reservations_tomorrow.append(dict_r0930_1000_tomorrow)
            all_reservations_tomorrow.append(dict_r1000_1030_tomorrow)
            all_reservations_tomorrow.append(dict_r1030_1100_tomorrow)
            all_reservations_tomorrow.append(dict_r1100_1130_tomorrow)
            all_reservations_tomorrow.append(dict_r1130_1200_tomorrow)
            all_reservations_tomorrow.append(dict_r1200_1230_tomorrow)
            all_reservations_tomorrow.append(dict_r1230_1300_tomorrow)
            all_reservations_tomorrow.append(dict_r1300_1330_tomorrow)
            all_reservations_tomorrow.append(dict_r1330_1400_tomorrow)
            all_reservations_tomorrow.append(dict_r1400_1430_tomorrow)
            all_reservations_tomorrow.append(dict_r1430_1500_tomorrow)
            all_reservations_tomorrow.append(dict_r1500_1530_tomorrow)
            all_reservations_tomorrow.append(dict_r1530_1600_tomorrow)
            all_reservations_tomorrow.append(dict_r1600_1630_tomorrow)
            all_reservations_tomorrow.append(dict_r1630_1700_tomorrow)
            all_reservations_tomorrow.append(dict_r1700_1730_tomorrow)
            all_reservations_tomorrow.append(dict_r1730_1800_tomorrow)
            all_reservations_tomorrow.append(dict_r1800_1830_tomorrow)
            all_reservations_tomorrow.append(dict_r1830_1900_tomorrow)
            all_reservations_tomorrow.append(dict_r1900_1930_tomorrow)
            all_reservations_tomorrow.append(dict_r1930_2000_tomorrow)
            all_reservations_tomorrow.append(dict_r2000_2030_tomorrow)
            all_reservations_tomorrow.append(dict_r2030_2100_tomorrow)
            all_reservations_tomorrow.append(dict_r2100_2130_tomorrow)
            all_reservations_tomorrow.append(dict_r2130_2200_tomorrow)
            all_reservations_tomorrow.append(dict_r2200_2230_tomorrow)
            all_reservations_tomorrow.append(dict_r2230_2300_tomorrow)
            all_reservations_tomorrow.append(dict_r2300_2330_tomorrow)
            all_reservations_tomorrow.append(dict_r2330_0000_tomorrow)
            context['all_reservations_tomorrow'] = all_reservations_tomorrow

            if not start_date <= today <= end_date:
                today = 'Not working today'
            context['barbershop'] = barbershop
            context['user'] = user
            context['operation_date'] = str(start_date) + " ~ " + str(end_date)
            context['today'] = today
            context['yesterday'] = yesterday
            context['tomorrow'] = tomorrow
            return render(request, 'barbershopMgmt.html', context)


def editMgmt(request):
    context = {}
    errors_name = []
    errors_service_type = []
    if request.method == 'GET':
        user = User.objects.get(username=request.user)
        barbershop = request.GET['barbershop']
        barbershop_object = Barbershop.objects.get(name=barbershop)
        barbershop_form = BarbershopForm(instance=barbershop_object)
        context['barbershop_object'] = barbershop_object
        context['barbershop_form'] = barbershop_form
        address = Address.objects.get(user=user)
        address_form = AddressForm(instance=address)
        context['address_form'] = address_form
        return render(request, 'editMgmt.html', context)
    if request.method == 'POST':
        user = User.objects.get(username=request.user)
        name = request.POST['name']
        barbershop1 = request.POST['barbershop']
        print barbershop1
        print name
        print request.POST
        print 'service_type' in request.POST

        if not barbershop1 == name or not 'service_type' in request.POST:
            if Barbershop.objects.filter(name__exact=name) or not 'service_type' in request.POST:
                if Barbershop.objects.filter(name__exact=name):
                    errors_name.append('Barbershop name has already been used.')
                if not 'service_type' in request.POST:
                    errors_service_type.append('Please choose the service type.')
                barbershop_object1 = Barbershop.objects.get(name=barbershop1, user=user)
                barbershop_form = BarbershopForm(request.POST, request.FILES, instance=barbershop_object1)
                address = Address.objects.get(user=user)
                address_form = AddressForm(request.POST, instance=address)
                if not barbershop_form.is_valid() or not address_form.is_valid():
                    barbershop_object1 = Barbershop.objects.get(name=barbershop1, user=user)
                    context['barbershop_object'] = barbershop_object1
                    context['barbershop_form'] = barbershop_form
                    context['address_form'] = address_form
                    context['errors_name'] = errors_name
                    context['errors_service_type'] = errors_service_type
                    return render(request, 'editMgmt.html', context)
                barbershop_object1 = Barbershop.objects.get(name=barbershop1,
                                                            user=user)  # need to declare again, otherwise it would change to another barbershop, dont know why, seems like it is because of is_valid()
                context['barbershop_object'] = barbershop_object1
                context['barbershop_form'] = barbershop_form
                context['address_form'] = address_form
                context['errors_name'] = errors_name
                context['errors_service_type'] = errors_service_type
                return render(request, 'editMgmt.html', context)

        barbershop_object1 = Barbershop.objects.get(name=barbershop1, user=user)
        barbershop_form = BarbershopForm(request.POST, request.FILES, instance=barbershop_object1)
        address = Address.objects.get(user=user)
        address_form = AddressForm(request.POST, instance=address)
        # print address
        # print address_form
        if not barbershop_form.is_valid() or not address_form.is_valid():
            print barbershop_form.is_valid()
            print address_form.is_valid()
            barbershop_object1 = Barbershop.objects.get(name=barbershop1, user=user)
            context['barbershop_object'] = barbershop_object1
            context['barbershop_form'] = barbershop_form
            context['address_form'] = address_form
            return render(request, 'editMgmt.html', context)
        # print barbershop_form.cleaned_data['picture']
        barbershop_object = barbershop_form.save(commit=False)
        # print barbershop_object.start_date
        # if not the model, you need to assign them manually
        barbershop_object.user = user
        barbershop_object.address = address
        barbershop_object.start_date = request.POST['start_date']
        barbershop_object.end_date = request.POST['end_date']
        barbershop_object.operation_start_time = request.POST['operation_start_time']
        barbershop_object.operation_end_time = request.POST['operation_end_time']
        services = request.POST.getlist('service_type')
        tmp = ""
        for i in range(len(services) - 1):
            tmp = tmp + services[i] + ", "
        tmp = tmp + services[len(services) - 1]
        barbershop_object.service_type = tmp
        # print tmp
        if barbershop_form.cleaned_data['picture']:
            url = s3_upload(barbershop_form.cleaned_data['picture'], barbershop_object.id)
            print url
            barbershop_object.picture_url = url
            barbershop_object.save()
        # if 'picture' in request.FILES:
        #     profile.picture = request.FILES['picture']
        # context['barbershop'] = barbershop_object
        # print barbershop_object.save()
        message = 'Barbershop information updated successfully!'
        context['message'] = message
        context['barbershop_object'] = barbershop_object
        context['barbershop_form'] = barbershop_form
        context['address_form'] = address_form
        barbershop_form.save()
        address_form.save()
        barbershop_object.save()
        return render(request, 'editMgmt.html', context)


def modifyReservation(request):
    context = {}
    results = []
    user = User.objects.get(username=request.user)
    barbershop_name = request.POST['barbershop']
    city = request.POST['city']
    service_type = request.POST['old_service_type']
    date = request.POST['old_date']
    time = request.POST['old_time']
    print request.POST
    reservation_date_and_time = request.POST['reservation_date_and_time']
    new_service_type = request.POST['new_service_type']
    new_date = request.POST['date']
    new_time = request.POST['new_time']
    barbershop_object = Barbershop.objects.get(name=barbershop_name)
    start_date = barbershop_object.start_date
    end_date = barbershop_object.end_date
    operation_start_time = barbershop_object.operation_start_time
    operation_end_time = barbershop_object.operation_end_time
    flag = False
    print "habnonsoanonsoc"
    print str(start_date)
    print new_date
    print date
    if not str(start_date) <= new_date <= str(end_date):
        flag = True
        results.append('The barbershop does not work on ' + new_date + '.')
    if not str(operation_start_time) <= new_time <= str(operation_end_time):
        flag = True
        results.append('The barbershop does not work at ' + new_time + '.')

    print barbershop_object
    barbershop_user = User.objects.get(username=barbershop_object.user)

    print new_service_type
    end_time = ''
    if new_service_type == 'Cutting':
        tmp = new_time
        tmp = tmp.replace(':', '')
        num = int(tmp) + 30
        tmp = str(num)
        if len(tmp) == 2:
            tmp = '00' + tmp
        elif len(tmp) == 3:
            tmp = '0' + tmp
        end_time = tmp[:-2] + ':' + tmp[-2:]
    elif new_service_type == 'Coloring':
        tmp = new_time
        tmp = tmp.replace(':', '')
        num = int(tmp) + 200
        tmp = str(num)
        if len(tmp) == 3:
            tmp = '0' + tmp
        end_time = tmp[:-2] + ':' + tmp[-2:]
    elif new_service_type == 'Waving':
        tmp = new_time
        tmp = tmp.replace(':', '')
        num = int(tmp) + 400
        tmp = str(num)
        if len(tmp) == 3:
            tmp = '0' + tmp
        end_time = tmp[:-2] + ':' + tmp[-2:]
    print 'end_time'
    print end_time
    if not str(operation_start_time) <= end_time <= str(operation_end_time):
        flag = True
        results.append(
            'The time duration of the service ' + new_service_type + ' will exceed the barbershop operation time does not work at')

    if flag == True:
        results.append('Sorry, the modification does not succeed')
        context['results'] = results
        return render(request, 'modifyConfirmation.html', context)
    # print reservation_date_and_time
    # date_object = datetime.strptime('Jun 1 2005  1:33PM', '%b %d %Y %I:%M%p')
    # reservation_date_and_time2 = datetime.datetime.strptime(reservation_date_and_time, "%Y-%m-%d %H:%M")
    old_reservation = Reservations.objects.get(user=user, service_type=service_type, start_date=date, start_time=time,
                                               barbershop=barbershop_object)
    old_reservation.service_type = new_service_type
    old_reservation.start_date = new_date
    old_reservation.start_time = new_time
    old_reservation.end_time = end_time
    old_reservation.save()
    results.append('Congratulations. You reservation is modified successfully!')
    context['results'] = results
    return render(request, 'modifyConfirmation.html', context)


def redirectToModification(request):
    context = {}
    city = request.POST['city']
    service_type = request.POST['service_type']
    date = request.POST['date']
    time = request.POST['time']
    reservation_date_and_time = request.POST['reservation_date_and_time']
    print reservation_date_and_time
    print service_type
    print date
    print time

    barbershop = request.POST['barbershop']
    print barbershop
    context['search_form'] = SearchForm()
    context['city'] = city
    context['service_type'] = service_type
    context['date'] = date
    context['time'] = time
    context['reservation_date_and_time'] = reservation_date_and_time
    context['barbershop'] = barbershop
    return render(request, 'modificationSelection.html', context)


def cancelReservation(request):
    context = {}
    results = []
    user = User.objects.get(username=request.user)
    barbershop_name = request.POST['barbershop']
    city = request.POST['city']
    service_type = request.POST['old_service_type']
    date = request.POST['old_date']
    time = request.POST['old_time']
    barbershop_object = Barbershop.objects.get(name=barbershop_name)
    old_reservation = Reservations.objects.get(user=user, service_type=service_type, start_date=date, start_time=time,
                                               barbershop=barbershop_object)
    old_reservation.delete()
    results.append('Congratulations. You have deleted the reservation!')
    context['results'] = results
    return render(request, 'modifyConfirmation.html', context)
