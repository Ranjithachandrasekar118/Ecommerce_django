from django.contrib import admin
from .models import Catagory,Product,UserProfile,AddCart,Favourite,CustomerFeedback,Order,OrderItem


# class CategoryAdmin(admin.ModelAdmin):
    # list_display=('name','image','description')
# admin.site.register(Catagory,CategoryAdmin)
admin.site.register(Catagory)

admin.site.register(Product)
admin.site.register(AddCart)
admin.site.register(Favourite)
admin.site.register(CustomerFeedback)
admin.site.register(Order)
admin.site.register(OrderItem)



# admin.site.register(Register)


# Register your models here.
