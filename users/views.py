from django.db import connection
from django.http import JsonResponse
from django.views import View
import json
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# REGISTER
class RegisterView(View):
    def post(self, request):
        data = json.loads(request.body)

        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        phone = data.get('phone', '')
        address = data.get('address', '')

        if not username or not email or not password:
            return JsonResponse({'error': 'username, email, password required'}, status=400)

        if len(password) < 8:
            return JsonResponse({'error': 'password minimum 8 characters'}, status=400)

        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE email = %s", [email])
            existing = cursor.fetchone()

            if existing:
                return JsonResponse({'error': 'Email already registered'}, status=400)

            cursor.execute("""
                INSERT INTO users (username, email, password, phone, address)
                VALUES (%s, %s, %s, %s, %s)
            """, [username, email, hash_password(password), phone, address])

        return JsonResponse({'message': 'User registered successfully'}, status=201)


# GET ALL USERS
class UserListView(View):
    def get(self, request):
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, username, email, phone, address, created_at FROM users")
            rows = cursor.fetchall()

        users = []
        for row in rows:
            users.append({
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'phone': row[3],
                'address': row[4],
                'created_at': str(row[5])
            })

        return JsonResponse({'users': users})


# GET SINGLE USER
class UserDetailView(View):
    def get(self, request, user_id):
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, username, email, phone, address, created_at
                FROM users WHERE id = %s
            """, [user_id])
            row = cursor.fetchone()

        if not row:
            return JsonResponse({'error': 'User not found'}, status=404)

        return JsonResponse({
            'id': row[0],
            'username': row[1],
            'email': row[2],
            'phone': row[3],
            'address': row[4],
            'created_at': str(row[5])
        })


# UPDATE USER
class UserUpdateView(View):
    def put(self, request, user_id):
        data = json.loads(request.body)

        phone = data.get('phone')
        address = data.get('address')

        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE id = %s", [user_id])
            existing = cursor.fetchone()

        if not existing:
            return JsonResponse({'error': 'User not found'}, status=404)

        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE users SET phone = %s, address = %s WHERE id = %s
            """, [phone, address, user_id])

        return JsonResponse({'message': 'User updated successfully'})


# DELETE USER
class UserDeleteView(View):
    def delete(self, request, user_id):
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE id = %s", [user_id])
            existing = cursor.fetchone()

        if not existing:
            return JsonResponse({'error': 'User not found'}, status=404)

        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM users WHERE id = %s", [user_id])

        return JsonResponse({'message': 'User deleted successfully'})