from django.db import connection
from django.http import JsonResponse
from django.views import View
import json
import hashlib
import jwt
import datetime
from django.conf import settings


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),
        'iat': datetime.datetime.utcnow()
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    return token


def verify_token(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None

    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


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

            cursor.execute("SELECT id FROM users WHERE email = %s", [email])
            user = cursor.fetchone()

        token = generate_token(user[0])

        return JsonResponse({
            'message': 'User registered successfully',
            'token': token,
            'user_id': user[0]
        }, status=201)


# LOGIN
class LoginView(View):
    def post(self, request):
        data = json.loads(request.body)

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return JsonResponse({'error': 'email and password required'}, status=400)

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, username, email FROM users 
                WHERE email = %s AND password = %s
            """, [email, hash_password(password)])
            user = cursor.fetchone()

        if not user:
            return JsonResponse({'error': 'Invalid email or password'}, status=401)

        token = generate_token(user[0])

        return JsonResponse({
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': user[0],
                'username': user[1],
                'email': user[2]
            }
        })


# PROFILE - sirf authenticated user dekh sakta hai
class ProfileView(View):
    def get(self, request):
        user_id = verify_token(request)
        if not user_id:
            return JsonResponse({'error': 'Invalid or expired token'}, status=401)

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

    def put(self, request):
        user_id = verify_token(request)
        if not user_id:
            return JsonResponse({'error': 'Invalid or expired token'}, status=401)

        data = json.loads(request.body)
        phone = data.get('phone')
        address = data.get('address')

        if not phone and not address:
            return JsonResponse({'error': 'phone ya address dono mein se kuch toh do'}, status=400)

        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE users SET phone = %s, address = %s WHERE id = %s
            """, [phone, address, user_id])

        return JsonResponse({'message': 'Profile updated successfully'})

    def delete(self, request):
        user_id = verify_token(request)
        if not user_id:
            return JsonResponse({'error': 'Invalid or expired token'}, status=401)

        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE id = %s", [user_id])
            existing = cursor.fetchone()

        if not existing:
            return JsonResponse({'error': 'User not found'}, status=404)

        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM users WHERE id = %s", [user_id])

        return JsonResponse({'message': 'Account deleted successfully'})
# GET ALL USERS
class UserListView(View):
    def get(self, request):
        user_id = verify_token(request)
        if not user_id:
            return JsonResponse({'error': 'Invalid or expired token'}, status=401)

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


# DELETE USER
class UserDeleteView(View):
    def delete(self, request, user_id):
        auth_user = verify_token(request)
        if not auth_user:
            return JsonResponse({'error': 'Invalid or expired token'}, status=401)

        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE id = %s", [user_id])
            existing = cursor.fetchone()

        if not existing:
            return JsonResponse({'error': 'User not found'}, status=404)

        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM users WHERE id = %s", [user_id])

        return JsonResponse({'message': 'User deleted successfully'})