"""URLs configuration for the mfe api."""

from django.urls import path

from lms.djangoapps.mfe_config_api.views import MFEConfigView, FrontendSiteConfigView

app_name = "mfe_config_api"
urlpatterns = [
    path("", MFEConfigView.as_view(), name="config"),
    path(
        "/frontend_site", FrontendSiteConfigView.as_view(), name="frontend_site_config"
    ),
]
