from django.shortcuts import render
from rest_framework import viewsets
from .models import Server
from .serializer import ServerSerializer
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from django.db.models import Count

class ServerListViewSet(viewsets.ViewSet):

    queryset = Server.objects.all()

    def list(self, request):
        """
        List servers based on various query parameters.

        Args:
            request (HttpRequest): The HTTP request object.

        Returns:
            Response: A Response object containing serialized server data.

        Raises:
            AuthenticationFailed: If 'by_user' is set to 'true' but the user is not authenticated.
            ValidationError: If there are validation errors in the query parameters.

        Note:
            This view supports the following query parameters:
            
            - 'category': Filters servers by category name.
            - 'qty': Limits the number of servers returned.
            - 'by_user': Filters servers by the current authenticated user (if 'true').
            - 'by_serverid': Filters servers by a specific server ID.
            - 'with_num_members': Annotates the queryset with the number of members (if 'true').

        Example Usage:
            To list servers in a specific category with the number of members and limit the result to 10 servers:
            GET /servers/?category=gaming&with_num_members=true&qty=10

            To list servers owned by the currently authenticated user:
            GET /servers/?by_user=true

            To retrieve a server by its ID:
            GET /servers/?by_serverid=1234
        """
        category = request.query_params.get('cagetory')
        qty = request.query_params.get('qty')
        by_user = request.query_params.get('by_user') == 'true'
        by_serverid = request.query_params.get('by_serverid')
        with_num_members = request.query_params.get('with_num_members') == 'true'

        if by_user and not request.user.is_authenticated:
            raise AuthenticationFailed()

        if category:
            self.queryset = self.queryset.filter(category__name = category)

        if by_user:
            user_id = request.user.id
            self.queryset = self.queryset.filter(member = user_id)

        if with_num_members:
            self.queryset = self.queryset.annotate(num_members=Count('member'))
        
        if qty:
            self.queryset = self.queryset[:int(qty)]

        if by_serverid:
            try:
                self.queryset = self.queryset.filter(id=by_serverid)
                if not self.queryset.exists():
                    raise ValidationError(detail=f"Server with id{by_serverid} not found")
            except ValueError:
                raise ValidationError(detail="Server value error")
    
        serializer = ServerSerializer(self.queryset, many = True, context={"num_members":with_num_members})
        return Response(serializer.data)