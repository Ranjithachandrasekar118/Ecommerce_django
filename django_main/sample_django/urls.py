from django.urls import path
from . import views

urlpatterns=[
    path('login/',views.login_page,name='login'),
    path('logout/',views.logout_page,name='logout'),
    path('reg/',views.reg,name='reg'),
    path('',views.home,name='home'),
    path('collections/',views.collections,name="collections"),
    path('collections/<str:name>/',views.collectionsview,name="collections"),
    path('collections/<str:cname>/<str:pname>/',views.product_details,name="product_details"),
    path('addtocart/',views.add_to_cart,name="addtocart"),
    path('cart',views.view_cart,name="cart"),
    path('fav_page',views.fav_page,name="fav_page"),
    path('favourites/', views.favourites, name="favourites"),
    path('remove-from-favourites/<int:fav_id>/', views.remove_from_favourites, name="remove_from_favourites"),
    path('remove-from-cart/<int:item_id>/',views.remove_from_cart,name='remove_from_cart'),
    path('dashboard/',views.dashboard,name='dashboard'),
    path('update-profile/',views.update_profile,name='update_profile'),
    path('change-password/',views.change_password,name='change_password'),
    path('checkout/',views.checkout,name='checkout'),
    path('checkout/buy-now/<int:product_id>/<int:quantity>/',views.checkout_buy_now,name='checkout_buy_now'),
    path('order-confirmation/<int:order_id>/',views.order_confirmation,name='order_confirmation'),
    path('my-orders/',views.my_orders,name='my_orders'),
    path('feedback/', views.feedback, name='feedback'),
    path('feedback/thank-you/', views.feedback_thank_you, name='feedback_thank_you'),
    path('admin/feedback/', views.admin_feedback_list, name='admin_feedback_list'),
    path('admin/feedback/<int:feedback_id>/mark-read/', views.mark_feedback_read, name='mark_feedback_read'),
    path('order-feedback/<int:order_id>/', views.order_feedback, name='order_feedback')
]
