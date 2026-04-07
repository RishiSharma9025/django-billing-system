from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from users.decorators import approved_business_required
from users.utils import get_owner_business, is_staff_or_superuser, queryset_for_business

from .forms import ProductForm
from .models import Product


@login_required
@approved_business_required
def product_list(request):
    query = request.GET.get("q", "").strip()
    products_qs = queryset_for_business(Product.objects.all(), request.user)
    if query:
        products_qs = products_qs.filter(Q(name__icontains=query))

    paginator = Paginator(products_qs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "products/product_list.html",
        {
            "page_obj": page_obj,
            "query": query,
        },
    )


@login_required
@approved_business_required
def product_create(request):
    show_business = is_staff_or_superuser(request.user)
    if request.method == "POST":
        form = ProductForm(request.POST, show_business=show_business)
        if form.is_valid():
            product = form.save(commit=False)
            if not show_business:
                product.business = get_owner_business(request.user)
            product.save()
            return redirect("products:product_list")
    else:
        form = ProductForm(show_business=show_business)

    return render(
        request,
        "products/product_form.html",
        {
            "form": form,
            "title": "Add Product",
        },
    )


@login_required
@approved_business_required
def product_update(request, pk):
    products_qs = queryset_for_business(Product.objects.all(), request.user)
    product = get_object_or_404(products_qs, pk=pk)
    show_business = is_staff_or_superuser(request.user)
    if request.method == "POST":
        form = ProductForm(request.POST, instance=product, show_business=show_business)
        if form.is_valid():
            form.save()
            return redirect("products:product_list")
    else:
        form = ProductForm(instance=product, show_business=show_business)

    return render(
        request,
        "products/product_form.html",
        {
            "form": form,
            "title": "Edit Product",
        },
    )


@login_required
@approved_business_required
def product_delete(request, pk):
    products_qs = queryset_for_business(Product.objects.all(), request.user)
    product = get_object_or_404(products_qs, pk=pk)
    if request.method == "POST":
        product.delete()
        return redirect("products:product_list")

    return render(
        request,
        "products/product_confirm_delete.html",
        {
            "product": product,
        },
    )
