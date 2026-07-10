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
