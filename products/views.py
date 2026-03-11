from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProductForm
from .models import Product


@login_required
def product_list(request):
    query = request.GET.get("q", "").strip()
    products_qs = Product.objects.all()
    if query:
        products_qs = products_qs.filter(
            Q(name__icontains=query)
        )

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
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("products:product_list")
    else:
        form = ProductForm()

    return render(
        request,
        "products/product_form.html",
        {
            "form": form,
            "title": "Add Product",
        },
    )


@login_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect("products:product_list")
    else:
        form = ProductForm(instance=product)

    return render(
        request,
        "products/product_form.html",
        {
            "form": form,
            "title": "Edit Product",
        },
    )


@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
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

