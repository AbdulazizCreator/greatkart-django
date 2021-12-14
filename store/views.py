from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from orders.models import OrderProduct
from .forms import ReviewForm
from .models import Product, ReviewRating, ProductGallery
from category.models import Category
from carts.models import CartItem
from carts.views import _cart_id
from django.core.paginator import Paginator
from django.db.models import Q


def store(request, category_slug=None):
    categories = None
    products = None

    if category_slug is not None:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.all().filter(category=categories, is_available=True)
    else:
        products = Product.objects.all().filter(is_available=True).order_by("id")

    paginator = Paginator(products, 4)
    page = request.GET.get("page")
    paged_products = paginator.get_page(page)
    product_count = products.count()

    context = {"products": paged_products, "product_count": product_count}

    return render(request, "store/store.html", context)


def product_detail(request, category_slug, product_slug):
    try:
        single_product = get_object_or_404(
            Product, category__slug=category_slug, slug=product_slug
        )
        in_cart = CartItem.objects.filter(
            cart__cart_id=_cart_id(request), product=single_product
        ).exists()
    except Exception as e:
        raise e

    try:
        if request.user.is_authenticated:
            is_ordered_product = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
        else:
            is_ordered_product = None
    except OrderProduct.DoesNotExist:
        is_ordered_product = None

    # Get reviews
    reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True)

    # Get the product gallery
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)

    context = \
        {"single_product": single_product,
         "in_cart": in_cart,
         'reviews': reviews,
         'range': list(range(1, 6)),
         'is_ordered_product': is_ordered_product,
         'product_gallery': product_gallery
         }

    return render(request, "store/product_detail.html", context)


def search(request):
    products = None
    product_count = 0
    if "keyword" in request.GET:
        keyword = request.GET["keyword"]
        if keyword:
            products = Product.objects.order_by("-created_date").filter(
                Q(description__icontains=keyword) | Q(product_name__icontains=keyword)
            )
            product_count = products.count()

    context = {"products": products, "product_count": product_count}
    return render(request, "store/store.html", context)


def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')

    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, 'Thank you ! Your review has been updated.')
            return redirect(url)

        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()

                messages.success(request, 'Thank you ! Your review has been submitted.')
                return redirect(url)


def apply_sort(request):
    products = None
    product_count = 0
    if "min_price" and 'max_price' in request.GET:
        min_price = request.GET["min_price"]
        max_price = request.GET["max_price"]
        products = Product.objects.all().filter(price__range=(min_price, max_price))
        # if min_price > max_price:
        #     messages.error(request, 'Max price should be larger than min price !')
        #     return redirect('store')
    context = {"products": products, "product_count": product_count}
    return render(request, 'store/store.html', context)
