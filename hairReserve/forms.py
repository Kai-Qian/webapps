from django import forms
from hairReserve.models import *
from django.contrib.auth.models import User
from bootstrap3_datetime.widgets import DateTimePicker

# Citation of COUNTRY_CHOICES: https://github.com/viewflow/django-material/blob/master/demo/forms.py
# COUNTRY_CHOICES = (
#     ('', 'Country'), (244, 'Aaland Islands'), (1, 'Afghanistan'), (2, 'Albania'), (3, 'Algeria'),
#     (4, 'American Samoa'), (5, 'Andorra'), (6, 'Angola'), (7, 'Anguilla'), (8, 'Antarctica'),
#     (9, 'Antigua and Barbuda'), (10, 'Argentina'), (11, 'Armenia'), (12, 'Aruba'), (13, 'Australia'),
#     (14, 'Austria'), (15, 'Azerbaijan'), (16, 'Bahamas'), (17, 'Bahrain'), (18, 'Bangladesh'),
#     (19, 'Barbados'), (20, 'Belarus'), (21, 'Belgium'), (22, 'Belize'), (23, 'Benin'),
#     (24, 'Bermuda'), (25, 'Bhutan'), (26, 'Bolivia'), (245, 'Bonaire, Sint Eustatius and Saba'),
#     (27, 'Bosnia and Herzegovina'), (28, 'Botswana'), (29, 'Bouvet Island'), (30, 'Brazil'),
#     (31, 'British Indian Ocean Territory'), (32, 'Brunei Darussalam'),
#     (33, 'Bulgaria'), (34, 'Burkina Faso'), (35, 'Burundi'), (36, 'Cambodia'), (37, 'Cameroon'),
#     (38, 'Canada'), (251, 'Canary Islands'), (39, 'Cape Verde'), (40, 'Cayman Islands'),
#     (41, 'Central African Republic'),
#     (42, 'Chad'), (43, 'Chile'), (44, 'China'), (45, 'Christmas Island'), (46, 'Cocos (Keeling) Islands'),
#     (47, 'Colombia'), (48, 'Comoros'), (49, 'Congo'), (50, 'Cook Islands'), (51, 'Costa Rica'),
#     (52, "Cote D'Ivoire"), (53, 'Croatia'), (54, 'Cuba'), (246, 'Curacao'), (55, 'Cyprus'),
#     (56, 'Czech Republic'), (237, 'Democratic Republic of Congo'), (57, 'Denmark'), (58, 'Djibouti'), (59, 'Dominica'),
#     (60, 'Dominican Republic'), (61, 'East Timor'), (62, 'Ecuador'), (63, 'Egypt'), (64, 'El Salvador'),
#     (65, 'Equatorial Guinea'), (66, 'Eritrea'), (67, 'Estonia'), (68, 'Ethiopia'), (69, 'Falkland Islands (Malvinas)'),
#     (70, 'Faroe Islands'), (71, 'Fiji'), (72, 'Finland'), (74, 'France, skypolitan'), (75, 'French Guiana'),
#     (76, 'French Polynesia'), (77, 'French Southern Territories'), (126, 'FYROM'), (78, 'Gabon'), (79, 'Gambia'),
#     (80, 'Georgia'), (81, 'Germany'), (82, 'Ghana'), (83, 'Gibraltar'), (84, 'Greece'),
#     (85, 'Greenland'), (86, 'Grenada'), (87, 'Guadeloupe'), (88, 'Guam'), (89, 'Guatemala'),
#     (241, 'Guernsey'), (90, 'Guinea'), (91, 'Guinea-Bissau'), (92, 'Guyana'), (93, 'Haiti'),
#     (94, 'Heard and Mc Donald Islands'), (95, 'Honduras'), (96, 'Hong Kong'), (97, 'Hungary'), (98, 'Iceland'),
#     (99, 'India'), (100, 'Indonesia'), (101, 'Iran (Islamic Republic of)'), (102, 'Iraq'), (103, 'Ireland'),
#     (104, 'Israel'), (105, 'Italy'), (106, 'Jamaica'), (107, 'Japan'), (240, 'Jersey'),
#     (108, 'Jordan'), (109, 'Kazakhstan'), (110, 'Kenya'), (111, 'Kiribati'), (113, 'Korea, Republic of'),
#     (114, 'Kuwait'), (115, 'Kyrgyzstan'), (116, "Lao People's Democratic Republic"), (117, 'Latvia'), (118, 'Lebanon'),
#     (119, 'Lesotho'), (120, 'Liberia'), (121, 'Libyan Arab Jamahiriya'), (122, 'Liechtenstein'), (123, 'Lithuania'),
#     (124, 'Luxembourg'), (125, 'Macau'), (127, 'Madagascar'), (128, 'Malawi'), (129, 'Malaysia'),
#     (130, 'Maldives'), (131, 'Mali'), (132, 'Malta'), (133, 'Marshall Islands'), (134, 'Martinique'),
#     (135, 'Mauritania'), (136, 'Mauritius'), (137, 'Mayotte'), (138, 'Mexico'),
#     (139, 'Micronesia, Federated States of'),
#     (140, 'Moldova, Republic of'), (141, 'Monaco'), (142, 'Mongolia'), (242, 'Montenegro'), (143, 'Montserrat'),
#     (144, 'Morocco'), (145, 'Mozambique'), (146, 'Myanmar'), (147, 'Namibia'), (148, 'Nauru'),
#     (149, 'Nepal'), (150, 'Netherlands'), (151, 'Netherlands Antilles'), (152, 'New Caledonia'), (153, 'New Zealand'),
#     (154, 'Nicaragua'), (155, 'Niger'), (156, 'Nigeria'), (157, 'Niue'), (158, 'Norfolk Island'),
#     (112, 'North Korea'), (159, 'Northern Mariana Islands'), (160, 'Norway'), (161, 'Oman'), (162, 'Pakistan'),
#     (163, 'Palau'), (247, 'Palestinian Territory, Occupied'), (164, 'Panama'), (165, 'Papua New Guinea'),
#     (166, 'Paraguay'),
#     (167, 'Peru'), (168, 'Philippines'), (169, 'Pitcairn'), (170, 'Poland'), (171, 'Portugal'),
#     (172, 'Puerto Rico'), (173, 'Qatar'), (174, 'Reunion'), (175, 'Romania'), (176, 'Russian Federation'),
#     (177, 'Rwanda'), (178, 'Saint Kitts and Nevis'), (179, 'Saint Lucia'), (180, 'Saint Vincent and the Grenadines'),
#     (181, 'Samoa'), (182, 'San Marino'), (183, 'Sao Tome and Principe'), (184, 'Saudi Arabia'), (185, 'Senegal'),
#     (243, 'Serbia'), (186, 'Seychelles'), (187, 'Sierra Leone'), (188, 'Singapore'), (189, 'Slovak Republic'),
#     (190, 'Slovenia'), (191, 'Solomon Islands'), (192, 'Somalia'), (193, 'South Africa'),
#     (194, 'South Georgia &amp; South Sandwich Islands'), (248, 'South Sudan'), (195, 'Spain'), (196, 'Sri Lanka'),
#     (249, 'St. Barthelemy'), (197, 'St. Helena'), (250, 'St. Martin (French part)'), (198, 'St. Pierre and Miquelon'),
#     (199, 'Sudan'), (200, 'Suriname'), (201, 'Svalbard and Jan Mayen Islands'), (202, 'Swaziland'),
#     (203, 'Sweden'), (204, 'Switzerland'), (205, 'Syrian Arab Republic'), (206, 'Taiwan'), (207, 'Tajikistan'),
#     (208, 'Tanzania, United Republic of'), (209, 'Thailand'), (210, 'Togo'), (211, 'Tokelau'), (212, 'Tonga'),
#     (213, 'Trinidad and Tobago'), (214, 'Tunisia'), (215, 'Turkey'), (216, 'Turkmenistan'),
#     (217, 'Turks and Caicos Islands'), (218, 'Tuvalu'), (219, 'Uganda'), (220, 'Ukraine'),
#     (221, 'United Arab Emirates'),
#     (222, 'United Kingdom'), (223, 'United States'), (224, 'United States Minor Outlying Islands'), (225, 'Uruguay'),
#     (226, 'Uzbekistan'), (227, 'Vanuatu'), (228, 'Vatican City State (Holy See)'), (229, 'Venezuela'),
#     (230, 'Viet Nam'),
#     (231, 'Virgin Islands (British)'), (232, 'Virgin Islands (U.S.)'), (233, 'Wallis and Futuna Islands'),
#     (234, 'Western Sahara'), (235, 'Yemen'), (238, 'Zambia'), (239, 'Zimbabwe'),
# )
CITY_CHOICES = (
    ('', 'City'), ('Aberdeen', 'Aberdeen'), ('Albuquerque', 'Albuquerque'),
    ('Allentown', 'Allentown'), ('Anchorage', 'Anchorage'), ('Atlanta', 'Atlanta'),
    ('Augusta', 'Augusta'), ('Aurora', 'Aurora'), ('Aurora', 'Aurora'), ('Balitmore', 'Balitmore'),
    ('Bangor', 'Bangor'), ('Baton Rouge', 'Baton Rouge'), ('Bellevue', 'Bellevue'),
    ('Billings', 'Billings'), ('Biloxi', 'Biloxi'), ('Birmingham', 'Birmingham'),
    ('Bismarck', 'Bismarck'), ('Boise', 'Boise'), ('Boston', 'Boston'), ('Bridgeport', 'Bridgeport'),
    ('Buffalo', 'Buffalo'), ('Burlington', 'Burlington'), ('Casper', 'Casper'),
    ('Cedar Rapids', 'Cedar Rapids'), ('Charleston', 'Charleston'), ('Charleston', 'Charleston'),
    ('Charlotte', 'Charlotte'), ('Chesapeake', 'Chesapeake'), ('Cheyenne', 'Cheyenne'),
    ('Chicago', 'Chicago'), ('Cincinnati', 'Cincinnati'), ('Cleveland', 'Cleveland'),
    ('Colorado Springs', 'Colorado Springs'), ('Columbia', 'Columbia'), ('Columbus', 'Columbus'),
    ('Columbus', 'Columbus'), ('Concord', 'Concord'), ('Cranston', 'Cranston'), ('Dallas', 'Dallas'),
    ('Davenport', 'Davenport'), ('Denver', 'Denver'), ('Des Moines', 'Des Moines'),
    ('Detroit', 'Detroit'), ('Dover', 'Dover'), ('Eugene', 'Eugene'), ('Evansville', 'Evansville'),
    ('Fairbanks', 'Fairbanks'), ('Fargo', 'Fargo'), ('Fayetteville', 'Fayetteville'),
    ('Fort Smith', 'Fort Smith'), ('Fort Wayn', 'Fort Wayn'), ('Frederick', 'Frederick'),
    ('Gaithersburg', 'Gaithersburg'), ('Grand Forks', 'Grand Forks'), ('Grand Rapids', 'Grand Rapids'),
    ('Great Falls', 'Great Falls'), ('Green Bay', 'Green Bay'), ('Greensboro', 'Greensboro'),
    ('Gulfport', 'Gulfport'), ('Hartford', 'Hartford'), ('Henderson', 'Henderson'), ('Hilo', 'Hilo'),
    ('Honolulu', 'Honolulu'), ('Houston', 'Houston'), ('Huntington', 'Huntington'),
    ('Idaho Falls', 'Idaho Falls'), ('Indianapolis', 'Indianapolis'), ('Jackson', 'Jackson'),
    ('Jacksonville', 'Jacksonville'), ('Jersey City', 'Jersey City'), ('Juneau', 'Juneau'),
    ('Kailua', 'Kailua'), ('Kansas City', 'Kansas City'), ('Kansas City', 'Kansas City'),
    ('Knoxville', 'Knoxville'), ('Laramie', 'Laramie'), ('Las Cruces', 'Las Cruces'),
    ('Las Vegas', 'Las Vegas'), ('Lewiston', 'Lewiston'), ('Lexington', 'Lexington'),
    ('Lincoln', 'Lincoln'), ('Little Rock', 'Little Rock'), ('Los Angeles', 'Los Angeles'),
    ('Louisville', 'Louisville'), ('Madison', 'Madison'), ('Manchester', 'Manchester'),
    ('Memphis', 'Memphis'), ('Mesa', 'Mesa'), ('Miami', 'Miami'), ('Milwaukee', 'Milwaukee'),
    ('Minneapolis', 'Minneapolis'), ('Missoula', 'Missoula'), ('Mobile', 'Mobile'),
    ('Montgomery', 'Montgomery'), ('Nampa', 'Nampa'), ('Nashua', 'Nashua'), ('Nashville', 'Nashville'),
    ('New Haven', 'New Haven'), ('New Orleans', 'New Orleans'), ('New York', 'New York'),
    ('Newark', 'Newark'), ('Newark', 'Newark'), ('Norfolk', 'Norfolk'), ('Norman', 'Norman'),
    ('North Charleston', 'North Charleston'), ('Oklahoma City', 'Oklahoma City'), ('Omaha', 'Omaha'),
    ('Overland Park', 'Overland Park'), ('Owensboro', 'Owensboro'), ('Parkersburg', 'Parkersburg'),
    ('Paterson', 'Paterson'), ('Philadephia', 'Philadephia'), ('Phoenix', 'Phoenix'),
    ('Pittsburgh', 'Pittsburgh'), ('Portland', 'Portland'), ('Portland', 'Portland'),
    ('Providence', 'Providence'), ('Provo', 'Provo'), ('Raleigh', 'Raleigh'),
    ('Rapid City', 'Rapid City'), ('Reno', 'Reno'), ('Rochester', 'Rochester'),
    ('Rochester', 'Rochester'), ('Rockford', 'Rockford'), ('Rutland', 'Rutland'),
    ('Saint Paul', 'Saint Paul'), ('Salem', 'Salem'), ('Salt Lake City', 'Salt Lake City'),
    ('San Antonio', 'San Antonio'), ('San Diego', 'San Diego'), ('San Jose', 'San Jose'),
    ('Sanit Louis', 'Sanit Louis'), ('Santa Fe', 'Santa Fe'), ('Seattle', 'Seattle'),
    ('Shreveport', 'Shreveport'), ('Sioux Falls', 'Sioux Falls'),
    ('South Burlington', 'South Burlington'), ('Spokane', 'Spokane'),
    ('Springfield', 'Springfield'), ('Springfield', 'Springfield'), ('Tacoma', 'Tacoma'),
    ('Tampa', 'Tampa'), ('Tucson', 'Tucson'), ('Tulsa', 'Tulsa'),
    ('Virginia Beach', 'Virginia Beach'), ('Warren', 'Warren'), ('Warwick', 'Warwick'),
    ('Washington D.C.', 'Washington D.C.'), ('West Valley City', 'West Valley City'),
    ('Wichita', 'Wichita'), ('Wilmington', 'Wilmington'), ('Worcester', 'Worcester'),
)

