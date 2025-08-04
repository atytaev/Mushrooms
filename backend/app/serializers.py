import zipfile, os
from io import BytesIO
from django.core.files.base import ContentFile
from rest_framework import serializers
from .models import *
from django.conf import settings

# 1. Размещение
class MushroomPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MushroomPhoto
        fields = ('id','image')

class ProductMarkingPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductMarkingPhoto
        fields = ('id', 'image', 'uploaded_at')

class ThermometerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Thermometer
        fields = ['id', 'info', 'serial', 'calibration_date']

class MushroomStorageSerializer(serializers.ModelSerializer):
    zip_photos = serializers.FileField(required=False, write_only=True)
    photos = MushroomPhotoSerializer(many=True, read_only=True)
    thermometer = serializers.PrimaryKeyRelatedField(
        queryset=Thermometer.objects.all(),
        allow_null=True,
        required=False
    )
    thermometer_info = ThermometerSerializer(source='thermometer', read_only=True)

    class Meta:
        model = MushroomStorage
        exclude = ['inspection']

    def create(self, validated_data):
        zip_file = validated_data.pop('zip_photos', None)
        storage = MushroomStorage.objects.create(**validated_data)
        if zip_file:
            with zipfile.ZipFile(zip_file) as zf:
                for name in zf.namelist():
                    if name.lower().endswith(('.jpg','.png','.jpeg')):
                        data = zf.read(name)
                        fn = os.path.basename(name)
                        photo = MushroomPhoto(storage=storage)
                        photo.image.save(fn, ContentFile(data), save=True)
        return storage

# 2. Маркировка
class ProductMarkingZipSerializer(serializers.ModelSerializer):
    zip_photos = serializers.FileField(write_only=True)

    class Meta:
        model = ProductMarkingZip
        fields = ('zip_photos',)

    def create(self, validated_data):
        zip_file = validated_data.pop('zip_photos')
        obj = ProductMarkingZip.objects.create(**validated_data)
        with zipfile.ZipFile(zip_file) as zf:
            for name in zf.namelist():
                if name.lower().endswith(('.jpg','.png')):
                    data = zf.read(name)
                    fn = os.path.basename(name)
                    pm = ProductMarkingPhoto(inspection=obj.inspection)
                    pm.image.save(fn, ContentFile(data), save=True)
        return obj

class ScaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scale
        fields = ['id', 'model', 'serial_number', 'calibration_date']

# 3. Количество
class BoxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Box
        fields = ('net_weight','defect_weight')

class QuantityInspectionPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuantityInspectionPhoto
        fields = ('id', 'image', 'uploaded_at')

class QuantityInspectionSerializer(serializers.ModelSerializer):
    boxes = BoxSerializer(many=True)
    photos = QuantityInspectionPhotoSerializer(many=True, read_only=True)
    zip_photos = serializers.FileField(required=False, write_only=True)
    scale = serializers.PrimaryKeyRelatedField(queryset=Scale.objects.all(), allow_null=True, required=False)

    class Meta:
        model = QuantityInspection
        fields = ('id', 'zip_photos', 'boxes', 'photos', 'scale')

    def create(self, validated_data):
        # извлекаем архив
        zip_file = validated_data.pop('zip_photos', None)

        # создаём саму QuantityInspection
        boxes_data = validated_data.pop('boxes', [])
        qi = QuantityInspection.objects.create(**validated_data)

        # создаём Box
        for box in boxes_data:
            Box.objects.create(quantity_inspection=qi, **box)

        # распаковываем фото из архива, если он был
        if zip_file:
            import zipfile
            from django.core.files.base import ContentFile

            with zipfile.ZipFile(zip_file) as zf:
                for name in zf.namelist():
                    if name.lower().endswith(('.jpg', '.jpeg', '.png')):
                        data = zf.read(name)
                        fn = os.path.basename(name)
                        ph = QuantityInspectionPhoto(quantity_inspection=qi)
                        ph.image.save(fn, ContentFile(data), save=True)

        return qi

# 4. Качество
class QualityInspectionPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualityInspectionPhoto
        fields = ('id', 'image', 'uploaded_at')


class QualityInspectionSerializer(serializers.ModelSerializer):
    zip_photos = serializers.FileField(required=False, write_only=True)
    class Meta:
        model = QualityInspection
        exclude = ['inspection']
    def create(self, validated_data):
        zip_file = validated_data.pop('zip_photos', None)
        ql = QualityInspection.objects.create(**validated_data)
        if zip_file:
            with zipfile.ZipFile(zip_file) as zf:
                for name in zf.namelist():
                    if name.lower().endswith(('.jpg','.png')):
                        data = zf.read(name)
                        fn = os.path.basename(name)
                        ph = QualityInspectionPhoto(quality_inspection=ql)
                        ph.image.save(fn, ContentFile(data), save=True)
        return ql

# 5. Диаметр
class DiameterMeasurementSerializer(serializers.ModelSerializer):
    zip_photos = serializers.FileField(required=False, write_only=True)
    class Meta:
        model = DiameterMeasurement
        exclude = ['inspection']
    def create(self, validated_data):
        zip_file = validated_data.pop('zip_photos', None)
        dm = DiameterMeasurement.objects.create(**validated_data)
        if zip_file:
            with zipfile.ZipFile(zip_file) as zf:
                for name in zf.namelist():
                    if name.lower().endswith(('.jpg','.png')):
                        data = zf.read(name)
                        fn = os.path.basename(name)
                        ph = DiameterMeasurementPhoto(diameter_measurement=dm)
                        ph.image.save(fn, ContentFile(data), save=True)
        return dm

