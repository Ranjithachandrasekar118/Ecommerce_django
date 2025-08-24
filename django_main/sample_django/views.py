from django.shortcuts import render, redirect, HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
import json
from django.utils import timezone

from sample_django.Register import CustomUserForm
from .models import Catagory, Product, UserProfile, AddCart, Order, OrderItem, Favourite, CustomerFeedback


def home(request):
    # Get all active products (status=0)
    products = Product.objects.filter(status=0)
    # Get trending products specifically
    trending_products = Product.objects.filter(trending=1, status=0)
    return render(request,'shop/home.html',{
        'products': products,
        'trending_products': trending_products
    })

def add_to_cart(request):
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        if request.user.is_authenticated:
            try:
                data = json.loads(request.body)
                quantity = int(data.get("product_qty", 1))
                product_id = int(data.get("pid"))
                
                product = Product.objects.get(id=product_id)
                
                # Check if already in cart
                if AddCart.objects.filter(user=request.user, product=product).exists():
                    return JsonResponse({"status": "Product already in cart"}, status=200)
                
                if product.quantity >= quantity:
                    AddCart.objects.create(
                        user=request.user,
                        product=product,
                        quantity=quantity
                    )
                    return JsonResponse({"status": "Product added to cart"}, status=200)
                else:
                    return JsonResponse({"status": "Not enough stock"}, status=200)
                    
            except Product.DoesNotExist:
                return JsonResponse({"status": "Product not found"}, status=404)
            except (ValueError, json.JSONDecodeError):
                return JsonResponse({"status": "Invalid data"}, status=400)
        else:
            return JsonResponse({"status": "Login to add to cart"}, status=403)
    
    return JsonResponse({"status": "Invalid access"}, status=400)

def reg(request):
    form = CustomUserForm()
    if request.method == 'POST':
        form = CustomUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create UserProfile with contact number
            contact_number = form.cleaned_data.get('contact_number')
            UserProfile.objects.create(
                user=user,
                contact_number=contact_number
            )
            messages.success(request, "Registration Success you can login now")
            return redirect('/login/')
        
    return render(request, "shop/register.html", {'form': form})

def login_page(request):
    if request.user.is_authenticated:
        return redirect('/')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, "Logged in Success")
            return redirect('/')
        else:
            messages.error(request, "Invalid User Name or Password")
            return redirect('/login')
    
    return render(request, "shop/login.html")

def logout_page(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "Logged out Successfully")
    return redirect('/')

def collections(request):
    catagory = Catagory.objects.filter(status=0)
    return render(request, "shop/collections.html", {"catagory": catagory})

def collectionsview(request, name):
    if Catagory.objects.filter(name=name, status=0).exists():
        products = Product.objects.filter(category__name=name)
        return render(request, "shop/products/index.html", {"products": products, "category_name": name})
    else:
        messages.warning(request, "No Such Catagory Found")
        return redirect('collections')

def product_details(request, cname, pname):
    if Catagory.objects.filter(name=cname, status=0).exists():
        product = Product.objects.filter(name=pname, status=0).first()
        if product:
            return render(request, "shop/products/productdetails.html", {"products": product})
        else:
            messages.error(request, "No such product found")
            return redirect('collections')
    else:
        messages.error(request, "No such catagory Found")
        return redirect('collections')

def view_cart(request):
    if request.user.is_authenticated:
        cart = AddCart.objects.filter(user=request.user)
        return render(request, "shop/cart.html", {"cart": cart})
    else:
        return redirect('/login')

def remove_from_cart(request, item_id):
    if request.user.is_authenticated:
        try:
            cart_item = AddCart.objects.get(id=item_id, user=request.user)
            cart_item.delete()
            messages.success(request, "Item removed from cart successfully!")
        except AddCart.DoesNotExist:
            messages.error(request, "Item not found in your cart!")
    return redirect('cart')

def dashboard(request):
    if not request.user.is_authenticated:
        messages.warning(request, "Please login to access your dashboard")
        return redirect('login')
    
    return render(request, "shop/dashboard.html")

