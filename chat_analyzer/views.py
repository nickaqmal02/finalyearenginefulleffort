from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import AdminRegisterationForm, LoginForm, ClientRegisterationForm, TherapistRegistrationForm
from .models import Admin, Therapist, Client, Conversation, UnmatchedMessage
from datetime import datetime

# Create your views here.
def welcome(request):
    """ welcome landing page for all users """
    return render(request, 'chat_analyzer/welcome.html')

def login_view(request):
    """ login page - handles both Admin and Therapist login """
    # if already logged in , redirect to appropriate dashboard
    if request.session.get('user_id') and request.session.get('user_role'):
        if request.session.get('user_role') == 'admin':
            return redirect('chat_analyzer:admin_dashboard')
        elif request.session.get('user_role') == 'therapist':
            return redirect('chat_analyzer:therapist_dashboard')
        
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            # try to authenticate as Admin
            try:
                admin = Admin.objects.get(username=username)
                if admin.check_password(password):

                    # set session tgk sapo session lonih
                    request.session['user_id'] = admin.id
                    request.session['user_name'] = admin.name
                    request.session['user_role'] = 'admin'
                    messages.success(request, f'Welcome back, {admin.name}!')

                    # terus redirect ke admin dashboard if admin
                    return redirect('chat_analyzer:admin_dashboard')
            except Admin.DoesNotExist:
                pass

            #try to authenticate as Therapist
            try:
                therapist = Therapist.objects.get(username=username)
                if therapist.check_password(password):
                    if not therapist.is_active:
                        messages.error(request, 'Your account is inactive. Please contact admin.')

                        return render(request, 'chat_analyzer/auth/login.html')
                    
                    # set session
                    request.session['user_id'] = therapist.id
                    request.session['user_name'] = therapist.name
                    request.session['user_role'] = 'therapist'
                    messages.success(request, f'Welcome back, {therapist.name}!')

                    return redirect('chat_analyzer:therapist_dashboard')
            except Therapist.DoesNotExist:
                pass

            # authentication failed
            messages.error(request, 'invalid username or password')
    
    else:
        form = LoginForm()

    return render(request, 'chat_analyzer/auth/login.html',{'form': form})

def logout_view(request):
    """ logout user and clear session """
    request.session.flush()
    messages.info(request, 'You have been logged out. ')
    return redirect('chat_analyzer:login')

# admin dashboard views
def admin_dashboard(request):
    # this for check wether wwhich user is login
    if not request.session.get('user_id') or request.session.get('user_role') != 'admin':
        messages.warning(request, 'Please login as admin')
        return redirect('chat_analyzer:login')
    
    # get admin info 
    admin_id = request.session.get('user_id')

    # ==== add this context data ==== 
    # key metrics that we want to shows 
    total_clients = Client.objects.filter(registered_by_id=admin_id).count()
    active_clients = Client.objects.filter(
        registered_by_id=admin_id, 
        status='active'
    ).count()
    total_therapists = Therapist.objects.filter(registered_by_id=admin_id).count()
    total_messages = Conversation.objects.filter(
        client__registered_by_id=admin_id
    ).count()
    
    # Messages this month
    today = datetime.now()
    first_day_of_month = today.replace(day=1)
    messages_this_month = Conversation.objects.filter(
        client__registered_by_id=admin_id,
        date__gte=first_day_of_month
    ).count()

    # Unmatched messages
    unmatched_messages = Conversation.objects.filter(
        client__isnull=True
    ).count()

    # Recent conversations (last 10)
    recent_conversations = Conversation.objects.filter(
        client__registered_by_id=admin_id
    ).select_related('client').order_by('-uploaded_at')[:10]

    # Recent clients (last 5)
    recent_clients = Client.objects.filter(
        registered_by_id=admin_id
    ).order_by('-created_at')[:5]
    
    context = {
        'total_clients': total_clients,
        'active_clients': active_clients,
        'total_therapists': total_therapists,
        'total_messages': total_messages,
        'messages_this_month': messages_this_month,
        'unmatched_messages': unmatched_messages,
        'recent_conversations': recent_conversations,
        'recent_clients': recent_clients,
    }
    # ==========================================

    return render(request, 'chat_analyzer/admin/dashboard.html')




