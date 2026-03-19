from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from .models import User, Node, Trip, TripNode, CarpoolRequest, CarpoolOffer, Wallet, Transaction, Rating
from .graph import bfs, is_within_2_nodes_of_route, calculate_fare, insert_passenger_into_route, optimize_route_for_passengers

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from allauth.account.signals import user_signed_up
from django.dispatch import receiver
from django.db.models import Avg
from django.http import JsonResponse


from decimal import Decimal

def signup_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        role = request.POST['role']

        if User.objects.filter(username=username).exists():
            return render(request, 'carpool/signup.html', {'error' : 'Username Already Exists'})
        
        user = User.objects.create_user(username=username, password=password, role=role)

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect("/home")
    
    return render(request, 'carpool/signup.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
    

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('/home')
        else:
            return render(request, 'carpool/login.html', {'error' : 'invalid credentials'})
    
    return render(request, 'carpool/login.html')

def logout_view(request):
    logout(request)
    return redirect('/login')


@login_required(login_url='/login')


def home_view(request):
    if request.user.is_driver():
        return render(request, 'carpool/driver_home.html')
    return render(request, 'carpool/passenger_home.html')


@login_required(login_url='/login')
def create_trip_view(request):
    if not request.user.is_driver():
        return redirect('/home')
    
    nodes = Node.objects.all()

    if request.method == 'POST':
        start_id = request.POST['start_node']
        end_id = request.POST['end_node']
        max_passengers = request.POST['max_passengers']

        start_node = Node.objects.get(id = start_id)
        end_node = Node.objects.get(id = end_id)

        route = bfs(start_node,  end_node)

        if route is None:
            return render(request, 'carpool/create_trip.html', {
                'nodes' : nodes,
                'error' : 'No route between these nodes'
            })
        
        trip = Trip.objects.create(
            driver=request.user,
            start_node=start_node,
            end_node=end_node,
            current_node=start_node,
            max_passengers=max_passengers
        )

        for i, node in enumerate(route):
            TripNode.objects.create(
                trip = trip,
                node = node,
                order = i,
                passed = False

            )

        return redirect('/trips')

    return render(request, 'carpool/create_trip.html', {'nodes' : nodes})


@login_required(login_url='/login')
def trip_list_view(request):
    if not request.user.is_driver():
        return redirect('/home')

    trips = Trip.objects.filter(driver=request.user).order_by('-created_at')
    return render(request, 'carpool/trip_list.html', {'trips': trips})


@login_required(login_url='/login')
def cancel_trip_view(request, trip_id):
    trip = Trip.objects.get(id=trip_id, driver=request.user)
    if trip.status == 'active':
        trip.status = 'cancelled'
        trip.save()
    return redirect('/trips')

@api_view(['POST'])
def update_current_node(request, trip_id):
    try:
        trip = Trip.objects.get(id=trip_id, driver=request.user)
    except Trip.DoesNotExist:
        return Response({'error': 'Trip not found'}, status=status.HTTP_404_NOT_FOUND)

    if trip.status != 'active':
        return Response({'error': 'Trip is not active'}, status=status.HTTP_400_BAD_REQUEST)

    node_id = request.data.get('node_id')
    if not node_id:
        return Response({'error': 'node_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        node = Node.objects.get(id=node_id)
    except Node.DoesNotExist:
        return Response({'error': 'Node not found'}, status=status.HTTP_404_NOT_FOUND)

    
    trip_node = TripNode.objects.filter(trip=trip, node=node).first()
    if not trip_node:
        return Response({'error': 'Node is not on this trip route'}, status=status.HTTP_400_BAD_REQUEST)

    
    TripNode.objects.filter(trip=trip, order__lte=trip_node.order).update(passed=True)

    
    trip.current_node = node

    if node == trip.end_node:
        trip.status = 'completed'
    trip.save()

    return Response({
        'message': 'Current node updated',
        'current_node': node.name,
        'trip_status': trip.status
    })


@login_required(login_url='/login')
def create_request_view(request):
    if not request.user.is_passenger():
        return redirect('/home')
    
    nodes = Node.objects.all()

    if request.method == 'POST':
        pickup_id = request.POST['pickup_node']
        dropoff_id = request.POST['dropoff_node']

        pickup_node = Node.objects.get(id=pickup_id)
        dropoff_node = Node.objects.get(id=dropoff_id)

        if pickup_node == dropoff_node:
            return render(request, 'carpool/create_request.html', {
                'nodes' : nodes,
                'error' : 'Pickup and dropoff cant be the same node'
            })
        
        carpool_request = CarpoolRequest.objects.create(
            passenger= request.user,
            pickup_node= pickup_node,
            dropoff_node= dropoff_node
        )

        return redirect('/requests')
    
    return render(request, 'carpool/create_request.html', {'nodes': nodes})


@login_required(login_url='/login')
def request_list_view(request):
    print("REQUEST LIST VIEW CALLED")
    if not request.user.is_passenger():
        return redirect('/home')

    
    requests = CarpoolRequest.objects.filter(passenger=request.user).order_by('-created_at')
    return render(request, 'carpool/request_list.html', {'requests' : requests})

@login_required(login_url='/login')
def cancel_request_view(request, request_id):
    carpool_request = CarpoolRequest.objects.get(id=request_id, passenger=request.user)
    if carpool_request.status == 'pending':
        carpool_request.status = 'cancelled'
        carpool_request.save()
    return redirect('/requests')

@login_required(login_url='/login')
def confirm_offer_view(request, offer_id):
    offer = CarpoolOffer.objects.get(id=offer_id)

    if offer.carpool_request.passenger != request.user:
        return redirect('/home')

    offer.status = 'accepted'
    offer.save()

    offer.carpool_request.status = 'confirmed'
    offer.carpool_request.save()

    CarpoolOffer.objects.filter(carpool_request= offer.carpool_request).exclude(id=offer_id).update(status='rejected')
    trip = offer.trip
    if trip.status == 'active':
        _optimize_trip_route(trip)

    return redirect('/requests')

def _optimize_trip_route(trip):
    accepted_offers = CarpoolOffer.objects.filter(
        trip = trip, status= 'accepted'
    ).select_related('carpool_request__pickup_node', 'carpool_request__dropoff_node')

    if accepted_offers.count() < 2:
        return
    
    passenger_stops = []

    for off in accepted_offers:
        passenger_stops.append((
            off.carpool_request.pickup_node,
            off.carpool_request.dropoff_node,
            off.id
        ))
    
    remaining_trip_nodes = TripNode.objects.filter(trip=trip, passed=False).select_related('node').order_by('order')

    if not remaining_trip_nodes.exists():
        return

    current_start = remaining_trip_nodes.first().node
    destination = trip.end_node

    optimized_route , optimized_order = optimize_route_for_passengers(current_start, destination, passenger_stops)

    if optimized_route is None:
        return
    
    passed_nodes = TripNode.objects.filter(trip = trip, passed= True)
    offset = passed_nodes.count()

    TripNode.objects.filter(trip = trip, passed= False).delete()

    for i, node in enumerate(optimized_route):
        TripNode.objects.create(trip = trip, node = node, order = offset + i, passed= False)
    



# @login_required(login_url='/login')
# def driver_requests_view(request):
#     if not request.user.is_driver():
#         return redirect('/home')

#     try:
#         trip = Trip.objects.filter(driver=request.user, status='active').order_by('-created_at').first()
#     except Trip.DoesNotExist:
#         return render(request, 'carpool/driver_requests.html', {
#             'error' : 'You have no active trip',
#             'incoming_requests' : [] 
#         })
    
#     remaining_trip_nodes = TripNode.objects.filter(trip=trip, passed=False).select_related('node')
#     remaining_nodes = [tn.node for tn in remaining_trip_nodes]

#     all_requests = CarpoolRequest.objects.filter(status='pending')

#     incoming_requests = []

#     for cr in all_requests:
#         pickup_ok = is_within_2_nodes(cr.pickup_node, remaining_nodes)
#         dropoff_ok = is_within_2_nodes(cr.dropoff_node, remaining_nodes)

#         if pickup_ok and dropoff_ok:
#             incoming_requests.append(cr)
    
#     return render(request, 'carpool/driver_requests.html', {'trip' : trip, 'incoming_requests' : incoming_requests})


@login_required(login_url='/login')
def make_offer_view(request, request_id):
    print("MAKE OFFER VIEW CALLED", request_id)
    if not request.user.is_driver():
        return redirect('/home')

    trip = Trip.objects.filter(driver=request.user, status='active').order_by('-created_at').first()
    if not trip:
        print("NO ACTIVE TRIP FOUND")
        return redirect('/home')

    carpool_request = CarpoolRequest.objects.get(id=request_id)

    remaining_trip_nodes = TripNode.objects.filter(trip=trip, passed=False).select_related('node')
    remaining_nodes = [tn.node for tn in remaining_trip_nodes]

    print("REMAINING NODES:", [n.name for n in remaining_nodes])
    print("PICKUP:", carpool_request.pickup_node)
    print("DROPOFF:", carpool_request.dropoff_node)

    new_route = insert_passenger_into_route(remaining_nodes, carpool_request.pickup_node, carpool_request.dropoff_node)

    print("NEW ROUTE:", new_route)

    if new_route is None:
        print("NEW ROUTE IS NONE - REDIRECTING")
        return redirect('/driver/requests')

    fare, detour = calculate_fare(
        remaining_nodes,
        new_route,
        carpool_request.pickup_node,
        carpool_request.dropoff_node
    )

    print("FARE:", fare, "DETOUR:", detour)


    existing_offer = CarpoolOffer.objects.filter(trip=trip, carpool_request=carpool_request).first()
    if existing_offer:
        return redirect('/driver/requests')


    CarpoolOffer.objects.create(
        trip=trip,
        carpool_request=carpool_request,
        detour_nodes=detour,
        fare=fare
    )

    return redirect('/driver/requests')

@login_required(login_url='/login')
def driver_requests_view(request):
    if not request.user.is_driver():
        return redirect('/home')

    try:
        trip = Trip.objects.filter(driver=request.user, status='active').order_by('-created_at').first()
    except Trip.DoesNotExist:
        return render(request, 'carpool/driver_requests.html', {
            'error': 'You have no active trip.',
            'incoming_requests': []
        })

    remaining_trip_nodes = TripNode.objects.filter(
        trip=trip, passed=False
    ).select_related('node')
    remaining_nodes = [tn.node for tn in remaining_trip_nodes]

    print("REMAINING NODES:", [n.name for n in remaining_nodes])

    all_requests = CarpoolRequest.objects.filter(status='pending')
    print("ALL PENDING REQUESTS:", list(all_requests))

    incoming_requests = []
    for cr in all_requests:
        pickup_ok = is_within_2_nodes_of_route(cr.pickup_node, remaining_nodes)
        dropoff_ok = is_within_2_nodes_of_route(cr.dropoff_node, remaining_nodes)
        print(f"Request {cr.id}: pickup={cr.pickup_node} ok={pickup_ok}, dropoff={cr.dropoff_node} ok={dropoff_ok}")
        if pickup_ok and dropoff_ok:
            incoming_requests.append(cr)

    return render(request, 'carpool/driver_requests.html', {
        'trip': trip,
        'incoming_requests': incoming_requests
    })



@receiver(user_signed_up)
def set_role_on_signup(sender, request, user, **kwargs):
    if not user.role:
        user.role = 'passenger'
        user.save()


@login_required(login_url='/login')
def wallet_view(request):
    wallet, created = Wallet.objects.get_or_create(user = request.user)
    transactions = Transaction.objects.filter(user = request.user).order_by('-created_at')
    return render(request, 'carpool/wallet.html', {
        'wallet' : wallet,
        'transactions' : transactions
    })

@login_required(login_url='/login')
def topup_view(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')
        try:
            amount = Decimal(amount)
            if amount <= 0:
                raise ValueError
        except(ValueError, TypeError):
            return redirect('/wallet')
        
        wallet, created = Wallet.objects.get_or_create(user= request.user)
        wallet.balance += amount
        wallet.save()

        Transaction.objects.create(
            user = request.user,
            transaction_type= Transaction.TOPUP,
            amount= amount,
            description = f'Wallet topup of ${amount}'
        )

        return redirect('/wallet')
    
    return redirect('/wallet')


@login_required(login_url='/login')
def complete_trip_view(request, trip_id):
    if not request.user.is_driver():
        return redirect('/home')
    
    trip = Trip.objects.get(id = trip_id, driver= request.user)

    if trip.status != 'active':
        return redirect('/trips')
    

    confirmed_offers = CarpoolOffer.objects.filter(
        trip = trip,
        status = 'accepted'
    ).select_related('carpool_request__passenger')

    for offer in confirmed_offers:
        passenger = offer.carpool_request.passenger
        fare = Decimal(str(offer.fare))

        passenger_wallet, _ = Wallet.objects.get_or_create(user = passenger)
        if passenger_wallet.balance < fare:
            return render(request, 'carpool/trip_list.html', {
                'trips' : Trip.objects.filter(driver=request.user).order_by('-created_at'),
                'error': f'Passenger {passenger.username} has insufficient balance to complete the trip!'
            })

    
    driver_wallet, _ = Wallet.objects.get_or_create(user = request.user)
    total_earnings = Decimal('0.00')

    for offer in confirmed_offers:
        passenger = offer.carpool_request.passenger
        fare = Decimal(str(offer.fare))

        passenger_wallet, _ = Wallet.objects.get_or_create(user = passenger)
        passenger_wallet.balance -= fare
        passenger_wallet.save()

        Transaction.objects.create(
            user = passenger,
            transaction_type= Transaction.FARE_DEDUCTION,
            amount= fare,
            trip = trip,
            description = f'Fare for trip {trip.id}'
        )

        total_earnings += fare
    
    driver_wallet.balance += total_earnings
    driver_wallet.save()

    Transaction.objects.create(
        user = request.user,
        transaction_type= Transaction.DRIVER_EARNING,
        amount = total_earnings,
        trip = trip,
        description = f'Earnings from trip {trip.id}'
    )

    trip.status = 'completed'
    trip.save()

    return redirect('/trips')

@login_required(login_url='/login')
def rate_user_view(request, trip_id, user_id):
    trip = Trip.objects.get(id=trip_id)
    ratee = User.objects.get(id=user_id)


    existing_rating = Rating.objects.filter(trip=trip, rater=request.user, ratee=ratee).first()
    if existing_rating:
        return redirect('/home')

    if request.method == 'POST':
        score = request.POST.get('score')
        comment = request.POST.get('comment', '')

        if not score or not score.isdigit() or not (1 <= int(score) <= 5):
            return render(request, 'carpool/rate_user.html', {
                'ratee': ratee,
                'trip': trip,
                'error': 'Please select a score between 1 and 5'
            })

        Rating.objects.create(
            trip=trip,
            rater=request.user,
            ratee=ratee,
            score=int(score),
            comment=comment
        )
        return redirect('/home')

    return render(request, 'carpool/rate_user.html', {
        'ratee': ratee,
        'trip': trip
    })


@login_required(login_url='/login')
def profile_view(request, user_id):
    profile_user = User.objects.get(id=user_id)
    ratings = Rating.objects.filter(ratee=profile_user).order_by('-created_at')
    avg_rating = ratings.aggregate(Avg('score'))['score__avg']
    return render(request, 'carpool/profile.html', {
        'profile_user': profile_user,
        'ratings': ratings,
        'avg_rating': round(avg_rating, 1) if avg_rating else None
    })


@login_required(login_url='/login')
def network_map_api(request):
    """Returns JSON with all nodes, edges, and active trip route for the map."""
    nodes = Node.objects.all()
    edges = Edge.objects.all().select_related('from_node', 'to_node')

    nodes_data = [{'id': n.id, 'name': n.name, 'lat': n.latitude, 'lng': n.longitude} for n in nodes]
    edges_data = [{'from': e.from_node.id, 'to': e.to_node.id} for e in edges]

    active_route = []
    active_trip_info = None
    pickup_dropoff_nodes = []

    if request.user.is_driver():
        trip = Trip.objects.filter(driver=request.user, status='active').order_by('-created_at').first()
        if trip:
            route_nodes = TripNode.objects.filter(trip=trip).select_related('node').order_by('order')
            active_route = [{'id': tn.node.id, 'name': tn.node.name, 'passed': tn.passed} for tn in route_nodes]
            active_trip_info = {
                'id': trip.id, 'start': trip.start_node.name, 'end': trip.end_node.name,
                'current_node': trip.current_node.id if trip.current_node else None,
            }
            for off in CarpoolOffer.objects.filter(trip=trip, status='accepted').select_related(
                'carpool_request__pickup_node', 'carpool_request__dropoff_node', 'carpool_request__passenger'
            ):
                pickup_dropoff_nodes.append({
                    'pickup_id': off.carpool_request.pickup_node.id,
                    'pickup_name': off.carpool_request.pickup_node.name,
                    'dropoff_id': off.carpool_request.dropoff_node.id,
                    'dropoff_name': off.carpool_request.dropoff_node.name,
                    'passenger': off.carpool_request.passenger.username,
                })

    elif request.user.is_passenger():
        confirmed_request = CarpoolRequest.objects.filter(
            passenger=request.user, status='confirmed'
        ).order_by('-created_at').first()
        if confirmed_request:
            accepted_offer = CarpoolOffer.objects.filter(
                carpool_request=confirmed_request, status='accepted'
            ).select_related('trip').first()
            if accepted_offer:
                trip = accepted_offer.trip
                route_nodes = TripNode.objects.filter(trip=trip).select_related('node').order_by('order')
                active_route = [{'id': tn.node.id, 'name': tn.node.name, 'passed': tn.passed} for tn in route_nodes]
                active_trip_info = {
                    'id': trip.id, 'start': trip.start_node.name, 'end': trip.end_node.name,
                    'current_node': trip.current_node.id if trip.current_node else None,
                }
                pickup_dropoff_nodes.append({
                    'pickup_id': confirmed_request.pickup_node.id,
                    'pickup_name': confirmed_request.pickup_node.name,
                    'dropoff_id': confirmed_request.dropoff_node.id,
                    'dropoff_name': confirmed_request.dropoff_node.name,
                    'passenger': request.user.username,
                })

    return JsonResponse({
        'nodes': nodes_data, 'edges': edges_data,
        'active_route': active_route, 'active_trip': active_trip_info,
        'passenger_stops': pickup_dropoff_nodes,
    })