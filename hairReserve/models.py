from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from django.core.validators import RegexValidator


# Create your models here.

class Address(models.Model):
    user = models.OneToOneField(User, null=True)
    address = models.CharField(max_length=200, blank=True)
    # line2Address = models.CharField(max_length=200)
    city = models.CharField(max_length=30, blank=True)
    state = models.CharField(max_length=20, blank=True)
    zip = models.CharField(max_length=10, blank=True)

    # country = models.CharField(max_length=20, blank=True)

    def __unicode__(self):
        return '{}: {}'.format(self.user, self.city)


class Barbershop(models.Model):
    name = models.CharField(max_length=30)
    user = models.ForeignKey(User)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$',
                                 message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone = models.CharField(max_length=15, validators=[phone_regex])  # validators should be a list
    address = models.OneToOneField(Address)
    website = models.CharField(max_length=765, blank=True)
    picture_url = models.CharField(blank=True, max_length=256)
    service_type = models.CharField(max_length=200)
    start_date = models.DateField(auto_now_add=False, null=True)
    end_date = models.DateField(auto_now_add=False, null=True)
    operation_start_time = models.CharField(max_length=10, default='0000')
    operation_end_time = models.CharField(max_length=10, default='0000')
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=0)
    total_rating = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    description = models.CharField(max_length=430, blank=True)
    number_of_comments = models.IntegerField(default=0)

    def __unicode__(self):
        return '{}'.format(self.name)

    def __str__(self):
        return self.__unicode__()


class Comments(models.Model):
    user = models.ForeignKey(User)
    barbershop = models.ForeignKey(Barbershop, related_name="barbershopcomments")
    text = models.CharField(max_length=400)
    dateAndTime = models.DateTimeField(auto_now_add=True)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=0)

    def __unicode__(self):
        return '{}, {}, {}'.format(self.user, self.barbershop, self.dateAndTime)

    def __str__(self):
        return self.__unicode__()

    class Meta:  # ordering descending
        ordering = ['-dateAndTime']


class Profile(models.Model):
    # Required: link a Profile to User.
    user = models.OneToOneField(User)
    address = models.OneToOneField(Address)
    # The additional attributes we wish to include.
    # Citation of phone number: http://stackoverflow.com/questions/19130942/whats-the-best-way-to-store-phone-number-in-django-models
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$',
                                 message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone = models.CharField(max_length=15, validators=[phone_regex], blank=True)  # validators should be a list
    # phone = models.CharField(max_length=12, blank=True)
    picture_url = models.CharField(blank=True, max_length=256)
    primary_city = models.CharField(blank=True, max_length=30)

    # picture = models.ImageField(upload_to='profile_pictures', blank=True)

    def __unicode__(self):
        return self.user.username


class Favorites(models.Model):
    barbershop = models.ManyToManyField(Barbershop, related_name="favorites")
    user = models.ForeignKey(User, related_name="user")
    countForFavorites = models.IntegerField(default=0)

    def __unicode__(self):
        return '{}: {}'.format(self.user, self.countForFavorites)

    def __str__(self):
        return self.__unicode__()


class Reservations(models.Model):
    user = models.ForeignKey(User)
    reservation_date_and_time = models.DateTimeField(auto_now_add=True)
    barbershop = models.ForeignKey(Barbershop, related_name="reservations", null=True)
    service_type = models.CharField(max_length=200, blank=True)
    start_time = models.CharField(max_length=10, default='00:00')
    end_time = models.CharField(max_length=10, default='00:00')
    start_date = models.DateField(auto_now_add=False, null=True)

    def __unicode__(self):
        return '{}: {}'.format(self.user, self.barbershop)

    def __str__(self):
        return self.__unicode__()

# class ServiceType(models.Model):
#     barbershop = models.ForeignKey(Barbershop, related_name="barbershopservicetypes")
#     cutting_service = models.CharField(default='cutting service', max_length=200)
#     coloring_service = models.CharField(default='coloring service', max_length=200)
#     waving_service = models.CharField(default='waving service', max_length=200)
#
#     def __unicode__(self):
#         return '{}: {}'.format(self.barbershop, self.id)
#
#     def __str__(self):
#         return self.__unicode__()
