from django.db import models
from django.contrib.auth.models import AbstractUser
import os
import datetime
from django.conf import settings

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('inspector', 'Инспектор'),
        ('manager',   'Менеджер'),
        ('admin',     'Администратор'),
    ]
    role = models.CharField("Роль", max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return self.username

def inspection_photo_upload_path(instance, filename):
    # определяем inspection
    if hasattr(instance, 'inspection'):
        insp = instance.inspection
    elif hasattr(instance, 'storage'):
        insp = instance.storage.inspection
    elif hasattr(instance, 'loading'):
        insp = instance.loading.inspection
    elif hasattr(instance, 'quantity_inspection'):
        insp = instance.quantity_inspection.inspection
    elif hasattr(instance, 'quality_inspection'):
        insp = instance.quality_inspection.inspection
    elif hasattr(instance, 'diameter_measurement'):
        insp = instance.diameter_measurement.inspection
    elif hasattr(instance, 'pallet'):
        insp = instance.pallet.inspection
    else:
        raise ValueError("Cannot determine inspection")

    date_str = insp.inspection_date.strftime("%Y-%m-%d")
    time_str = datetime.datetime.now().strftime("%H-%M-%S")
    base = f"photos/{date_str}_{time_str}"

    sub = {
        'MushroomPhoto': 'placement',
        'ProductMarkingPhoto': 'marking',
        'QuantityInspectionPhoto': 'quantity_inspection',
        'QualityInspectionPhoto': 'quality_inspection',
        'DiameterMeasurementPhoto': 'diameter',
        'PalletPhoto': 'pallets',
        'ProductLoadingPhoto': 'loading',
    }.get(instance.__class__.__name__, 'other')

    return os.path.join(base, sub, filename)

class Inspection(models.Model):
    inspection_date= models.DateField("Дата инспекции")
    inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Инспектор",
        on_delete=models.PROTECT,
        related_name="inspections"
    )
    job_number = models.CharField(
        "Номер работы",
        max_length=30,
        null=True,      # Позволяет хранить NULL в базе, если значение отсутствует
        blank=True      # Позволяет оставить поле пустым в формах и валидации
    )


    @property
    def inspector_name(self):
        return f"{self.inspector.last_name} {self.inspector.first_name}"

    @property
    def car_number(self):
        # берём первую (или единственную) загрузку
        loading = self.product_loading.first()
        return loading.car_number if loading else None

    def __str__(self):
        return f"{self.car_number} — {self.job_number}"

class Thermometer(models.Model):
    info = models.CharField("Информация о термометре", max_length=255)
    serial = models.CharField("Индентификационный номер термометра", max_length=100, blank=True, null=True)
    calibration_date = models.DateField("Дата поверки термометра", blank=True, null=True)

    def __str__(self):
        return f"{self.info} ({self.serial or '-'})"

# 1. Размещение товара
class MushroomStorage(models.Model):
    inspection = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name='mushroom_storage')
    quantity_of_boxes = models.IntegerField("Количество ящиков")
    quantity_of_pallets = models.IntegerField("Количество поддонов")
    temperature_in_fridge = models.FloatField("Температура в холодильнике")
    mushroom_temperature_min= models.FloatField("Мин. температура гриба")
    mushroom_temperature_max= models.FloatField("Макс. температура гриба")
    thermometer = models.ForeignKey(Thermometer, on_delete=models.PROTECT, blank=True, null=True)
    invoice_number = models.CharField("Номер счета-фактуры", max_length=100, blank=True, null=True)
    zip_photos = models.FileField(upload_to='zips/placement', null=True, blank=True,
                                          verbose_name="ZIP с фото размещения")
    def __str__(self):
        return f"Размещение — {self.inspection}"

class MushroomPhoto(models.Model):
    storage     = models.ForeignKey(MushroomStorage, on_delete=models.CASCADE, related_name='photos')
    image       = models.ImageField(upload_to=inspection_photo_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

# 2. Маркировка товара
class ProductMarkingZip(models.Model):
    inspection = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name='marking_zips')
    zip_photos = models.FileField(upload_to='zips/marking', verbose_name="ZIP с фото маркировки")

class ProductMarkingPhoto(models.Model):
    inspection = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name='marking_photos')
    image      = models.ImageField(upload_to=inspection_photo_upload_path)
    uploaded_at= models.DateTimeField(auto_now_add=True)

