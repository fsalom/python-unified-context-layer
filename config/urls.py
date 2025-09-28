"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

import os

from commons_package.commons.url_error_responses import (url_400, url_403,
                                                         url_404, url_500)
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from oauth2_provider import urls as oauth2_urls

urlpatterns = [
    path('users/admin/', admin.site.urls),
    path("o/", include(oauth2_urls)),
    # path('api/', include('driving.api.urls')),
]

if not bool(int(os.environ.get('DEBUG', "0"))):
    handler400 = url_400
    handler403 = url_403
    handler404 = url_404
    handler500 = url_500

if bool(int(os.environ.get('DEBUG', "0"))):
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if bool(int(os.environ.get('HIDE_AUTH_MODELS', 0))):
    from django.contrib.auth.models import Group
    from oauth2_provider.models import (AccessToken, Application, Grant,
                                        IDToken, RefreshToken)
    from social_django.models import Association, Nonce, UserSocialAuth

    admin.site.unregister(AccessToken)
    admin.site.unregister(Grant)
    admin.site.unregister(IDToken)
    admin.site.unregister(RefreshToken)
    admin.site.unregister(Application)
    admin.site.unregister(Association)
    admin.site.unregister(Nonce)
    admin.site.unregister(UserSocialAuth)