TIME_CHOICE_START = (
    ('', 'Operation start time'), ('00:00', '00:00'), ('00:30', '00:30'), ('01:00', '01:00'), ('01:30', '01:30'),
    ('02:00', '02:00'), ('02:30', '02:30'), ('03:00', '03:00'), ('03:30', '03:30'), ('04:00', '04:00'),
    ('04:30', '04:30'), ('05:00', '05:00'), ('05:30', '05:30'), ('06:00', '06:00'), ('06:30', '06:30'),
    ('07:00', '07:00'), ('07:30', '07:30'), ('08:00', '08:00'), ('08:30', '08:30'), ('09:00', '09:00'),
    ('09:30', '09:30'), ('10:00', '10:00'), ('10:30', '10:30'), ('11:00', '11:00'), ('11:30', '11:30'),
    ('12:00', '12:00'), ('12:30', '12:30'), ('13:00', '13:00'), ('13:30', '13:30'), ('14:00', '14:00'),
    ('14:30', '14:30'), ('15:00', '15:00'), ('15:30', '15:30'), ('16:00', '16:00'), ('16:30', '16:30'),
    ('17:00', '17:00'), ('17:30', '17:30'), ('18:00', '18:00'), ('18:30', '18:30'), ('19:00', '19:00'),
    ('19:30', '19:30'), ('20:00', '20:00'), ('20:30', '20:30'), ('21:00', '21:00'), ('21:30', '21:30'),
    ('22:00', '22:00'), ('22:30', '22:30'), ('23:00', '23:00'), ('23:30', '23:30')
)

