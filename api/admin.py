from django.contrib import admin
from .models import UserProfile, Ad, AdView, Transaction, RedemptionRequest, AppSettings


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('uid', 'email', 'phone_number', 'role', 'wallet_balance', 'is_blocked', 'created_at')
    list_filter = ('role', 'is_blocked')
    search_fields = ('uid', 'email', 'phone_number')
    readonly_fields = ('uid', 'created_at')
    ordering = ('-created_at',)
    list_editable = ('is_blocked', 'role')
    list_per_page = 25

    fieldsets = (
        ('Identity', {
            'fields': ('uid', 'email', 'phone_number')
        }),
        ('Status & Role', {
            'fields': ('role', 'is_blocked')
        }),
        ('Wallet', {
            'fields': ('wallet_balance',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    list_display = ('title', 'media_type', 'point_reward', 'timer_duration', 'active', 'view_count', 'created_at')
    list_filter = ('active', 'media_type')
    search_fields = ('title', 'description')
    list_editable = ('active', 'point_reward')
    ordering = ('-created_at',)
    readonly_fields = ('view_count', 'created_at')
    list_per_page = 25

    fieldsets = (
        ('Ad Content', {
            'fields': ('title', 'description', 'media_url', 'media_type')
        }),
        ('Reward Settings', {
            'fields': ('point_reward', 'timer_duration')
        }),
        ('Status & Stats', {
            'fields': ('active', 'view_count', 'created_at')
        }),
    )


@admin.register(AdView)
class AdViewAdmin(admin.ModelAdmin):
    list_display = ('user', 'ad', 'reward', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('user__uid', 'user__email', 'ad__title')
    readonly_fields = ('user', 'ad', 'reward', 'timestamp')
    ordering = ('-timestamp',)
    list_per_page = 50


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'type', 'description', 'timestamp')
    list_filter = ('type', 'timestamp')
    search_fields = ('user__uid', 'user__email', 'description')
    readonly_fields = ('user', 'amount', 'type', 'description', 'timestamp')
    ordering = ('-timestamp',)
    list_per_page = 50


@admin.register(RedemptionRequest)
class RedemptionRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'payment_method', 'status', 'created_at')
    list_filter = ('status', 'payment_method')
    search_fields = ('user__uid', 'user__email')
    list_editable = ('status',)
    ordering = ('-created_at',)
    readonly_fields = ('user', 'amount', 'payment_method', 'payment_details', 'created_at')
    list_per_page = 25

    fieldsets = (
        ('Request Info', {
            'fields': ('user', 'amount', 'payment_method', 'payment_details')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(AppSettings)
class AppSettingsAdmin(admin.ModelAdmin):
    list_display = ('maintenance_mode', 'notifications_enabled', 'contact_email', 'two_factor_enabled')

    def has_add_permission(self, request):
        # Prevent adding more than one settings object
        return not AppSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