def admin_register(request):

    if request.session.get('user_id') and request.session.get('user_role') == 'admin':
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        form = AdminRegisterationForm(request.POST)
        if form.is_valid():
            admin = form.save()

            # auto login after registeration
            request.session['user_id'] = admin.id
            request.session['user_name'] = admin.name
            request.session['user_role'] = 'admin'

            messages.success(request, f"Welcome {admin.name}! Admin account created. ")
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminRegisterationForm()

    return render(request, 'chat_analyzer/auth/admin_register.html', {'form':form})


# ::::::::::::::::::: ADMIN CLIENT SECTION ::::::::::::::::::::::::::: #
# 1. ADMIN CREATING CLIENT
def admin_client_create(request):
    
    # always check wether the request session from admin or from another role 
    if not request.session.get('user_id') and request.session.get('user_role') == 'admin':
        messages.warning(request, 'Please login as admin')
        return redirect('chat_analyzer:login')
    
    admin_id = request.session.get('user_id')

    if request.method == 'POST':
        form = ClientRegisterationForm(request.POST, admin_id=admin_id)
        if form.is_valid():
            client = form.save(commit=False)
            client.registered_by_id = admin_id
            client.save()
            messages.success(request, f'Client {client.parent_name} created successfully !')
            return redirect('chat_analyzer:admin_client_list')
        else:
            messages.erro(request, 'Please correct the errors below.')
    else:
            form = ClientRegisterationForm(admin_id=admin_id)
    
    return render(request, 'chat_analyzer/admin/client/create_client.html', {'form':form})

# 2. VIEWS FOR ALL CLIENT LIST FOR THIS ADMIN
def admin_client_list(request):
    """ display all cliens for logged-in admin"""

    if not (request.session.get('user_id') and request.session.get('user_role') == 'admin'):
        messages.warnin(request, 'please login as admin')
        return redirect('chat_analyzer:login')
    
    admin_id = request.session.get('user_id')

    # get all clients registered by this admin
    clients = Client.objects.filter(registered_by_id=admin_id).order_by('-created_at')

    # optional: add count of conversations per client
    for client in clients:
        client.conversation_count = client.conversations.count()

    context = {
        'clients': clients,
        'total_clients': clients.count(),
        'active_clients': clients.filter(status='active').count()

    }
    return render(request, 'chat_analyzer/admin/client/client_list.html', context)

# 3. DELETE CLIENT SECTION { lesson, we shall also send client_id }
# admin client delete views 
def admin_client_delete(request, client_id):
    """ Delete a client """

    # check admin session
    if not (request.session.get('user_id') and request.session.get('user_role') == 'admin'):
        messages.warning(request, 'Plase login as admin')
        return redirect('chat_analyzer:login')
    
    # get the admin id 
    admin_id = request.session.get('user_id')

    # get the client (make sure it belongs )
    client = get_object_or_404(Client, id=client_id, registered_by_id=admin_id)

    if request.method  == 'POST':
        client_name = client.parent_name
        client.delete()
        messages.success(request, f'Client "{client_name}" has been deleted succesfully. ')
        return redirect('chat_analyzer:admin_client_list')

    # get request - show confirmation page
    return render(request, 'chat_analyzer/admin/client/client_confirm_delete.html', {'client':client})

# 4. EDIT CLIENT FROM ADMIN PAGE
def admin_client_edit(request, client_id):
    """ edit client details """
    # check admin session or not 
    if not (request.session.get('user_id') and request.session.get('user_role') == 'admin'):
        messages.warning(request, 'Please login as admin')
        return redirect('chat_analyzer:login')
    
    admin_id = request.session.get('user_id')

    # get client (make sure is belongs to this admin)
    client = get_object_or_404(Client, id=client_id, registered_by_id=admin_id)

    if request.method == 'POST':
        form = ClientRegisterationForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, f'Client "{client.parent_name}" has been updated succesfully.')
            return redirect('chat_analyzer:admin_client_list')
        else:
            messages.error(request, 'Please correct the errors below')
    else:
        form = ClientRegisterationForm(instance=client)

    return render(request, 'chat_analyzer/admin/client/client_edit.html', {'form': form, 'client': client})

