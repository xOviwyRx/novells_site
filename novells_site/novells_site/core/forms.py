from django import forms
from .models import Comment, Profile, RatingStar, Rating


class CommentForm(forms.ModelForm):

    #Форма комментария
    class Meta:
        model = Comment
        fields = ('body',)


class EditProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('about', 'born_date', 'avatar', 'city', 'realname', 'sex')


class RatingForm(forms.ModelForm):
    rate = forms.ModelChoiceField(
        queryset=RatingStar.objects.all(), widget=forms.RadioSelect(), empty_label=None
    )

    class Meta:
        model = Rating
        fields = ('rate',)