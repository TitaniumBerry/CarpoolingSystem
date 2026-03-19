from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Node, Edge, Trip, TripNode, CarpoolRequest, CarpoolOffer, Wallet, Transaction, Rating

admin.site.register(Rating)
admin.site.register(User, UserAdmin)
admin.site.register(Node)
admin.site.register(Edge)
admin.site.register(Trip)
admin.site.register(TripNode)
admin.site.register(CarpoolRequest)
admin.site.register(CarpoolOffer)
admin.site.register(Wallet)
admin.site.register(Transaction)



# Register your models here.
