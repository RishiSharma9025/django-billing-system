from django import forms

from users.models import Business

from .models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "description", "price", "gst_rate", "stock_quantity"]

    def __init__(self, *args, show_business=False, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != "description":
                field.widget.attrs.setdefault("class", "form-control")
        self.fields["description"].widget.attrs.setdefault("class", "form-control")
        if show_business:
            self.fields["business"] = forms.ModelChoiceField(
                queryset=Business.objects.all().order_by("business_name"),
                required=True,
                label="Business",
            )
            self.fields["business"].widget.attrs.setdefault("class", "form-select")