# 5. VIEWS DETAIL OF CLIENT
def admin_client_detail(request, client_id):
    """ View detailed information about spesific client """

    # check admin session mcm biasa 
    if not (request.session.get('user_id') and request.session.get('user_role') == 'admin'):
        messages.warning(request, 'Please login as admin')
        return redirect('chat_analyzer:login')
    
    # get the admin id 
    admin_id = request.session.get('user_id')

    # get the client we append the value of client 
    client = get_object_or_404(Client, id=client_id, registered_by_id=admin_id)

    # get recent conversation (last 10)
    recent_conversations = client.conversations.all().order_by('-date', '-time')[:10]

    # get conversation statistics
    total_messages = client.conversations.count()
    unique_dates = client.conversations.dates('date', 'day').count()
    last_message_date = client.conversations.order_by('-date', '-time').first()

    # sentiment statistics
    positive_count = client.conversations.filter(sentiment='positive').count()
    negative_count = client.conversations.filter(sentiment='negative').count()
    neutral_count = client.conversations.filter(sentiment='neutral').count()

    context = {
        'client': client,
        'recent_conversations': recent_conversations,
        'total_messages': total_messages,
        'unique_dates': unique_dates,
        'last_message_date': last_message_date,
        'positive_count': positive_count,
        'negative_count': negative_count,
        'neutral_count': neutral_count,
    }

    return render(request, 'chat_analyzer/admin/client/client_detail.html', context)

# admin client delete views 
def admin_client_delete(request, client_id):
    """ Delete a client """

    # check admin session
    if not (request.session.get('user_id') and request.session.get('user_role') == 'admin'):
        messages.warning(request, 'Plase login as admin')
        return redirect('chat_analyzer:login')
    
    # get the admin id 
    admin_id = request.session.get('user_id')

    # get the client (make sure it belongs )
    client = get_object_or_404(Client, id=client_id, registered_by_id=admin_id)

    if request.method  == 'POST':
        client_name = client.parent_name
        client.delete()
        messages.success(request, f'Client "{client_name}" has been deleted succesfully. ')
        return redirect('chat_analyzer:admin_client_list')

    # get request - show confirmation page
    return render(request, 'chat_analyzer/admin/client/client_confirm_delete.html', {'client':client})
















# ================== END OF ADMIN CLIENT SECTION ======================== #



# ==================== ADMIN THERAPIST SECTION =========================== #

# creating therapist views
def admin_therapist_create(request):
    """ admin creates"""
    # check wether it is admin session or not
    if not (request.session.get('user_id') and request.session.get('user_role') == 'admin'):
        messages.warning(request, 'please login as admin')
        return redirect('chat_analyzer:login')
    
    admin_id = request.session.get('user_id')

    if request.method == 'POST':
        form = TherapistRegistrationForm(request.POST)
        if form.is_valid():
            therapist = form.save(commit=False, admin_id=admin_id)
            therapist.save()
            messages.success(request, f'Therapist {therapist.name} created succesfully')
            return redirect('chat_analyzer:admin_therapist_list')
        else:
            messages.error(request, 'Please Correct the errors below.')
    else:
        form = TherapistRegistrationForm()
        # noted that dkt else punya form kita x send request.POST

    return render(request, 'chat_analyzer/admin/therapist/create_therapist.html', {'form':form})

# therapist list views
def admin_therapist_list(request):
    """ display all therapists for the logged-in admin"""

    # first skali check admin session 
    if not (request.session.get('user_id') and request.session.get('user_role') == 'admin'):
        messages.warning(request, 'Plase login as admin')
        return redirect('chat_analyzer:login')
    
    # mcm biasa take the admin id by initialize it
    admin_id = request.session.get('user_id')

    # get all therapist registered by this admin
    therapists = Therapist.objects.filter(registered_by_id=admin_id).order_by('-created_at')

    # get client count for each therapist
    for therapist in therapists:
        therapist.client_count = therapist.clients.count()

    context = {
        'therapists': therapists,
        'total_therapists': therapists.count(),
        'active_therapists': therapists.filter(is_active=True).count(),
    }
    
    # lastly we have to render it 
    return render(request, 'chat_analyzer/admin/therapist/therapist_list.html', context)

# toggle for active and inactive the therapist
def admin_therapist_toggle(request, therapist_id):
    """ Toggle therapist wether active/inactive """
    if not (request.session.get('user_id') and request.session.get('user_role') == 'admin'):
        messages.warning(request, 'please login as admin')
        return redirect('chat_analyzer:login')
    
    # initialize the admin id
    admin_id = request.session.get('user_id')
    therapist = get_object_or_404(Therapist, id = therapist_id, registered_by_id=admin_id)

    therapist.is_active = not therapist.is_active
    therapist.save()

    status = "activated" if therapist.is_active else "deactivated"
    messages.success(request, f'Therapist {therapist.name} has been {status}.')

    return redirect('chat_analyzer:admin_therapist_list')

