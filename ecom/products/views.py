from django.shortcuts import render,redirect, get_object_or_404
from products.models import Contact,Product
from django.contrib import messages
from math import ceil
from django.contrib.auth.decorators import login_required
from .models import Product, CartItem
from django.http import JsonResponse
from .forms import CheckoutForm
# Create your views here.
def index(request):
    allProds = []
    catprods = Product.objects.values('category', 'id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prod = Product.objects.filter(category=cat)
        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        allProds.append([prod, range(1, nSlides), nSlides])
        params = {'allProds': allProds}
    return render(request, "index.html", params)


@login_required
def contact(request):
    if request.method == "POST":
        name =request.POST.get("name")
        email =request.POST.get("email")
        desc =request.POST.get("desc")
        phonenumber =request.POST.get("phonenumber")
        myquery = Contact(name=name,email=email,desc=desc,phonenumber=phonenumber)
        myquery.save()
        messages.info(request,"We will get back to you soon..")
    return render(request, 'contact.html')

def about(request):
    return render(request, 'about.html')



@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    
    if not created:
        cart_item.quantity += 1
    else:
        cart_item.quantity = 1  # Start from 1 for new items
    
    cart_item.save()
    
    response_data = {
        'quantity': cart_item.quantity,
        'message': 'Product added to cart',
    }
    
    return JsonResponse(response_data)

def remove_from_cart(request, product_id):
    cart_item = get_object_or_404(CartItem, user=request.user, product_id=product_id)
    cart_item.delete()

    # Recalculate total price after removal
    cart_items = CartItem.objects.filter(user=request.user)
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    response_data = {
        'success': True,
        'total_price': total_price
    }
    
    return JsonResponse(response_data)


def view_cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    
    # Pre-compute item totals and pass them to the template
    cart_items_with_totals = []
    total_price = 0
    for item in cart_items:
        item_total = item.product.price * item.quantity
        total_price += item_total
        cart_items_with_totals.append({
            'item': item,
            'item_total': item_total
        })

    return render(request, 'view_cart.html', {'cart_items': cart_items_with_totals, 'total_price': total_price})


@login_required
def update_cart(request, product_id, action):
    cart_item = get_object_or_404(CartItem, user=request.user, product_id=product_id)
    
    # Update the quantity based on the action
    if action == 'increase':
        cart_item.quantity += 1
    elif action == 'decrease' and cart_item.quantity > 1:
        cart_item.quantity -= 1
    cart_item.save()

    # Calculate the updated total price for the cart
    cart_items = CartItem.objects.filter(user=request.user)
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    # Send a JSON response with updated data
    response_data = {
        'success': True,
        'quantity': cart_item.quantity,
        'price': cart_item.product.price * cart_item.quantity,
        'total_price': total_price
    }
    
    return JsonResponse(response_data)

"""@login_required
def view_cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render(request, 'view_cart.html', {'cart_items': cart_items, 'total': total})"""

@login_required
def clear_cart(request):
    CartItem.objects.filter(user=request.user).delete()
    return redirect('view_cart')


def checkout(request):
    if not request.user.is_authenticated:
        messages.warning(request,"Login & Try Again")
        return redirect('/auth/login')
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # You can handle the form data here, e.g., save to the database
            # Redirect to the payment page (you can adjust the URL as needed)
            return redirect('payment')  # Assuming you have a payment page with this name
    else:
        form = CheckoutForm()
    
    return render(request, 'checkout.html', {'form': form})

# views.py
def payment_page(request):
    # Render the payment page
    return render(request, 'payment.html')