TIME_CHOICES_END = (
    ('', 'Operation end time'), ('00:00', '00:00'), ('00:30', '00:30'), ('01:00', '01:00'), ('01:30', '01:30'),
    ('02:00', '02:00'), ('02:30', '02:30'), ('03:00', '03:00'), ('03:30', '03:30'), ('04:00', '04:00'),
    ('04:30', '04:30'), ('05:00', '05:00'), ('05:30', '05:30'), ('06:00', '06:00'), ('06:30', '06:30'),
    ('07:00', '07:00'), ('07:30', '07:30'), ('08:00', '08:00'), ('08:30', '08:30'), ('09:00', '09:00'),
    ('09:30', '09:30'), ('10:00', '10:00'), ('10:30', '10:30'), ('11:00', '11:00'), ('11:30', '11:30'),
    ('12:00', '12:00'), ('12:30', '12:30'), ('13:00', '13:00'), ('13:30', '13:30'), ('14:00', '14:00'),
    ('14:30', '14:30'), ('15:00', '15:00'), ('15:30', '15:30'), ('16:00', '16:00'), ('16:30', '16:30'),
    ('17:00', '17:00'), ('17:30', '17:30'), ('18:00', '18:00'), ('18:30', '18:30'), ('19:00', '19:00'),
    ('19:30', '19:30'), ('20:00', '20:00'), ('20:30', '20:30'), ('21:00', '21:00'), ('21:30', '21:30'),
    ('22:00', '22:00'), ('22:30', '22:30'), ('23:00', '23:00'), ('23:30', '23:30')
)