def update_profile(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.method == 'POST':
        user = request.user
        user.email = request.POST.get('email', '')
        
        # Update contact number in UserProfile
        contact_number = request.POST.get('contact_number', '')
        user_profile, created = UserProfile.objects.get_or_create(user=user)
        user_profile.contact_number = contact_number
        user_profile.save()
        
        user.save()
        messages.success(request, "Profile updated successfully!")
    
    return redirect('dashboard')

def change_password(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Password changed successfully!")
        else:
            messages.error(request, "Please correct the errors below.")
    
    return redirect('dashboard')

def checkout(request):
    """Handle checkout from cart"""
    if not request.user.is_authenticated:
        messages.warning(request, "Please login to proceed with checkout")
        return redirect('login')
    
    if request.method == 'POST':
        # Handle checkout from cart
        cart_items = AddCart.objects.filter(user=request.user)
        if not cart_items:
            messages.warning(request, "Your cart is empty")
            return redirect('cart')
        
        shipping_address = request.POST.get('shipping_address', '')
        if not shipping_address:
            messages.error(request, "Please provide a shipping address")
            return redirect('checkout')
        
        # Validate that shipping address contains at least one special character
        import re
        if not re.search(r'[,.\-/#@&()]', shipping_address):
            messages.error(request, "Shipping address must contain at least one special character: , . - / # @ & ( )")
            return redirect('checkout')
        
        total_amount = sum(item.product.selling * item.quantity for item in cart_items)
        
        order_number = f"ORD-{request.user.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        order = Order.objects.create(
            user=request.user,
            order_number=order_number,
            total_amount=total_amount,
            shipping_address=shipping_address,
            status='pending'
        )
        
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.selling
            )
            
            item.product.quantity -= item.quantity
            item.product.save()
        
        cart_items.delete()
        
        messages.success(request, f"Order #{order_number} placed successfully!")
        return redirect('order_confirmation', order_id=order.id)
    
    cart_items = AddCart.objects.filter(user=request.user)
    if not cart_items:
        messages.warning(request, "Your cart is empty")
        return redirect('cart')
    
    total_amount = sum(item.product.selling * item.quantity for item in cart_items)
    context = {
        'cart_items': cart_items,
        'total_amount': total_amount,
        'is_buy_now': False,
    }
    
    return render(request, 'shop/checkout.html', context)

def checkout_buy_now(request, product_id, quantity):
    """Handle direct buy now checkout"""
    if not request.user.is_authenticated:
        messages.warning(request, "Please login to proceed with checkout")
        return redirect('login')
    
    try:
        product = Product.objects.get(id=product_id)
        
        if request.method == 'POST':
            # Get customer information and payment method
            customer_name = request.POST.get('customer_name', '')
            customer_email = request.POST.get('customer_email', '')
            customer_contact = request.POST.get('customer_contact', '')
            payment_method = request.POST.get('payment_method', 'cash_on_delivery')
            shipping_address = request.POST.get('shipping_address', '')
            
            # Validate required fields
            if not all([customer_name, customer_email, customer_contact, shipping_address]):
                messages.error(request, "Please fill in all required fields")
                return redirect('checkout_buy_now', product_id=product_id, quantity=quantity)
            
            # Validate that contact number is exactly 10 digits
            import re
            if not re.match(r'^[0-9]{10}$', customer_contact):
                messages.error(request, "Contact number must be exactly 10 digits")
                return redirect('checkout_buy_now', product_id=product_id, quantity=quantity)
            
            # Validate that shipping address contains at least one special character
            if not re.search(r'[,.\-/#@&()]', shipping_address):
                messages.error(request, "Shipping address must contain at least one special character: , . - / # @ & ( )")
                return redirect('checkout_buy_now', product_id=product_id, quantity=quantity)
            
            quantity = int(quantity)
            if product.quantity >= quantity:
                order_number = f"ORD-{request.user.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
                total_amount = product.selling * quantity
                
                order = Order.objects.create(
                    user=request.user,
                    order_number=order_number,
                    total_amount=total_amount,
                    customer_name=customer_name,
                    customer_email=customer_email,
                    customer_contact=customer_contact,
                    payment_method=payment_method,
                    shipping_address=shipping_address,
                    status='pending'
                )
                
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=product.selling
                )
                
                product.quantity -= quantity
                product.save()
                
                messages.success(request, f"Order #{order_number} placed successfully!")
                return redirect('order_confirmation', order_id=order.id)

            else:
                messages.error(request, "Not enough stock available")
                return redirect('product_details', cname=product.category.name, pname=product.name)
                
    except Product.DoesNotExist:
        messages.error(request, "Product not found")
        return redirect('home')
    
    # Pre-fill user information if available
    customer_name = request.user.get_full_name() or request.user.username
    customer_email = request.user.email
    customer_contact = ''
    
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        customer_contact = user_profile.contact_number or ''
    except UserProfile.DoesNotExist:
        pass
    
    total_amount = product.selling * int(quantity)
    context = {
        'product': product,
        'quantity': int(quantity),
        'total_amount': total_amount,
        'is_buy_now': True,
        'customer_name': customer_name,
        'customer_email': customer_email,
        'customer_contact': customer_contact,
        'payment_methods': Order.PAYMENT_METHOD_CHOICES,
    }
    
    return render(request, 'shop/checkout.html', context)

def order_confirmation(request, order_id):
    if not request.user.is_authenticated:
        messages.warning(request, "Please login to view your order")
        return redirect('login')
    
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        order_items = OrderItem.objects.filter(order=order)
        
        context = {
            'order': order,
            'order_items': order_items,
        }
        
        return render(request, 'shop/order_confirmation.html', context)
        
    except Order.DoesNotExist:
        messages.error(request, "Order not found")
        return redirect('dashboard')

def my_orders(request):
    if not request.user.is_authenticated:
        messages.warning(request, "Please login to view your orders")
        return redirect('login')
    
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shop/my_orders.html', {'orders': orders})