# 6. Паллеты
class PalletSerializer(serializers.ModelSerializer):
    zip_photos = serializers.FileField(required=False, write_only=True)

    class Meta:
        model = Pallet
        exclude = ['inspection']  # Исключаем поля, которые не должны быть переданы

    def create(self, validated_data):
        print("1. Вызван метод create для паллеты с данными:", validated_data)

        zip_file = validated_data.pop('zip_photos', None)
        print(f"2. Zip файл: {zip_file}")

        # Создаем паллету
        pal = Pallet.objects.create(**validated_data)
        print(f"3. Паллет с id {pal.id} успешно создан.")

        # Проверяем, если есть zip-файл, распаковываем и сохраняем фотографии
        if zip_file:
            print("4. Zip файл найден, начинаем распаковку...")

            try:
                # Убедитесь, что директория существует
                directory = os.path.join(settings.MEDIA_ROOT, 'zips/pallets')
                os.makedirs(directory, exist_ok=True)
                print(f"5. Директория для сохранения файлов: {directory}")

                # Распаковка zip-файла
                with zipfile.ZipFile(zip_file) as zf:
                    print(f"6. Содержимое zip-файла: {zf.namelist()}")
                    for name in zf.namelist():
                        if name.lower().endswith(('.jpg', '.png')):  # Проверка на изображение
                            print(f"7. Обрабатываем файл: {name}")
                            data = zf.read(name)
                            fn = os.path.basename(name)

                            # Сохраняем каждое изображение
                            ph = PalletPhoto(pallet=pal)
                            ph.image.save(fn, ContentFile(data), save=True)
                            print(f"8. Фотография {fn} успешно сохранена.")

            except zipfile.BadZipFile as e:
                print(f"9. Ошибка при открытии ZIP-файла: {e}")
            except Exception as e:
                print(f"10. Ошибка при сохранении изображения: {e}")

        else:
            print("11. Zip файл не передан.")

        return pal


# 7. Погрузка (ZIP & обычные фото)
class ProductLoadingPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductLoadingPhoto
        fields = ('id','image')

class ProductLoadingSerializer(serializers.ModelSerializer):
    thermometer = serializers.PrimaryKeyRelatedField(
        queryset=Thermometer.objects.all(),
        allow_null=True,
        required=False
    )
    zip_photos = serializers.FileField(required=False, write_only=True)
    photos = ProductLoadingPhotoSerializer(many=True, required=False)

    class Meta:
        model = ProductLoading
        exclude = ['inspection']

    def create(self, validated_data):
        zip_file = validated_data.pop('zip_photos', None)
        photos   = validated_data.pop('photos', [])
        pl = ProductLoading.objects.create(**validated_data)
        for p in photos:
            ProductLoadingPhoto.objects.create(loading=pl, **p)
        if zip_file:
            with zipfile.ZipFile(zip_file) as zf:
                for name in zf.namelist():
                    if name.lower().endswith(('.jpg','.png')):
                        data = zf.read(name)
                        fn = os.path.basename(name)
                        ph = ProductLoadingPhoto(loading=pl)
                        ph.image.save(fn, ContentFile(data), save=True)
        return pl

class PalletPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PalletPhoto
        fields = ('id', 'image', 'uploaded_at', 'pallet')

# Главный сериализатор
class FullInspectionSerializer(serializers.ModelSerializer):
    inspector = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        write_only=True
    )
    inspector_name = serializers.SerializerMethodField(read_only=True)
    car_number = serializers.SerializerMethodField(read_only=True)
    mushroom_storage      = MushroomStorageSerializer(many=True)
    marking_zips          = ProductMarkingZipSerializer(many=True, required=False)
    quantity_inspections  = QuantityInspectionSerializer(many=True, required=False)
    quality_inspections   = QualityInspectionSerializer(many=True, required=False)
    diameter_measurements = DiameterMeasurementSerializer(many=True, required=False)
    pallets               = PalletSerializer(many=True, required=False)
    product_loading       = ProductLoadingSerializer(many=True, required=False)

    class Meta:
        model = Inspection
        fields = '__all__'

    def get_inspector_name(self, obj):
        return obj.inspector.get_full_name()

    def get_car_number(self, obj):
        # берём первую (или единственную) запись из product_loading
        loading = obj.product_loading.first()
        return loading.car_number if loading else None
        # не забываем вернуть значение!

    def create(self, validated_data):
        sections = {
            'mushroom_storage':      (MushroomStorageSerializer,   'mushroom_storage'),
            'marking_zips':          (ProductMarkingZipSerializer, 'marking_zips'),
            'quantity_inspections':  (QuantityInspectionSerializer,'quantity_inspections'),
            'quality_inspections':   (QualityInspectionSerializer, 'quality_inspections'),
            'diameter_measurements': (DiameterMeasurementSerializer,'diameter_measurements'),
            'pallets':               (PalletSerializer,            'pallets'),
            'product_loading':       (ProductLoadingSerializer,    'product_loading'),
        }
        user = validated_data.pop('inspector')
        inspection = Inspection.objects.create(
            inspection_date= validated_data.pop('inspection_date'),
            inspector=user,
            job_number     = validated_data.pop('job_number'),
        )

        for key, (ser_cls, _) in sections.items():
            items = validated_data.pop(key, [])
            for item in items:
                item['inspection'] = inspection
                ser_cls().create(item)

        return inspection
