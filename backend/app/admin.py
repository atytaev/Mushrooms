# admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    CustomUser,
    Inspection,
    MushroomStorage,
    MushroomPhoto,
    ProductMarkingZip,
    ProductMarkingPhoto,
    QuantityInspection,
    Box,
    QuantityInspectionPhoto,
    QualityInspection,
    QualityInspectionPhoto,
    DiameterMeasurement,
    DiameterMeasurementPhoto,
    Pallet,
    PalletPhoto,
    ProductLoading,
    ProductLoadingPhoto,
)
from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

# Inline models for photos and boxes
class MushroomPhotoInline(admin.TabularInline):
    model = MushroomPhoto
    extra = 1
    readonly_fields = ('uploaded_at',)

class ProductMarkingPhotoInline(admin.TabularInline):
    model = ProductMarkingPhoto
    extra = 1
    readonly_fields = ('uploaded_at',)

class QuantityBoxInline(admin.TabularInline):
    model = Box
    extra = 1

class QuantityPhotoInline(admin.TabularInline):
    model = QuantityInspectionPhoto
    extra = 1
    readonly_fields = ('uploaded_at',)

class QualityPhotoInline(admin.TabularInline):
    model = QualityInspectionPhoto
    extra = 1
    readonly_fields = ('uploaded_at',)

class DiameterPhotoInline(admin.TabularInline):
    model = DiameterMeasurementPhoto
    extra = 1
    readonly_fields = ('uploaded_at',)

class PalletPhotoInline(admin.TabularInline):
    model = PalletPhoto
    extra = 1
    readonly_fields = ('uploaded_at',)

class LoadingPhotoInline(admin.TabularInline):
    model = ProductLoadingPhoto
    extra = 1
    readonly_fields = ('uploaded_at',)

# Admin for each section
@admin.register(MushroomStorage)
class MushroomStorageAdmin(admin.ModelAdmin):
    list_display = ('inspection', 'quantity_of_boxes', 'quantity_of_pallets', 'invoice_number')
    inlines = [MushroomPhotoInline]
    search_fields = ('inspection__job_number',)

@admin.register(ProductMarkingZip)
class ProductMarkingZipAdmin(admin.ModelAdmin):
    list_display = ('inspection', 'zip_photos')
    search_fields = ('inspection__job_number',)

@admin.register(ProductMarkingPhoto)
class ProductMarkingPhotoAdmin(admin.ModelAdmin):
    list_display = ('inspection', 'thumbnail', 'uploaded_at')
    readonly_fields = ('uploaded_at',)
    search_fields = ('inspection__job_number',)

    def thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" />', obj.image.url)
        return '-'
    thumbnail.short_description = 'Preview'

class QuantityInspectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_scale_model', 'get_calibration_date')  # другие поля тоже можно добавить

    def get_scale_model(self, obj):
        return obj.scale.model if obj.scale else '-'
    get_scale_model.short_description = 'Модель весов'
    get_scale_model.admin_order_field = 'scale__model'  # сортировка по связанному полю

    def get_calibration_date(self, obj):
        return obj.scale.calibration_date if obj.scale else '-'
    get_calibration_date.short_description = 'Дата поверки весов'
    get_calibration_date.admin_order_field = 'scale__calibration_date'

admin.site.register(QuantityInspection, QuantityInspectionAdmin)

@admin.register(QualityInspection)
class QualityInspectionAdmin(admin.ModelAdmin):
    list_display = ('inspection', 'sample_mass_kg', 'conforms_to_declared_grade')
    inlines = [QualityPhotoInline]
    search_fields = ('inspection__job_number',)

@admin.register(DiameterMeasurement)
class DiameterMeasurementAdmin(admin.ModelAdmin):
    list_display = ('inspection',)
    inlines = [DiameterPhotoInline]
    search_fields = ('inspection__job_number',)

@admin.register(Pallet)
class PalletAdmin(admin.ModelAdmin):
    list_display = ('inspection',)
    inlines = [PalletPhotoInline]
    search_fields = ('inspection__job_number',)

@admin.register(ProductLoading)
class ProductLoadingAdmin(admin.ModelAdmin):
    list_display = ('inspection', 'car_number', 'transport_temperature')
    inlines = [LoadingPhotoInline]
    search_fields = ('inspection__job_number', 'car_number')

# Main Inspection admin inlines
class MushroomStorageInline(admin.StackedInline):
    model = MushroomStorage
    extra = 0
    show_change_link = True
    inlines = [MushroomPhotoInline]

class ProductMarkingZipInline(admin.StackedInline):
    model = ProductMarkingZip
    extra = 0
    show_change_link = True

class QuantityInspectionInline(admin.StackedInline):
    model = QuantityInspection
    extra = 0
    show_change_link = True
    inlines = [QuantityBoxInline, QuantityPhotoInline]

class QualityInspectionInline(admin.StackedInline):
    model = QualityInspection
    extra = 0
    show_change_link = True
    inlines = [QualityPhotoInline]

class DiameterMeasurementInline(admin.StackedInline):
    model = DiameterMeasurement
    extra = 0
    show_change_link = True
    inlines = [DiameterPhotoInline]

class PalletInline(admin.StackedInline):
    model = Pallet
    extra = 0
    show_change_link = True
    inlines = [PalletPhotoInline]

class ProductLoadingInline(admin.StackedInline):
    model = ProductLoading
    extra = 0
    show_change_link = True
    inlines = [LoadingPhotoInline]

@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    list_display = ('job_number', 'inspection_date', 'inspector_name', 'car_number')
    search_fields = ('job_number', 'inspector_name', 'product_loading__car_number')
    list_filter = ('inspection_date',)
    inlines = [
        MushroomStorageInline,
        ProductMarkingZipInline,
        QuantityInspectionInline,
        QualityInspectionInline,
        DiameterMeasurementInline,
        PalletInline,
        ProductLoadingInline,
    ]

class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Пароль", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Повтор пароля", widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ("username", "first_name", "last_name", "email", "role")

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Пароли не совпадают")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class CustomUserChangeForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ("username", "first_name", "last_name", "email", "role", "is_active", "is_staff", "is_superuser")

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser

    list_display = ("username", "first_name", "last_name", "email", "role", "is_staff")
    list_filter  = ("role", "is_staff", "is_superuser", "is_active")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Персональные данные", {"fields": ("first_name", "last_name", "email", "role")}),
        ("Права доступа",     {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Важные даты",       {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "first_name", "last_name", "email", "role", "password1", "password2", "is_active", "is_staff")
        }),
    )

    search_fields = ("username", "first_name", "last_name", "email", "role")
    ordering = ("username",)