class Scale(models.Model):
    model = models.CharField("Модель весов", max_length=100)
    serial_number = models.CharField("Заводской номер весов", max_length=100, blank=True, null=True)
    calibration_date = models.DateField("Дата поверки весов", blank=True, null=True)

    def __str__(self):
        return f"{self.model} ({self.serial_number or '-'})"

# 3. Инспекция количества товара
class QuantityInspection(models.Model):
    inspection = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name='quantity_inspections')
    scale = models.ForeignKey(Scale, on_delete=models.PROTECT, blank=True, null=True)
    zip_photos = models.FileField(upload_to='zips/quantity', null=True, blank=True)

class Box(models.Model):
    quantity_inspection = models.ForeignKey(
        QuantityInspection,
        on_delete=models.CASCADE,
        related_name='boxes'
    )
    net_weight          = models.FloatField("Вес брутто с поддоном, кг")
    defect_weight       = models.FloatField("Вес поддона, кг")


class QuantityInspectionPhoto(models.Model):
    quantity_inspection = models.ForeignKey(QuantityInspection, on_delete=models.CASCADE, related_name='photos')
    image               = models.ImageField(upload_to=inspection_photo_upload_path)
    uploaded_at         = models.DateTimeField(auto_now_add=True)

# 4. Инспекция качества товара
class QualityInspection(models.Model):
    inspection = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name='quality_inspections')
    zip_photos = models.FileField(upload_to='zips/quality', null=True, blank=True)
    # новые поля
    sample_mass_kg = models.DecimalField(
        "Масса объединённой пробы, кг",
        max_digits=8, decimal_places=3,
        null=True, blank=True,
    )

    conforms_to_declared_grade = models.DecimalField(
        "Соответствие заявленному сорту, кг",
        max_digits=8, decimal_places=3,
        null=True, blank=True,
    )

    off_grade_mass_kg_50 = models.DecimalField(
        "Масса несоответствующих по калибру грибов 50, кг",
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
    )

    off_grade_mass_kg_70 = models.DecimalField(
        "Масса несоответствующих по калибру грибов 70, кг",
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
    )


    def __str__(self):
        return f"Качество — {self.inspection}"

class QualityInspectionPhoto(models.Model):
    quality_inspection = models.ForeignKey(QualityInspection, on_delete=models.CASCADE, related_name='photos')
    image              = models.ImageField(upload_to=inspection_photo_upload_path)
    uploaded_at        = models.DateTimeField(auto_now_add=True)

# 5. Замер диаметра грибов
class DiameterMeasurement(models.Model):
    inspection      = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name='diameter_measurements')
    zip_photos      = models.FileField(upload_to='zips/diameter', null=True, blank=True)

class DiameterMeasurementPhoto(models.Model):
    diameter_measurement = models.ForeignKey(DiameterMeasurement, on_delete=models.CASCADE, related_name='photos')
    image                = models.ImageField(upload_to=inspection_photo_upload_path)
    uploaded_at          = models.DateTimeField(auto_now_add=True)

# 6. Фотографии палет и их вес
class Pallet(models.Model):
    inspection    = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name='pallets')
    zip_photos    = models.FileField(upload_to='zips/pallets', null=True, blank=True)

class PalletPhoto(models.Model):
    pallet      = models.ForeignKey(Pallet, on_delete=models.CASCADE, related_name='photos')
    image       = models.ImageField(upload_to=inspection_photo_upload_path, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

# 7. Погрузка товара
class ProductLoading(models.Model):
    inspection           = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name="product_loading")
    mushroom_temperature = models.FloatField("Температура гриба, °C", null=True, blank=True)
    thermometer = models.ForeignKey(Thermometer, on_delete=models.PROTECT, blank=True, null=True)
    car_number           = models.CharField("Номер машины", max_length=20, null=True, blank=True)
    refrigerator_number  = models.CharField("Авторефрижератор", max_length=20, null=True, blank=True)
    seal_number          = models.CharField("Пломба SGS", max_length=50, null=True, blank=True)
    transport_temperature= models.FloatField("Температура транспортировки, °C", null=True, blank=True)
    zip_photos           = models.FileField(upload_to='zips/loading', null=True, blank=True)

class ProductLoadingPhoto(models.Model):
    loading     = models.ForeignKey(ProductLoading, on_delete=models.CASCADE, related_name='photos')
    image       = models.ImageField(upload_to=inspection_photo_upload_path, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
