from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from functools import wraps

# setup the decorators
def role_required(allowed_roles):
    """ this is how we create decorators allowed_roles as a parameter
    example of usage: @role_required('admin', 'therapist')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('chat_analyzer:login_view')

            if request.user.role not in allowed_roles:
                raise PermissionDenied("You don't have permission to access this page")

            return view_func(request, *args, **kwargs)

        return wrapped_view
    return decorator

def admin_required(view_func):
    return role_required('admin')(view_func)

def therapist_required(view_func):
    return role_required('therapist')(view_func)

def doctor_required(view_func):
    return role_required('doctor')(view_func)

def client_required(view_func):
    return role_required('client')(view_func)

def clinical_staff_required(view_func):
    return role_required('admin', 'doctor')(view_func)        


# ╔════════════════════════════════════════════╗ 
# ║           Little tips 😊                   ║ 
# ╚════════════════════════════════════════════╝ 
""" 
- this decorators will be use in our views 
  e.x. @client_required
  for stater beginner level this approach was suitable to make it less complex
"""

