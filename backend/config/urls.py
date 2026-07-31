from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/auth/', include('apps.accounts.urls')),
    path('api/developers/', include('apps.developers.urls')),
    path('api/projects/', include('apps.projects.urls')),
    path('api/announcements/', include('apps.govfeed.urls')),
    path('api/listings/', include('apps.listings.urls')),
    path('api/applications/', include('apps.applications.urls')),
    path('api/', include('apps.engagement.urls')),
    path('api/me/', include('apps.accounts.me_urls')),

    # OpenAPI Docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