# :: EDIT VIEWS FOR THERAPIST IN ADMIN INTERFACE :: #
def admin_therapist_edit(request, therapist_id):
    # check wether in session is admin or not 
    if not (request.session.get('user_id') and request.session.get('user_role') == 'admin'):
        # so why request why not f 'please login as admin' so request here is about who is requesting this url
        messages.warning(request, 'please login as admin')
        return redirect('chat_analyzer:login')
    
    # so now get the admin id 
    admin_id = request.session.get('user_id')
    therapist = get_object_or_404(Therapist, id = therapist_id, registered_by_id=admin_id)

    if request.method == 'POST':
        form = TherapistRegistrationForm(request.POST, instance=therapist)
        if form.is_valid():
            form.save()
            messages.success(request, f'Client "{therapist.name}" has been updated succesfully.')
            return redirect('chat_analyzer:admin_client_list')
        else:
            messages.error(request, 'Please correct the errors below')
    else:
        form = TherapistRegistrationForm(instance=therapist)

    return render(request, 'chat_analyzer/admin/therapist/therapist_edit.html', {'form': form, 'therapist': therapist})

# :: THERAPIST DETAIL VIEWS FROM ADMIN :: #
def admin_therapist_detail(request, therapist_id):
        """view detailed information about a spesific therapist"""

        # check admin session
        if not (request.session.get('user_id') and request.session.get):
            messages.warning(request, 'please login as admin')
            return redirect('chat_analyzer:login')
        
        # get the admin id
        admin_id = request.session.get('user_id')

        # get the therapist and make it as object nicky
        therapist = get_object_or_404(Therapist, id=therapist_id, registered_by_id=admin_id)

        # get all clients assigned to this therapist
        assigned_clients = therapist.clients.all().order_by('-created_at')

        # get statistics
        total_clients = assigned_clients.count()
        active_clients = assigned_clients.filter(status='active').count()

        # get recent conversations from this therapist's clients 
        recent_conversations = Conversation.objects.filter(
            client__in=assigned_clients
        ).order_by('-date', '-time')[:10]

        # get all conversations count
        total_conversations = Conversation.objects.filter(
            client__in=assigned_clients
        ).count()

        context = {
            'therapist': therapist,
            'assigned_clients': assigned_clients,
            'total_clients': total_clients,
            'active_clients': active_clients,
            'recent_conversations': recent_conversations,
            'total_conversations': total_conversations,
        }

        return render(request, 'chat_analyzer/admin/therapist/therapist_detail.html', context)

# :: ASSIGN CLIENT TO THERAPIST VIEWS ::
def admin_assign_clients_to_therapist(request, therapist_id):
    """ admin page to assign multiple clients to a spesific therapist"""

    if not (request.session.get('user_id') and request.session.get('user_role') == 'admin'):
        messages.warning(request, 'Please login as admin')
        return redirect('chat_analyzer:login')
    
    # mcm biasa get admin_id
    admin_id = request.session.get('user_id')
    therapist = get_object_or_404(Therapist, id=therapist_id, registered_by_id=admin_id)

    # get all assigned and unassigned clients
    unassigned_clients = Client.objects.filter(
        registered_by_id=admin_id,
        assigned_therapist__isnull=True
    ).order_by('parent_name')

    assigned_clients = Client.objects.filter(
        registered_by_id=admin_id,
        assigned_therapist=therapist
    ).order_by('parent_name')

    # get other therapists (to switch assignments)
    other_therapists = Therapist.objects.filter(
        registered_by_id=admin_id,
        is_active=True
    ).exclude(id=therapist_id)

    if request.method == 'POST':
        action = request.POST.get('action')
    
        if action == 'assign':
            client_ids = request.POST.getlist('client_ids')
            # clients to assign kita filter yg still xdk therapist assigned
            clients_to_assign = Client.objects.filter(id__in=client_ids, registered_by_id=admin_id)
            count = clients_to_assign.update(assigned_therapist=therapist)
            messages.success(request, f'✅ Assigned {count} client(s) to {therapist.name}')

        elif action == 'remove':
            client_ids = request.POST.getlist('client_ids')
            # bezo function clients to remove is it is for assigned therapist only
            clients_to_remove = Client.objects.filter(id__in=client_ids, registered_by_id=admin_id, assigned_therapist=therapist)
            count = clients_to_remove.update(assigned_therapist=None)
            messages.success(request, f'✅ Removed {count} client(s) from {therapist.name}')

        elif action == 'transfer':
            client_ids = request.POST.getlist('client_ids')
            new_therapist_id = request.POST.getlist('client_ids')
            new_therapist = get_object_or_404(Therapist, id=new_therapist_id, registered_by_id=admin_id)
            clients_to_transfer = Client.objects.filter(id__in=client_ids, registered_by_id=admin_id, assigned_therapist=therapist)
            count = clients_to_transfer.update(assigned_therapist=None)
            messages.success(request, f'✅ Transferred {count} client(s) from {therapist.name} to {new_therapist.name}')

        return redirect('chat_analyzer:admin_assign_clients_to_therapist',therapist_id=therapist.id)

    context = {
        'therapist': therapist,
        'unassigned_clients': unassigned_clients,
        'assigned_clients': assigned_clients,
        'other_therapists': other_therapists,
        'total_assigned': assigned_clients.count(),
        'total_unassigned': unassigned_clients.count(),
    }

    return render(request, 'chat_analyzer/admin/therapist/assign_client.html', context)
   








