from django import forms

from users.models import Business

from .models import Customer


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["name", "phone", "email", "address", "gst_number"]

    def __init__(self, *args, show_business=False, **kwargs):
        super().__init__(*args, **kwargs)
        for _, field in self.fields.items():
            field.widget.attrs.setdefault("class", "form-control")
        if show_business:
            self.fields["business"] = forms.ModelChoiceField(
                queryset=Business.objects.all().order_by("business_name"),
                required=True,
                label="Business",
            )
            self.fields["business"].widget.attrs.setdefault("class", "form-select")
