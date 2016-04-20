"""InClassExercise URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^$', auth_views.login, {'template_name': 'login.html'}, name='login2'),
    url(r'^login$', auth_views.login, {'template_name': 'login.html'}, name='login'),
    url(r'^barbershopLogin$', 'hairReserve.views.barbershopLogin', name='barbershopLogin'),
    url(r'^follow/(\w+)/$', 'hairReserve.views.follow', name='follow'),
    url(r'^follow/(?P<name>[a-zA-Z0-9_@\+\-]+)/$', 'hairReserve.views.follow', name='follow2'),
    url(r'^register$', 'hairReserve.views.register', name='register'),
    url(r'^registerAsBarbershop', 'hairReserve.views.register_as_barbershop', name='registerAsBarbershop'),
    url(r'^home$', 'hairReserve.views.home', name='home'),
    url(r'^post$', 'hairReserve.views.post', name='post'),
    url(r'^profile', 'hairReserve.views.profile', name='profile'),
    url(r'^editprofile/', 'hairReserve.views.editprofile', name='editprofile'),
    # url(r'^otherProfile/(\w+)/$', 'hairReserve.views.follow',name='follow'),
    # url(r'^followerStream', 'hairReserve.views.followerStream', name='followerStream'),
    url(r'^logout$', auth_views.logout_then_login, name='logout'),
    url(r'^postcomment/$', 'hairReserve.views.postcomment', name='postcomment'),
    url(r'^sendReminder/$', 'hairReserve.views.sendReminder', name='sendReminder'),
    url(r'^getallcomments/$', 'hairReserve.views.getallcomments',name='getallcomments'),
    url(r'^confirm-registration/(?P<username>[a-zA-Z0-9_@\+\-]+)/(?P<token>[a-z0-9\-]+)$',
        'hairReserve.views.confirm_registration', name='confirm'),
    url(r'^searchBarbershop', 'hairReserve.views.searchBarbershop', name='searchBarbershop'),
    url(r'^reserveBarbershop', 'hairReserve.views.reserveBarbershop', name='reserveBarbershop'),
    url(r'^reserveThroughFavorites', 'hairReserve.views.reserveThroughFavorites', name='reserveThroughFavorites'),
    url(r'^barbershopMgmtBoard', 'hairReserve.views.barbershopMgmtBoard', name='barbershopMgmtBoard'),
    url(r'^redirectToMgmt/(?P<barbershop_name>\w+)/(?P<user_name>\w+)/$', 'hairReserve.views.redirectToMgmt',
        name='redirectToMgmt'),
    url(r'^editMgmt', 'hairReserve.views.editMgmt', name='editMgmt'),
    url(r'^returnToMgmt', 'hairReserve.views.returnToMgmt', name='returnToMgmt'),
    url(r'^redirectToModification$', 'hairReserve.views.redirectToModification', name='redirectToModification'),
    url(r'^modifyReservation', 'hairReserve.views.modifyReservation', name='modifyReservation'),
    url(r'^cancelReservation', 'hairReserve.views.cancelReservation', name='cancelReservation'),

]