def fav_page(request):
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        if request.user.is_authenticated:
            try:
                data = json.loads(request.body)
                product_id = int(data.get("pid"))
                
                product = Product.objects.get(id=product_id)
                
                # Check if already in favourites
                if Favourite.objects.filter(user=request.user, product=product).exists():
                    return JsonResponse({"status": "Product already in favourites"}, status=200)
                
                Favourite.objects.create(
                    user=request.user,
                    product=product
                )
                return JsonResponse({"status": "Product added to favourites"}, status=200)
                    
            except Product.DoesNotExist:
                return JsonResponse({"status": "Product not found"}, status=404)
            except (ValueError, json.JSONDecodeError):
                return JsonResponse({"status": "Invalid data"}, status=400)
        else:
            return JsonResponse({"status": "Login to add to favourites"}, status=403)
    
    return JsonResponse({"status": "Invalid access"}, status=400)

@login_required
def favourites(request):
    """Display user's favourite products"""
    if not request.user.is_authenticated:
        messages.warning(request, "Please login to view your favourites")
        return redirect('login')
    
    favourites = Favourite.objects.filter(user=request.user).select_related('product', 'product__category')
    return render(request, 'shop/favourite.html', {'favourites': favourites})

@login_required
def remove_from_favourites(request, fav_id):
    """Remove a product from user's favourites"""
    if not request.user.is_authenticated:
        messages.warning(request, "Please login to modify your favourites")
        return redirect('login')
    
    try:
        favourite = Favourite.objects.get(id=fav_id, user=request.user)
        product_name = favourite.product.name
        favourite.delete()
        messages.success(request, f"{product_name} removed from favourites successfully!")
    except Favourite.DoesNotExist:
        messages.error(request, "Favourite item not found")
    
    return redirect('favourites')

    
    
    


def feedback(request):
    """Handle customer feedback form"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        rating = request.POST.get('rating', 5)
        
        # Optional: link to product/order if provided
        product_id = request.POST.get('product_id')
        order_id = request.POST.get('order_id')
        
        feedback = CustomerFeedback.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message,
            rating=int(rating)
        )
        
        # Link to product if provided
        if product_id:
            try:
                product = Product.objects.get(id=product_id)
                feedback.product = product
            except Product.DoesNotExist:
                pass
        
        # Link to order if provided
        if order_id and request.user.is_authenticated:
            try:
                order = Order.objects.get(id=order_id, user=request.user)
                feedback.order = order
            except Order.DoesNotExist:
                pass
        
        feedback.save()
        
        messages.success(request, "Thank you for your feedback! We'll get back to you soon.")
        return redirect('feedback_thank_you')
    
    # Get products for dropdown
    products = Product.objects.filter(status=0)
    
    # Get user's recent orders for linking
    user_orders = []
    if request.user.is_authenticated:
        user_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    context = {
        'products': products,
        'user_orders': user_orders,
    }
    
    return render(request, 'shop/feedback.html', context)

def feedback_thank_you(request):
    """Thank you page after feedback submission"""
    return render(request, 'shop/feedback_thank_you.html')

def admin_feedback_list(request):
    """Admin view to see all feedback"""
    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, "You don't have permission to view this page")
        return redirect('home')
    
    feedback_list = CustomerFeedback.objects.all()
    unread_count = feedback_list.filter(is_read=False).count()
    
    context = {
        'feedback_list': feedback_list,
        'unread_count': unread_count,
    }
    
    return render(request, 'shop/admin_feedback.html', context)

def mark_feedback_read(request, feedback_id):
    """Mark feedback as read"""
    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, "You don't have permission to perform this action")
        return redirect('home')
    
    try:
        feedback = CustomerFeedback.objects.get(id=feedback_id)
        feedback.is_read = True
        feedback.save()
        messages.success(request, "Feedback marked as read")
    except CustomerFeedback.DoesNotExist:
        messages.error(request, "Feedback not found")
    
    return redirect('admin_feedback_list')

@login_required
def order_feedback(request, order_id):
    """Handle feedback specifically for an order"""
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        messages.error(request, "Order not found or you don't have permission to leave feedback for this order.")
        return redirect('my_orders')
    
    if request.method == 'POST':
        name = request.POST.get('name', request.user.get_full_name() or request.user.username)
        email = request.POST.get('email', request.user.email)
        subject = request.POST.get('subject', f'Feedback for Order #{order.order_number}')
        message = request.POST.get('message')
        rating = request.POST.get('rating', 5)
        
        if not message:
            messages.error(request, "Please provide your feedback message.")
            return render(request, 'shop/feedback.html', {
                'order': order,
                'preselected_order': order,
            })
        
        feedback = CustomerFeedback.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message,
            rating=int(rating),
            order=order
        )
        
        messages.success(request, "Thank you for your feedback about your order! We'll review it shortly.")
        return redirect('feedback_thank_you')
    
    # Get products from this order for dropdown
    order_products = []
    for item in order.items.all():  # Fixed: using correct related_name 'items'
        order_products.append(item.product)
    
    context = {
        'order': order,
        'preselected_order': order,
        'order_products': order_products,
        'products': Product.objects.filter(status=0),
        'user_orders': Order.objects.filter(user=request.user).order_by('-created_at')[:5],
    }
    
    return render(request, 'shop/feedback.html', context)
