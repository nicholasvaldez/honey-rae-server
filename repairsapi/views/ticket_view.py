"""View module for handling requests for ticket data"""
from django.http import HttpResponseServerError
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import serializers, status
from repairsapi.models import ServiceTicket, Employee, Customer


class TicketView(ViewSet):
    """Honey Rae API tickets view"""

    def destroy(self, request, pk=None):
        """Handles DELETE requests for service tickets

        Returns:
            Response: None with 204 status code 
        """
        ticket = ServiceTicket.objects.get(pk=pk)
        ticket.delete()
        return Response(None, status=status.HTTP_204_NO_CONTENT)

    def create(self, request):
        """Handle POST requests for service tickets

        This method creates a new service ticket based on the incoming request data,
        saves it to the database, and returns a JSON serialized representation of
        the newly created ticket.

        Returns:
            Response: JSON serialized representation of newly created service ticket
        """
        new_ticket = ServiceTicket()
        new_ticket.customer = Customer.objects.get(user=request.auth.user)
        new_ticket.description = request.data['description']
        new_ticket.emergency = request.data['emergency']
        new_ticket.save()

        serialized = TicketSerializer(new_ticket, many=False)

        return Response(serialized.data, status=status.HTTP_201_CREATED)

    def list(self, request):
        """Handle GET requests to get all tickets

        This method returns a JSON serialized list of all service tickets based on
        the incoming request. The list can be filtered by the "status" query parameter,
        and the result depends on whether the user making the request is a staff member
        or a regular customer.

        Returns:
            Response -- JSON serialized list of tickets
        """

        service_tickets = []

        if request.auth.user.is_staff:
            # If the user is a staff member, retrieve all tickets
            service_tickets = ServiceTicket.objects.all()

            # If "status" is in the query parameters, filter the tickets based on the status
            if "status" in request.query_params:
                # If "status" is "done", return only completed tickets
                if request.query_params['status'] == "done":
                    service_tickets = service_tickets.filter(
                        date_completed__isnull=False)

                if request.query_params['status'] == "all":
                    # If "status" is "all", return all tickets (no filtering needed)
                    pass

        else:
            # If the user is not a staff member, retrieve only their own tickets
            service_tickets = ServiceTicket.objects.filter(
                customer__user=request.auth.user)

        serialized = TicketSerializer(service_tickets, many=True)
        return Response(serialized.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """Handle GET requests for single ticket

            Returns:
                Response -- JSON serialized ticket record
            """

        ticket = ServiceTicket.objects.get(pk=pk)
        serialized = TicketSerializer(ticket, context={'request': request})
        return Response(serialized.data, status=status.HTTP_200_OK)

    def update(self, request, pk=None):
        """Handles put requests for single customer 

        Returns:
            Response -- No response body. Just 204 status code.
        """
        ticket = ServiceTicket.objects.get(pk=pk)
        employee_id = request.data['employee']
        assigned_employee = Employee.objects.get(pk=employee_id)
        ticket.employee = assigned_employee
        ticket.save()
        return Response(None, status=status.HTTP_204_NO_CONTENT)


class TicketEmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ('id', 'specialty', 'full_name')


class TicketCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ('id', 'address', 'full_name')


class TicketSerializer(serializers.ModelSerializer):
    """JSON serializer for tickets"""

    employee = TicketEmployeeSerializer(many=False)
    customer = TicketCustomerSerializer(many=False)

    class Meta:
        model = ServiceTicket
        fields = ('id', 'description', 'emergency',
                  'date_completed', 'employee', 'customer', )
