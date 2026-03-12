from django import forms

from .models import BusinessRegistrationRequest


class BusinessRegistrationRequestForm(forms.ModelForm):
    class Meta:
        model = BusinessRegistrationRequest
        fields = [
            "full_name",
            "email",
            "phone",
            "business_name",
            "business_type",
            "business_address",
            "gst_number",
            "city",
            "state",
            "pincode",
        ]
        widgets = {
            "business_address": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "form-check-input")
            else:
                field.widget.attrs.setdefault("class", "form-control")

