from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from users.decorators import approved_business_required
from users.utils import get_owner_business, is_staff_or_superuser, queryset_for_business

from .forms import CustomerForm
from .models import Customer


@login_required
@approved_business_required
def customer_list(request):
    query = request.GET.get("q", "").strip()
    customers_qs = queryset_for_business(Customer.objects.all(), request.user)
    if query:
        customers_qs = customers_qs.filter(
            Q(name__icontains=query)
            | Q(phone__icontains=query)
            | Q(email__icontains=query)
        )

    paginator = Paginator(customers_qs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "customers/customer_list.html",
        {
            "page_obj": page_obj,
            "query": query,
        },
    )


@login_required
@approved_business_required
def customer_create(request):
    show_business = is_staff_or_superuser(request.user)
    if request.method == "POST":
        form = CustomerForm(request.POST, show_business=show_business)
        if form.is_valid():
            customer = form.save(commit=False)
            if not show_business:
                customer.business = get_owner_business(request.user)
            customer.save()
            return redirect("customers:customer_list")
    else:
        form = CustomerForm(show_business=show_business)

    return render(
        request,
        "customers/customer_form.html",
        {
            "form": form,
            "title": "Add Customer",
        },
    )


@login_required
@approved_business_required
def customer_update(request, pk):
    customers_qs = queryset_for_business(Customer.objects.all(), request.user)
    customer = get_object_or_404(customers_qs, pk=pk)
    show_business = is_staff_or_superuser(request.user)
    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer, show_business=show_business)
        if form.is_valid():
            form.save()
            return redirect("customers:customer_list")
    else:
        form = CustomerForm(instance=customer, show_business=show_business)

    return render(
        request,
        "customers/customer_form.html",
        {
            "form": form,
            "title": "Edit Customer",
        },
    )


@login_required
@approved_business_required
def customer_delete(request, pk):
    customers_qs = queryset_for_business(Customer.objects.all(), request.user)
    customer = get_object_or_404(customers_qs, pk=pk)
    if request.method == "POST":
        customer.delete()
        return redirect("customers:customer_list")

    return render(
        request,
        "customers/customer_confirm_delete.html",
        {
            "customer": customer,
        },
    )
