from django.contrib import admin
from .models import Client, Conversation, Therapist,Admin, UnmatchedMessage
import csv
from django.http import HttpResponse

# Register your models here.

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    ordering = ['-created_at'] 
    # means who created latest will be above
    list_display = ['parent_name', 'child_name', 'created_at']
    # this was so powerful to create column of what will be displayed in admin page
    list_filter = ['status', 'created_at']
    # list filter u will have filter segment below if u wann see status and when it have been created
    search_fields = ['parent_name', 'child_name', 'phone_number']
    # u will have a search and '' what u can search for

    #one more thing u can do is to add action button
    actions = ['export_to_csv']

    def export_to_csv(self, request, queryset):
        #self refers to Admin class itself
        # request http request from browser
        # queryset # the selected clients (the checked checkboxes)
        # how do program know thst queryset here is Client, because we have create this function in this ClientAdmin class

        # create the response object with csv header
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="clients_export.csv"'
        
        # content disposition meaning here is the file and 
        # create csv writer(response)
        writer = csv.writer(response)

        # write headers 
        writer.writerow([
            'ID',
            'Parent Name',
            'Child Name',
            'Phone Number',
            'Address',
            'Status',
            'Created At'
        ])

        for client in queryset: 
            writer.writerow([
                client.id,
                client.parent_name,
                client.child_name,
                client.phone_number,
                client.address or '',
                client.status,
                client.created_at
            ])

        # set count message, ni macam dkt atas dia macam notification
        self.message_user(request, f'exported {queryset.count()} clients to csv')

        return response
        #return response here means that what we have declared above about what we want to return actually
    export_to_csv.short_description = " export selected clients to csv"


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    ordering = ['-date']


@admin.register(Therapist)
class TherapistAdmin(admin.ModelAdmin):
    ordering = ['-created_at']
    list_display = ['name', 'username', 'specialization', 'is_active']
    list_filter = ['is_active', 'specialization', 'created_at']
    search_fields = ['name', 'username', 'phone_number']
    list_editable = ['is_active']
    
    readonly_fields = ['created_at', 'registered_by']

    fieldsets = (
        ('Personal Information', {
            'fields': ('username', 'name', 'phone_number', 'specialization')
        }),
        ('Account Information', {
            'fields': ('password', 'is_active')
        }),
        ('Metadata', {
            'fields': ('registered_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # New therapist being created
            obj.registered_by = Admin.objects.get(id=request.session.get('user_id'))
        super().save_model(request, obj, form, change)


@admin.register(Admin)
class AdminAdmin(admin.ModelAdmin):
    ordering=['-created_at']


@admin.register(UnmatchedMessage)
class UnmatchedMessageAdmin(admin.ModelAdmin):
    list_display = ['date', 'time', 'username', 'message_preview', 'uploaded_at']
    list_filter = ['date', 'uploaded_at']
    search_fields = ['username', 'message']

    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    
    message_preview.short_description = 'Message'

