from django import forms
from django.forms import inlineformset_factory

from customers.models import Customer
from products.models import Product

from .models import Invoice, InvoiceItem


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ["customer", "invoice_date"]

    def __init__(self, *args, business=None, **kwargs):
        super().__init__(*args, **kwargs)
        if business is not None:
            self.fields["customer"].queryset = Customer.objects.filter(business=business)
        else:
            self.fields["customer"].queryset = Customer.objects.all()


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ["product", "quantity"]

    def __init__(self, *args, business=None, **kwargs):
        self._business = business
        super().__init__(*args, **kwargs)
        if self._business is not None:
            self.fields["product"].queryset = Product.objects.filter(business=self._business)
        else:
            self.fields["product"].queryset = Product.objects.all()


InvoiceItemFormSet = inlineformset_factory(
    Invoice,
    InvoiceItem,
    form=InvoiceItemForm,
    extra=3,
    can_delete=False,
)