# ================ VIEWS FOR CONVERSATION ====================

# 1. :: CONVERSATION LIST ::
from django.core.paginator import Paginator

def admin_conversation_list(request):
    """display all conversations with pagination"""

    # like we always do check admin session or not
    if not (request.session.get('user_id') and request.session.get('user_role') == 'admin'):
        messages.warning(request, 'Please login as admin')
        return redirect('chat_analyzer:login')
    
    # get admin
    admin_id = request.session.get('user_id')

    # get all conversations for clients under this admin
    conversations = Conversation.objects.filter(
        client__registered_by_id=admin_id
    ).select_related('client').order_by('-date','-time')

    # pagination (20 per page)
    paginator = Paginator(conversations, 20)
    page_number = request.GET.get('page',1)
    page_obj = paginator.get_page(page_number)

    # Statistics
    total_messages = conversations.count()
    matched_messages = conversations.filter(client__isnull=False).count()
    unmatched_messages = conversations.filter(client__isnull=True).count()

    context = {
        'page_obj': page_obj,
        'total_messages': total_messages,
        'matched_messages': matched_messages,
        'unmatched_messages': unmatched_messages,
    }

    return render(request, 'chat_analyzer/admin/conversations/list.html', context)

# 2. :: UPLOAD PAGE VIEWS ::
from .forms import WhatsappUploadForm
from .services.whatsapp_parser import parse_whatsapp_file
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from datetime import datetime
import os

