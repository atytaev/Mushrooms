from app.views import (
    FullInspectionCreateView,
    InspectionViewSet,
    MushroomStorageViewSet,
    get_token_and_user_id,
    check_token,
    ProductMarkingZipViewSet,
    GenerateReportView,
    ProductMarkingPhotoViewSet,
    QuantityInspectionPhotoViewSet,
    QualityInspectionPhotoViewSet,
    PalletPhotoViewSet,
    ThermometerViewSet,
    ScaleViewSet
)

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'inspections', InspectionViewSet)
router.register(r'mushroom-storage', MushroomStorageViewSet)
router.register(r'marking-zips', ProductMarkingZipViewSet)
router.register(r'marking-photos', ProductMarkingPhotoViewSet)
router.register(r'quantity-photos', QuantityInspectionPhotoViewSet)
router.register(r'quality-photos', QualityInspectionPhotoViewSet)
router.register(r'pallet-photos', PalletPhotoViewSet)
router.register(r'thermometers', ThermometerViewSet)
router.register(r'scales', ScaleViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/full-inspection/', FullInspectionCreateView.as_view(), name='full-inspection'),
    path('api/token/', get_token_and_user_id, name='token'),
    path('api/token/check/', check_token, name='check-token'),
    path('generate-report/<int:inspection_id>/',
         GenerateReportView.as_view(),
         name='generate-report'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)