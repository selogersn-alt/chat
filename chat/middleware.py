from django.http import JsonResponse
from django.shortcuts import redirect

class RoleAccessMiddleware:
    """
    Middleware to restrict access to /admin/ and /manager/ portals.
    - /admin/ is restricted strictly to superusers (is_superuser=True).
    - /manager/ and /api/manager/ are restricted to managers and superusers.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        
        # 1. Restrict /admin/ access
        if path.startswith('/admin/'):
            if not request.user.is_authenticated:
                return redirect('login')
            if not request.user.is_superuser:
                if path.startswith('/api/'):
                    return JsonResponse({'error': 'Accès interdit. Super-administrateur requis.'}, status=403)
                return redirect('select_portal')
                
        # 2. Restrict /manager/ and /api/manager/ access
        if path.startswith('/manager/') or path.startswith('/api/manager/'):
            if not request.user.is_authenticated:
                return redirect('login')
            # role attribute might not exist on custom user or be empty, check safely
            user_role = getattr(request.user, 'role', '')
            if not (request.user.is_superuser or user_role == 'MANAGER'):
                if path.startswith('/api/') or path.startswith('/api/manager/'):
                    return JsonResponse({'error': 'Accès interdit. Droits Manager requis.'}, status=403)
                return redirect('select_portal')
                
        return self.get_response(request)


class CORSMiddleware:
    """
    Middleware to allow Cross-Origin Resource Sharing (CORS) for API endpoints.
    Allows local Flutter web development to communicate with the production server.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Handle preflight OPTIONS requests for API
        if request.method == 'OPTIONS' and request.path.startswith('/api/'):
            response = JsonResponse({'status': 'ok'})
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
            response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            return response
            
        response = self.get_response(request)
        if request.path.startswith('/api/'):
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
            response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        return response

