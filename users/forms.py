from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Business


class BusinessOwnerRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    business_name = forms.CharField(max_length=150, label="Business name")
    business_type = forms.CharField(max_length=100, required=False, label="Business type")
    gst_number = forms.CharField(max_length=50, required=False, label="GST number")
    phone = forms.CharField(max_length=20, label="Phone")
    address = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), label="Address")
    city = forms.CharField(max_length=100, required=False)
    state = forms.CharField(max_length=100, required=False)
    pincode = forms.CharField(max_length=10, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name not in ("password1", "password2"):
                field.widget.attrs.setdefault("class", "form-control")
        self.fields["password1"].widget.attrs.setdefault("class", "form-control")
        self.fields["password2"].widget.attrs.setdefault("class", "form-control")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.is_active = False
        if commit:
            user.save()
            Business.objects.create(
                owner=user,
                business_name=self.cleaned_data["business_name"],
                business_type=self.cleaned_data.get("business_type") or "",
                gst_number=self.cleaned_data.get("gst_number") or "",
                phone=self.cleaned_data["phone"],
                email=self.cleaned_data["email"],
                address=self.cleaned_data.get("address") or "",
                city=self.cleaned_data.get("city") or "",
                state=self.cleaned_data.get("state") or "",
                pincode=self.cleaned_data.get("pincode") or "",
                status=Business.Status.PENDING,
            )
        return user
