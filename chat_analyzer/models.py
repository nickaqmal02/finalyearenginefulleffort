from django.db import models
from django.contrib.auth.hashers import make_password, check_password


# create Admin models
class Admin(models.Model):
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
    class Meta:
        verbose_name="Admin and Staff"
    
    def __str__(self):
        return f'{self.username} - {self.name}'
    
class Therapist(models.Model):
    # therapist details 

    username = models.CharField(max_length=200, unique=True)
    password = models.CharField(max_length=200)
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255)
    specialization = models.CharField(max_length=200, blank=True)
    registered_by = models.ForeignKey(Admin, on_delete=models.CASCADE, related_name='therapists')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
    def __str__(self):
        return f"{self.name} - {self.specialization or 'General Therapist'}"
    

class Client(models.Model):
    username = models.CharField(max_length=100, unique=True, blank=True, null=True)
    parent_name = models.CharField(max_length=255)
    child_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    registered_by = models.ForeignKey(Admin, on_delete=models.CASCADE, related_name='clients')
    assigned_therapist = models.ForeignKey(
        Therapist,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clients'
        )
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending')
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default = 'pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # sini nk tukar namo 
        verbose_name='Client of Autism Center'

    def __str__(self):
        therapist_name = self.assigned_therapist.name if self.assigned_therapist else "Unassigned"
        return f"{self.parent_name} (Child: {self.child_name}) -> {therapist_name}"
    
# creating Conversation model
class Conversation(models.Model):

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="conversations",
        help_text="the client this conversation belongs to")
    # in future we can call it by client.coversations.message
    date = models.DateField(help_text="Date of message from whatsapp")
    time = models.TimeField(help_text="Time of the message from whatsapp")
    username = models.CharField(
        max_length=200,
        help_text="original sender name/ number from whatsapp")
    # message section
    message = models.TextField(help_text="original message text")
    cleaned_text = models.TextField(
        blank=True,
        null=True,
        help_text='cleaned version (after preprocessing)'
    )
    # analysis result
    sentiment = models.CharField (
        max_length=20,
        blank=True,
        null=True,
        choices=[
            ('positive', 'Positive'),
            ('negative', 'Negative'),
            ('neutral', 'Neutral')
        ],
        help_text='sentiment analysis result'
    )
    #meta data: which is the detail about data uploaded
    uploaded_at = models.DateTimeField(auto_now_add=True, help_text="when this was imported")
    upload_batch = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Batch ID for grouping uploads'
    )
    class Meta:
        # kegunaaan verbose name adalah name dkt admin page
        ordering = ['-date', '-time'] # newest first
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"

    def __str__(self):
        client_name = self.client.parent_name if self.client else "Uknown"
        return f"{self.date} - {client_name}: {self.message[:50]}"
    
# UNMATCHED MESSAGE MODEL
class UnmatchedMessage(models.Model):
    """Messages that couldnt be linked to any client"""
    date = models.DateField()
    time = models.TimeField()
    username = models.CharField(max_length=200)
    message = models.TextField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    upload_batch = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ['-date', '-time']
        verbose_name = 'Unmatched Message'
        verbose_name_plural = 'Unmatched Messages'

    def __str__(self):
        return f"{self.date} - {self.username} : {self.message[:50]}"