TIME_CHOICES = (
    ('', 'Time'), ('00:00', '00:00'), ('00:30', '00:30'), ('01:00', '01:00'), ('01:30', '01:30'),
    ('02:00', '02:00'), ('02:30', '02:30'), ('03:00', '03:00'), ('03:30', '03:30'), ('04:00', '04:00'),
    ('04:30', '04:30'), ('05:00', '05:00'), ('05:30', '05:30'), ('06:00', '06:00'), ('06:30', '06:30'),
    ('07:00', '07:00'), ('07:30', '07:30'), ('08:00', '08:00'), ('08:30', '08:30'), ('09:00', '09:00'),
    ('09:30', '09:30'), ('10:00', '10:00'), ('10:30', '10:30'), ('11:00', '11:00'), ('11:30', '11:30'),
    ('12:00', '12:00'), ('12:30', '12:30'), ('13:00', '13:00'), ('13:30', '13:30'), ('14:00', '14:00'),
    ('14:30', '14:30'), ('15:00', '15:00'), ('15:30', '15:30'), ('16:00', '16:00'), ('16:30', '16:30'),
    ('17:00', '17:00'), ('17:30', '17:30'), ('18:00', '18:00'), ('18:30', '18:30'), ('19:00', '19:00'),
    ('19:30', '19:30'), ('20:00', '20:00'), ('20:30', '20:30'), ('21:00', '21:00'), ('21:30', '21:30'),
    ('22:00', '22:00'), ('22:30', '22:30'), ('23:00', '23:00'), ('23:30', '23:30')
)