def admin_upload_whatsapp(request):
    """Upload and process whatsapp chat file"""

    # check admin sessionn
    if not (request.session.get('user_id') and request.session.get('user_role') == 'admin'):
        messages.warning(request, 'please login as admin')
        return redirect('chat_analyzer:login')
    
    # get the admin id
    admin_id = request.session.get('user_id')

    if request.method == 'POST':
        form = WhatsappUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']

            if not uploaded_file.name.endswith('.txt'):
                messages.error(request, 'please upload a .txt file')
                return render(request, 'chat_analyzer/admin/whatsapp/upload.html', {'form':form})
            
            # enhancement 1: save uploaded file (optional - for audit)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            saved_filename = f"uploads/whatsapp_{timestamp}_{uploaded_file.name}"
            saved_path = default_storage.save(saved_filename, ContentFile(uploaded_file.read()))

            # re-read the file (because we already read it)
            file_content = default_storage.open(saved_path).read().decode('utf-8')

            try:
                # parse messages
                messages_list = parse_whatsapp_file(file_content)

                if not messages_list:
                    messages.warning(request, 'No valid Whatsapp messages found')

                    # clean up saved file
                    default_storage.delete(saved_path)
                    return render(request, 'chat_analyzer/admin/whatsapp/upload.html', {'form':form})
                
                # ENHANCEMENT 2: GET LATEST MESSAGE DATE FOR REPORTING
                latest_message_date = max((msg['date'] for msg in messages_list), default=None)
                earliest_message_date = min((msg['date'] for msg in messages_list), default=None)

                # ENHANCEMENT 3: IMPROVED CLIENT MATCHING
                clients = Client.objects.filter(registered_by_id=admin_id)

                # create multiple lookup methods
                phone_lookup = {}
                name_lookup = {}
                username_lookup = {}

                for client in clients:
                    # method 1: phone number
                    if client.phone_number:
                        phone_lookup[client.phone_number] = client.id
                        # also store normalized version
                        normalized = client.phone_number.replace(' ', '').replace('-','')
                        phone_lookup[normalized] = client.id

                    # method 2 : username 
                    if client.username:
                        username_lookup[client.username.lower()] = client.id

                    # method 3: check using parent name
                    if client.parent_name:
                        name_lookup[client.parent_name.lower()] = client.id

                # enhancement 4: we track stats
                saved_count = 0
                matched_count = 0
                unmatched_senders = {}
                duplicate_count = 0
                unmatched_count = 0 # new : count of unmatched message

                # enhancement 5: check for duplicates before saving
                existing_messages = set(
                    Conversation.objects.filter(
                        client__registered_by_id=admin_id
                    ).values_list('date', 'time', 'username', 'message')
                )

                #new enhancement : check existing unmatched messages
                existing_unmatched = set(
                    UnmatchedMessage.objects.filter().values_list('date', 'time', 'username', 'message')
                )

                for msg in messages_list:
                    sender = msg['username']
                    client_id = None

                    # try matching in priority order
                    if sender in phone_lookup:
                        client_id = phone_lookup[sender]
                        matched_count +=1
                    elif sender.lower() in username_lookup:
                        client_id = username_lookup[sender.lower()]
                        matched_count +=1
                    elif sender.lower() in name_lookup:
                        client_id = name_lookup[sender.lower()]
                        matched_count += 1
                    else:
                        unmatched_senders[sender] = unmatched_senders.get(sender, 0) + 1

                    # check for duplicate message
                    is_duplicate = (
                        msg['date'],
                        msg['time'],
                        sender,
                        msg['message'][:100]
                    ) in existing_messages

                    if is_duplicate:
                        duplicate_count +=1
                        continue
                    #next improvement handles unmatched messages seperately
                    # if matched we save into our Conversation models
                    if client_id:
                    # save message into Conversation 
                        Conversation.objects.create(
                            client_id=client_id,
                            date=msg['date'],
                            time=msg['time'],
                            username=sender,
                            message=msg['message'],
                        )
                        saved_count += 1
                    # if not matched with our client numbers and username
                    else:
                        UnmatchedMessage.objects.create(
                            date=msg['date'],
                            time=msg['time'],
                            username=sender,
                            message=msg['message'],
                        )
                        unmatched_count += 1 # count unmatched

                # ENHANCEMENT 6: DELETE SAVED FILE IF NO ERRORS
                default_storage.delete(saved_path)

                # ENHANCMENT 7: BETTER REPORTING
                if duplicate_count > 0:
                    messages.info(request, f' Skipped {duplicate_count} duplicate messages')

                if unmatched_count > 0:
                    messages.warning(
                        request,
                        f'⚠️ {unmatched_count} message(s) from unknown senders saved to "Unmatched Messages"'
                    )

                if unmatched_senders:
                    # shows top 5 unmatched senders with counts
                    top_unmatched = sorted(unmatched_senders.items(), key=lambda x: x[1], reverse=True)[:5]

                    preview = ', '.join([f"{sender} ({count})" for sender, count in top_unmatched])
                    
                    if len(unmatched_senders) > 5:
                        preview += f' and {len(unmatched_senders) - 5} more'

                    messages.warning(request, f'⚠️ {len(unmatched_senders)} sender(s) not recognized: {preview}')

                # ENHANCEMENT 8: SUMMARY FOR DATE RANGE
                summary = f'✅ Imported {saved_count} messages! {matched_count} linked to clients.'
                if unmatched_count > 0:
                    summary += f'{unmatched_count} unmatched messages saved seperately.'

                if earliest_message_date and latest_message_date:
                    summary += f' (From {earliest_message_date} to {latest_message_date})'
                    
                    messages.success(request, summary)

                    return redirect('chat_analyzer:admin_conversation_list')
                
            except Exception as e:
                messages.error(request, f'Error processing file: {str(e)}')
                # clean up saved file on error
                default_storage.delete(saved_path)
                return render(request, 'chat_analyzer/admin/conversations/upload.html', {'form':form})
            
    else:
        form = WhatsappUploadForm()
        return render(request, 'chat_analyzer/admin/conversations/upload.html', {'form': form})
    
