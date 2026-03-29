from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('admin', 'Admin'),
    ]

    # Firebase UID as the primary key
    uid = models.CharField(max_length=128, primary_key=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    wallet_balance = models.FloatField(default=0.0)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    is_blocked = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email or self.phone_number or self.uid} ({self.role})"


class Ad(models.Model):
    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    media_url = models.URLField(max_length=1000)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    point_reward = models.IntegerField(default=0)
    timer_duration = models.IntegerField(default=15, help_text='Duration in seconds user must watch')
    active = models.BooleanField(default=True)
    view_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Advertisement'
        verbose_name_plural = 'Advertisements'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({'Active' if self.active else 'Inactive'}) — {self.point_reward} pts"


class AdView(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='ad_views')
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name='views')
    reward = models.IntegerField(default=0)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Ad View'
        verbose_name_plural = 'Ad Views'
        unique_together = ('user', 'ad')  # Prevents duplicate reward claims
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} viewed '{self.ad.title}' — +{self.reward} pts"


class Transaction(models.Model):
    TYPE_CHOICES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    ]

    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='transactions')
    amount = models.FloatField()
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    description = models.CharField(max_length=255)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-timestamp']

    def __str__(self):
        sign = '+' if self.type == 'credit' else '-'
        return f"{self.user} | {sign}{self.amount} pts — {self.description}"


class RedemptionRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='redemption_requests')
    amount = models.FloatField()
    payment_method = models.CharField(max_length=50)
    payment_details = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Redemption Request'
        verbose_name_plural = 'Redemption Requests'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} — {self.amount} pts via {self.payment_method} [{self.status}]"


class AppSettings(models.Model):
    """Singleton settings model — only one row (id=1) should ever exist."""
    maintenance_mode = models.BooleanField(default=False)
    notifications_enabled = models.BooleanField(default=True)
    contact_email = models.EmailField(default='admin@advertising-app.com')
    two_factor_enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'App Settings'
        verbose_name_plural = 'App Settings'

    def __str__(self):
        return 'App Settings'

    def save(self, *args, **kwargs):
        # Enforce singleton: always use id=1
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_instance(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