SERVICE_CHOICES = (
    ('Cutting', 'Cutting service'), ('Coloring', 'Coloring service'), ('Waving', 'Waving service')
)


class LoginUserForm(forms.Form):
    username = forms.CharField(max_length=20,
                               widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(max_length=200, label="Password", widget=forms.PasswordInput(
        attrs={'class': 'form-password form-control', 'placeholder': 'Password'}))
    name = forms.CharField(max_length=200, label="Barbershop name", widget=forms.TextInput(
        attrs={'class': 'form-password form-control', 'placeholder': 'Barbershop name'}))

    def clean(self):
        cleaned_data = super(LoginUserForm, self).clean()
        return cleaned_data


class UserForm(forms.ModelForm):
    username = forms.CharField(max_length=20,
                               widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    first_name = forms.CharField(max_length=20,
                                 widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}))
    last_name = forms.CharField(max_length=20,
                                widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}))
    password = forms.CharField(max_length=200, label="Password", widget=forms.PasswordInput(
        attrs={'class': 'form-password form-control', 'placeholder': 'Password'}))
    password2 = forms.CharField(max_length=200, label="Confirm password", widget=forms.PasswordInput(
        attrs={'class': 'form-password form-control', 'placeholder': 'Confirm Password'}))
    city = forms.ChoiceField(choices=CITY_CHOICES)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password')

    def clean(self):
        cleaned_data = super(UserForm, self).clean()
        password1 = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')
        if len(password1) > 200 or len(password2) > 200:
            raise forms.ValidationError("The input is longer than 200 characters.")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords did not match")

        return cleaned_data

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if len(username) > 20:
            raise forms.ValidationError('The input is longer than 20 characters.')
        if User.objects.filter(username__exact=username):
            raise forms.ValidationError('Username is already taken')

        return username

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if len(first_name) > 20:
            raise forms.ValidationError('The input is longer than 20 characters.')
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if len(last_name) > 20:
            raise forms.ValidationError('The input is longer than 20 characters.')
        return last_name

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__exact=email):
            raise forms.ValidationError('Email address is already taken')

        return email


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ('address', 'city', 'state', 'zip')
        widgets = {
            'address': forms.TextInput(attrs={'rows': '4', 'class': 'form-control', 'placeholder': 'Address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'rows': '4', 'class': 'form-control', 'placeholder': 'State'}),
            'zip': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Zip'}),
        }

    def clean(self):
        cleaned_data = super(AddressForm, self).clean()
        return cleaned_data

    def clean_zip(self):
        zip = self.cleaned_data.get('zip')
        try:
            int(zip)
        except ValueError:
            raise forms.ValidationError('Zip must only contain digits')
        return zip

    def clean_address(self):
        address = self.cleaned_data.get('address')
        if len(address) > 200:
            raise forms.ValidationError('The input is longer than 200 characters.')
        return address

    def clean_city(self):
        city = self.cleaned_data.get('city')
        if len(city) > 30:
            raise forms.ValidationError('The input is longer than 30 characters.')
        return city

    def clean_state(self):
        state = self.cleaned_data.get('state')
        if len(state) > 20:
            raise forms.ValidationError('The input is longer than 20 characters.')
        return state


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'email': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
        }

    def clean(self):
        cleaned_data = super(UserProfileForm, self).clean()
        return cleaned_data

    # def clean_email(self):
    #     email = self.cleaned_data.get('email')
    #     if User.objects.filter(email__exact=email):
    #         raise forms.ValidationError('Email address is already taken')
    #     return email

    # def clean_username(self):
    #     username = self.cleaned_data.get('username')
    #     if User.objects.filter(username__exact=username):
    #         raise forms.ValidationError('Username is already taken')
    #     return username


class ExtraUserProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('phone', 'primary_city')
        exclude = (
            'picture_url',
        )
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone'}),
            'primary_city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Primary City'}),
        }

    picture = forms.FileField(required=False)

    def clean(self):
        cleaned_data = super(ExtraUserProfileForm, self).clean()
        return cleaned_data

    def clean_primary_city(self):
        primary_city = self.cleaned_data.get('primary_city')
        if len(primary_city) > 30:
            raise forms.ValidationError('The input is longer than 30 characters.')
        return primary_city


