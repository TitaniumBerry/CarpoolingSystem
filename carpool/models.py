from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    PASSENGER = "passenger"
    DRIVER = "driver"
    ROLE_CHOICES = [
        (PASSENGER, "passenger"),
        (DRIVER, "driver")
    ]

    role = models.CharField(max_length = 20, choices = ROLE_CHOICES, default = PASSENGER)

    def is_driver(self):
        return self.role == self.DRIVER 
    
    def is_passenger(self):
        return self.role == self.PASSENGER


class Node(models.Model):
    name = models.CharField(max_length = 100, unique = True)
    latitude = models.FloatField(null = True, blank = True)
    longitude = models.FloatField(null = True, blank = True)

    def __str__(self):
        return self.name

    
class Edge(models.Model):
    from_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name="outgoing_edges")
    to_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name="incoming_edges")

    class Meta:
        unique_together = ("from_node", "to_node")

    def __str__(self):
        return f"{self.from_node} -> {self.to_node}"



class Trip(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_COMPLETED, 'Completed')
    ]

    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trips')
    start_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='trips_starting')
    end_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='trips_ending')
    current_node = models.ForeignKey(Node, on_delete=models.SET_NULL, null= True, blank= True, related_name='current_trips')
    max_passengers = models.PositiveIntegerField(default = 3)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Trip by {self.driver} ({self.start_node} -> {self.end_node})"
    

class TripNode(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='route_nodes')
    node = models.ForeignKey(Node, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()
    passed = models.BooleanField(default=False)

    class Meta:
        ordering = ['order']
        unique_together = ('trip', 'order')
    
    def __str__(self):
        return f"{self.trip} - Step {self.order} : {self.node}"
    


class CarpoolRequest(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_CANCELLED, 'Cancelled')
    ]

    passenger = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carpool_requests')
    pickup_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='pickup_requests')
    dropoff_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='dropoff_requests')
    status = models.CharField(max_length= 20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Request by {self.passenger} ({self.pickup_node} -> {self.dropoff_node})"
    
class CarpoolOffer(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_REJECTED, 'Rejected')
    ]

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='offers')
    carpool_request = models.ForeignKey(CarpoolRequest, on_delete=models.CASCADE, related_name='offers')
    detour_nodes = models.PositiveIntegerField()
    fare = models.DecimalField(max_digits=6, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    def __str__(self):
        return f"Offer from {self.trip.driver} for {self.carpool_request}"



class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f"{self.user.username}'s wallet - ${self.balance}"

class Transaction(models.Model):
    TOPUP = 'topup'
    FARE_DEDUCTION = 'fare_deduction'
    DRIVER_EARNING = 'driver_earning'
    TYPE_CHOICES = [
        (TOPUP, 'Top Up'),
        (FARE_DEDUCTION, 'Fare Deduction'),
        (DRIVER_EARNING, 'Driver Earning'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    trip = models.ForeignKey(Trip, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    created_at = models.DateTimeField(auto_now_add=True) 
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - ${self.amount}"
    





        
    


    
