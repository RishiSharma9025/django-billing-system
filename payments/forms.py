from django import forms

from invoices.models import Invoice

from .models import Payment


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["invoice", "payment_date", "amount_paid", "payment_method", "notes"]

    def __init__(self, *args, business=None, **kwargs):
        super().__init__(*args, **kwargs)
        for _, field in self.fields.items():
            field.widget.attrs.setdefault("class", "form-control")
        self.fields["invoice"].widget.attrs.setdefault("class", "form-select")
        if business is not None:
            self.fields["invoice"].queryset = Invoice.objects.filter(business=business)
        else:
            self.fields["invoice"].queryset = Invoice.objects.all()


class PaymentRecordForm(forms.ModelForm):
    """Payment for a fixed invoice (no invoice picker)."""

    class Meta:
        model = Payment
        fields = ["payment_date", "amount_paid", "payment_method", "notes"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _, field in self.fields.items():
            field.widget.attrs.setdefault("class", "form-control")
