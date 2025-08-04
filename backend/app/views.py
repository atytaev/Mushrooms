# app/views.py
import json
import os
from io import BytesIO

from django.conf import settings
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    CustomUser,
    Inspection,
    MushroomStorage,
    ProductMarkingZip,
    ProductMarkingPhoto,
    QuantityInspectionPhoto,
    QualityInspectionPhoto,
    PalletPhoto,
    Thermometer,
    Scale
)

from .report_generator import generate_inspection_report
from .serializers import (
    FullInspectionSerializer,
    MushroomStorageSerializer,
    ProductMarkingZipSerializer,
    ProductMarkingPhotoSerializer,
    QuantityInspectionPhotoSerializer,
    QualityInspectionPhotoSerializer,
    PalletPhotoSerializer,
    ThermometerSerializer,
    ScaleSerializer
)

class ThermometerViewSet(viewsets.ModelViewSet):
    queryset = Thermometer.objects.all()
    serializer_class = ThermometerSerializer


class ScaleViewSet(viewsets.ModelViewSet):
    queryset = Scale.objects.all()
    serializer_class = ScaleSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def get_token_and_user_id(request):
    username = request.data.get('username')
    password = request.data.get('password')
    if not username or not password:
        return Response({"error": "username и password обязательны"}, status=400)
    try:
        user = CustomUser.objects.get(username=username)
        if not user.check_password(password):
            return Response({"error": "Неверный пароль"}, status=400)
    except CustomUser.DoesNotExist:
        return Response({"error": "Пользователь не найден"}, status=404)

    refresh = RefreshToken.for_user(user)
    return Response({
        "access_token": str(refresh.access_token),
        "refresh_token": str(refresh),
        "user_id": user.id,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
@authentication_classes([])
def check_token(request):
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return Response({"token_valid": False, "error": "No Bearer token provided"})
    token = auth.split(' ')[1]
    jwt = JWTAuthentication()
    try:
        validated = jwt.get_validated_token(token)
        user = jwt.get_user(validated)
        return Response({"token_valid": True, "user_id": user.id})
    except (InvalidToken, TokenError):
        return Response({"token_valid": False, "error": "Token is invalid"})


class FullInspectionCreateView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        flat = request.data
        files = request.FILES

        raw = flat.get('quantity_inspections')
        if raw:
            try:
                # Перезапишем пустой список в structured на разобранный JSON
                parsed = json.loads(raw)
            except ValueError:
                return Response({"error": "Invalid JSON in quantity_inspections"}, status=400)
        else:
            parsed = []
        # Собираем корневые поля
        structured = {
            "inspection_date": flat.get("inspection_date"),
            "inspector":       flat.get("inspector"),
            "job_number":      flat.get("job_number"),

            "mushroom_storage":      [],
            "marking_zips":          [],
            "quantity_inspections":  parsed,
            "quality_inspections":   [],
            "diameter_measurements": [],
            "pallets":               [],
            "product_loading":       [],
        }

        # 1. MushroomStorage
        i = 0
        while f"mushroom_storage[{i}].quantity_of_boxes" in flat:
            item = {
                "quantity_of_boxes": flat[f"mushroom_storage[{i}].quantity_of_boxes"],
                "quantity_of_pallets": flat[f"mushroom_storage[{i}].quantity_of_pallets"],
                "temperature_in_fridge": flat[f"mushroom_storage[{i}].temperature_in_fridge"],
                "mushroom_temperature_min": flat[f"mushroom_storage[{i}].mushroom_temperature_min"],
                "mushroom_temperature_max": flat[f"mushroom_storage[{i}].mushroom_temperature_max"],
                "thermometer": flat.get(f"mushroom_storage[{i}].thermometer"),
                "invoice_number": flat.get(f"mushroom_storage[{i}].invoice_number")
            }
            key = f"mushroom_storage[{i}].zip_photos"
            if key in files:
                item["zip_photos"] = files[key]
            structured["mushroom_storage"].append(item)
            i += 1

        # 2. marking_zips
        j = 0
        while f"marking_zips[{j}].zip_photos" in files:
            structured["marking_zips"].append({
                "zip_photos": files[f"marking_zips[{j}].zip_photos"]
            })
            j += 1

        # 3. quantity_inspections
        k = 0
        while (
                f"quantity_inspections[{k}].zip_photos" in files or
                any(f"quantity_inspections[{k}].boxes[{n}].net_weight" in flat for n in range(20))
        # на всякий случай ограничим range
        ):
            item = {}

            # zip
            key_zip = f"quantity_inspections[{k}].zip_photos"
            if key_zip in files:
                item["zip_photos"] = files[key_zip]

            # вытаскиваем коробки
            boxes = []
            n = 0
            while f"quantity_inspections[{k}].boxes[{n}].net_weight" in flat:
                box = {
                    "net_weight": flat[f"quantity_inspections[{k}].boxes[{n}].net_weight"],
                    "defect_weight": flat[f"quantity_inspections[{k}].boxes[{n}].defect_weight"],
                }
                boxes.append(box)
                n += 1
            item["boxes"] = boxes

            key_scale_prefix = f"quantity_inspections[{k}].scale"

            # Собираем данные по весам, если передаются как вложенный объект
            scale_data = {}
            for suffix in ['model', 'serial_number', 'calibration_date']:
                key = f"{key_scale_prefix}_{suffix}"
                if key in flat:
                    scale_data[suffix] = flat[key]

            if scale_data:
                # создаём или ищем Scale
                from .models import Scale
                scale_obj, created = Scale.objects.get_or_create(
                    model=scale_data.get('model', ''),
                    serial_number=scale_data.get('serial_number'),
                    calibration_date=scale_data.get('calibration_date')
                )
                item['scale'] = scale_obj.id

            structured["quantity_inspections"].append(item)
            k += 1

        # 4. quality_inspections
        l = 0
        # пока есть хоть одно поле из нашей группы
        while any([
            f"quality_inspections[{l}].zip_photos" in files,
            f"quality_inspections[{l}].sample_mass_kg" in flat,
            f"quality_inspections[{l}].conforms_to_declared_grade" in flat,
        ]):
            item = {}
            # ZIP
            key_zip = f"quality_inspections[{l}].zip_photos"
            if key_zip in files:
                item["zip_photos"] = files[key_zip]
            # масса объединённой пробы
            mass_key = f"quality_inspections[{l}].sample_mass_kg"
            if mass_key in flat:
                item["sample_mass_kg"] = flat[mass_key]
            # соответствие сорту
            grade_key = f"quality_inspections[{l}].conforms_to_declared_grade"
            if grade_key in flat:
                item["conforms_to_declared_grade"] = flat[grade_key]

            key_offgrade_50 = f"quality_inspections[{l}].off_grade_mass_kg_50"
            if key_offgrade_50 in flat:
                item["off_grade_mass_kg_50"] = flat[key_offgrade_50]

            key_offgrade_70 = f"quality_inspections[{l}].off_grade_mass_kg_70"
            if key_offgrade_70 in flat:
                item["off_grade_mass_kg_70"] = flat[key_offgrade_50]

            structured["quality_inspections"].append(item)
            l += 1

        # 5. diameter_measurements
        m = 0
        while f"diameter_measurements[{m}].average_diameter" in flat:
            item = {
                "average_diameter": flat[f"diameter_measurements[{m}].average_diameter"],
                "notes":             flat[f"diameter_measurements[{m}].notes"],
            }
            key = f"diameter_measurements[{m}].zip_photos"
            if key in files:
                item["zip_photos"] = files[key]
            structured["diameter_measurements"].append(item)
            m += 1

        # 6. Паллеты
        p = 0
        while f"pallets[{p}].zip_photos" in files:
            print(f"Обрабатываем паллеты для {p}")
            item = {}

            # Сохраняем только zip_photos для паллеты
            key_zip = f"pallets[{p}].zip_photos"
            if key_zip in files:
                item["zip_photos"] = files[key_zip]
                print(f"Zip файл для паллеты {p} найден.")

            structured["pallets"].append(item)
            p += 1

        # 7. product_loading
        q = 0
        while f"product_loading[{q}].mushroom_temperature" in flat:
            item = {
                "mushroom_temperature": flat[f"product_loading[{q}].mushroom_temperature"],
                "car_number":           flat[f"product_loading[{q}].car_number"],
                "refrigerator_number":  flat[f"product_loading[{q}].refrigerator_number"],
                "seal_number":          flat[f"product_loading[{q}].seal_number"],
                "transport_temperature":flat[f"product_loading[{q}].transport_temperature"],
                "thermometer": flat.get(f"product_loading[{q}].thermometer"),
            }
            key = f"product_loading[{q}].zip_photos"
            if key in files:
                item["zip_photos"] = files[key]
            structured["product_loading"].append(item)
            q += 1

        # Теперь у нас есть правильно вложенный словарь + файлы
        serializer = FullInspectionSerializer(data=structured)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Инспекция успешно создана'}, status=201)
        else:
            print(f"Ошибки сериализатора: {serializer.errors}")
            return Response(serializer.errors, status=400)



class InspectionViewSet(viewsets.ModelViewSet):
    queryset = Inspection.objects.all()
    serializer_class = FullInspectionSerializer


class MushroomStorageViewSet(viewsets.ModelViewSet):
    queryset = MushroomStorage.objects.all()
    serializer_class = MushroomStorageSerializer

    def get_queryset(self):
        inspection_id = self.request.query_params.get('inspection')
        if inspection_id:
            return self.queryset.filter(inspection_id=inspection_id)
        return self.queryset.none()  # или вообще все, если не передан параметр


class ProductMarkingZipViewSet(viewsets.ModelViewSet):
    """
    Этот ViewSet принимает ZIP-архивы с фото маркировки,
    распаковывает их и создаёт ProductMarkingPhoto.
    """
    queryset = ProductMarkingZip.objects.all()
    serializer_class = ProductMarkingZipSerializer


@method_decorator(csrf_exempt, name='dispatch')
class GenerateReportView(View):
    def post(self, request, inspection_id):
        body = json.loads(request.body or "{}")
        doc, inspection_date = generate_inspection_report(
            inspection_id,
            placement_ids=body.get("placement_photo_ids"),
            marking_ids=body.get("marking_photo_ids"),
            quantity_photo_ids=body.get("quantity_photo_ids"),
            quality_photo_ids=body.get("quality_photo_ids"),
            pallet_photo_ids=body.get("pallet_photo_ids"),
            loading_ids=body.get("loading_photo_ids"),
        )
        buf = BytesIO()
        doc.save(buf)
        buf.seek(0)

        save_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
        os.makedirs(save_dir, exist_ok=True)

        date_str = inspection_date.strftime('%Y-%m-%d')
        fn = f"{date_str}.docx"

        with open(os.path.join(save_dir, fn), 'wb') as f:
            f.write(buf.read())

        return HttpResponse(status=200)


class ProductMarkingPhotoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProductMarkingPhoto.objects.all()
    serializer_class = ProductMarkingPhotoSerializer

    def get_queryset(self):
        inspection_id = self.request.query_params.get('inspection')
        if inspection_id:
            return self.queryset.filter(inspection_id=inspection_id)
        return self.queryset

class QuantityInspectionPhotoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = QuantityInspectionPhoto.objects.all()
    serializer_class = QuantityInspectionPhotoSerializer

    def get_queryset(self):
        insp = self.request.query_params.get('inspection')
        qs = self.queryset
        if insp:
            qs = qs.filter(quantity_inspection__inspection_id=insp)
        else:
            print(">> No 'inspection' param, returning empty queryset")
            return qs.none()
        return qs


class QualityInspectionPhotoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = QualityInspectionPhoto.objects.all()
    serializer_class = QualityInspectionPhotoSerializer

    def get_queryset(self):
        insp = self.request.query_params.get('inspection')
        if insp:
            return self.queryset.filter(quality_inspection__inspection_id=insp)
        return self.queryset.none()


class PalletPhotoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PalletPhoto.objects.all()
    serializer_class = PalletPhotoSerializer

    def get_queryset(self):
        inspection_id = self.request.query_params.get('inspection')
        if inspection_id:
            # фильтруем по связанным паллетам данной инспекции
            return self.queryset.filter(pallet__inspection_id=inspection_id)
        return self.queryset.none()