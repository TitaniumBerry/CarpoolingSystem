from django.urls import path
from django.shortcuts import redirect
from . import views

urlpatterns = [
    path('', lambda request: redirect('/home')),
    path('signup', views.signup_view),
    path('login', views.login_view),
    path('logout', views.logout_view),
    path('home', views.home_view),
    path('trips', views.trip_list_view),
    path('trips/create', views.create_trip_view),
    path('trips/<int:trip_id>/cancel', views.cancel_trip_view),
    path('api/trips/<int:trip_id>/update-node', views.update_current_node),
    path('requests', views.request_list_view),
    path('requests/create', views.create_request_view),
    path('requests/<int:request_id>/cancel', views.cancel_request_view),
    path('requests/confirm/<int:offer_id>', views.confirm_offer_view),
    path('driver/requests', views.driver_requests_view),
    path('driver/requests/<int:request_id>/offer', views.make_offer_view),
    path('wallet', views.wallet_view),
    path('wallet/topup', views.topup_view),
    path('trips/<int:trip_id>/complete', views.complete_trip_view),
    path('rate/<int:trip_id>/<int:user_id>', views.rate_user_view),
    path('profile/<int:user_id>', views.profile_view),
    path('api/network-map', views.network_map_api),
]