class BarbershopForm(forms.ModelForm):
    service_type = forms.MultipleChoiceField(choices=SERVICE_CHOICES)
    start_date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD",
                                       "pickTime": False}))
    end_date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD",
                                       "pickTime": False}))
    operation_start_time = forms.ChoiceField(choices=TIME_CHOICE_START)
    operation_end_time = forms.ChoiceField(choices=TIME_CHOICES_END)

    class Meta:
        model = Barbershop
        fields = ('name', 'phone', 'website', 'rating', 'description')
        exclude = (
            'picture_url',
            'rating'
        )
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Barbaershop name'}),
            'website': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Barbaershop website'}),
            'description': forms.Textarea(
                attrs={'rows': '4', 'column': '6', 'class': 'form-control', 'placeholder': 'Barbaershop description'}),
        }

    picture = forms.FileField(required=False)

    # the last to operate
    def clean(self):
        cleaned_data = super(BarbershopForm, self).clean()
        print self.cleaned_data
        return cleaned_data

    def clean_end_date(self):
        print self.cleaned_data
        start_date = self.cleaned_data.get('start_date')
        end_date = self.cleaned_data.get('end_date')  # would be none if use clean_start_date
        print start_date
        print end_date
        if start_date > end_date:
            raise forms.ValidationError('Start date is larger than end date.')
        return start_date

    def clean_operation_end_time(self):
        operation_start_time = self.cleaned_data.get('operation_start_time')
        print operation_start_time
        operation_end_time = self.cleaned_data.get('operation_end_time')
        print operation_end_time
        if operation_start_time > operation_end_time:
            raise forms.ValidationError('Operation start time is larger than operation end time.')
        return operation_start_time


class SearchForm(forms.Form):
    service_type = forms.ChoiceField(choices=SERVICE_CHOICES)
    date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD",
                                       "pickTime": False}))
    time = forms.ChoiceField(choices=TIME_CHOICES)
    city = forms.ChoiceField(choices=CITY_CHOICES)

    def clean(self):
        cleaned_data = super(SearchForm, self).clean()
        return cleaned_data
