"""
MFE API Views for useful information related to mfes.
"""

import edx_api_doc_tools as apidocs
from django.conf import settings
from django.http import HttpResponseNotFound, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import status
from rest_framework.views import APIView

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


def get_legacy_config() -> dict:
    """
    Return legacy configuration values available in either site configuration or django settings.
    """
    return {
        "ENABLE_COURSE_SORTING_BY_START_DATE": configuration_helpers.get_value(
            "ENABLE_COURSE_SORTING_BY_START_DATE",
            settings.FEATURES["ENABLE_COURSE_SORTING_BY_START_DATE"],
        ),
        "HOMEPAGE_PROMO_VIDEO_YOUTUBE_ID": configuration_helpers.get_value(
            "homepage_promo_video_youtube_id", None
        ),
        "HOMEPAGE_COURSE_MAX": configuration_helpers.get_value(
            "HOMEPAGE_COURSE_MAX", settings.HOMEPAGE_COURSE_MAX
        ),
        "COURSE_ABOUT_TWITTER_ACCOUNT": configuration_helpers.get_value(
            "course_about_twitter_account", settings.PLATFORM_TWITTER_ACCOUNT
        ),
        "NON_BROWSABLE_COURSES": not settings.FEATURES.get("COURSES_ARE_BROWSABLE"),
        "ENABLE_COURSE_DISCOVERY": settings.FEATURES["ENABLE_COURSE_DISCOVERY"],
    }


def get_mfe_config() -> dict:
    """Return common MFE configuration from settings or site configuration.

    Returns:
        A dictionary of configuration values shared across all MFEs.
    """
    mfe_config = (
        configuration_helpers.get_value("MFE_CONFIG", settings.MFE_CONFIG) or {}
    )
    if not isinstance(mfe_config, dict):
        return {}
    return mfe_config


def get_mfe_config_overrides() -> dict:
    """Return all MFE-specific overrides from settings or site configuration.

    Returns:
        A dictionary keyed by MFE name, where each value is a dict of
        per-MFE overrides.  Non-dict entries are filtered out.
    """
    mfe_config_overrides = (
        configuration_helpers.get_value(
            "MFE_CONFIG_OVERRIDES",
            settings.MFE_CONFIG_OVERRIDES,
        )
        or {}
    )
    if not isinstance(mfe_config_overrides, dict):
        return {}

    return {
        name: overrides
        for name, overrides in mfe_config_overrides.items()
        if isinstance(overrides, dict)
    }


class MFEConfigView(APIView):
    """
    Provides an API endpoint to get the MFE configuration from settings (or site configuration).
    """

    @method_decorator(cache_page(settings.MFE_CONFIG_API_CACHE_TIMEOUT))
    @apidocs.schema(
        parameters=[
            apidocs.query_parameter(
                "mfe",
                str,
                description="Name of an MFE (a.k.a. an APP_ID).",
            ),
        ],
    )
    def get(self, request):
        """
        Return the MFE configuration, optionally including MFE-specific overrides.

        This configuration currently also pulls specific settings from site configuration or
        django settings. This is a temporary change as a part of the migration of some legacy
        pages to MFEs. This is a temporary compatibility layer which will eventually be deprecated.

        See [DEPR ticket](https://github.com/openedx/edx-platform/issues/37210) for more details.

        The compatibility means that settings from the legacy locations will continue to work but
        the settings listed below in the `get_legacy_config` function should be added to the MFE
        config by operators.

        **Usage**

          Get common config:
          GET /api/mfe_config/v1

          Get app config (common + app-specific overrides):
          GET /api/mfe_config/v1?mfe=name_of_mfe

        **GET Response Values**
        ```
        {
            "BASE_URL": "https://name_of_mfe.example.com",
            "LANGUAGE_PREFERENCE_COOKIE_NAME": "example-language-preference",
            "CREDENTIALS_BASE_URL": "https://credentials.example.com",
            "DISCOVERY_API_BASE_URL": "https://discovery.example.com",
            "LMS_BASE_URL": "https://courses.example.com",
            "LOGIN_URL": "https://courses.example.com/login",
            "LOGOUT_URL": "https://courses.example.com/logout",
            "STUDIO_BASE_URL": "https://studio.example.com",
            "LOGO_URL": "https://courses.example.com/logo.png",
            "ENABLE_COURSE_SORTING_BY_START_DATE": True,
            "HOMEPAGE_COURSE_MAX": 10,
            ... and so on
        }
        ```
        """

        if not settings.ENABLE_MFE_CONFIG_API:
            return HttpResponseNotFound()

        mfe_name = (
            str(request.query_params.get("mfe"))
            if request.query_params.get("mfe")
            else None
        )

        merged_config = (
            get_legacy_config()
            | get_mfe_config()
            | get_mfe_config_overrides().get(mfe_name, {})
        )

        return JsonResponse(merged_config, status=status.HTTP_200_OK)


# Translation map from legacy SCREAMING_SNAKE_CASE MFE_CONFIG keys to
# camelCase field names matching frontend-base's RequiredSiteConfig and
# OptionalSiteConfig interfaces.
# See https://github.com/openedx/frontend-base/blob/main/types.ts
SITE_CONFIG_TRANSLATION_MAP = {
    # RequiredSiteConfig
    "SITE_NAME": "siteName",
    "BASE_URL": "baseUrl",
    "LMS_BASE_URL": "lmsBaseUrl",
    "LOGIN_URL": "loginUrl",
    "LOGOUT_URL": "logoutUrl",
    # OptionalSiteConfig
    "LOGO_URL": "headerLogoImageUrl",
    "ACCESS_TOKEN_COOKIE_NAME": "accessTokenCookieName",
    "LANGUAGE_PREFERENCE_COOKIE_NAME": "languagePreferenceCookieName",
    "USER_INFO_COOKIE_NAME": "userInfoCookieName",
    "CSRF_TOKEN_API_PATH": "csrfTokenApiPath",
    "REFRESH_ACCESS_TOKEN_API_PATH": "refreshAccessTokenApiPath",
    "SEGMENT_KEY": "segmentKey",
}


def mfe_name_to_app_id(mfe_name: str) -> str:
    """Convert a legacy MFE name to a frontend-base appId.

    Converts kebab-case MFE names (e.g. ``"learner-dashboard"``) to
    reverse-domain appIds (e.g. ``"org.openedx.frontend.app.learnerDashboard"``).
    """
    parts = mfe_name.split("-")
    camel_case = parts[0] + "".join(part.capitalize() for part in parts[1:])
    return f"org.openedx.frontend.app.{camel_case}"


class FrontendSiteConfigView(APIView):
    """
    Provides an API endpoint intended for frontend site configuration.

    It exists to support incremental migration to a frontend-site-oriented config surface.
    """

    @method_decorator(cache_page(settings.MFE_CONFIG_API_CACHE_TIMEOUT))
    def get(self, request):
        """
        Return frontend site configuration as converted from legacy MFE configuration.

        Translates the flat SCREAMING_SNAKE_CASE ``MFE_CONFIG`` / ``MFE_CONFIG_OVERRIDES``
        settings into the camelCase structure expected by `frontend-base SiteConfig
        <https://github.com/openedx/frontend-base/blob/main/types.ts>`_.

        * Keys that correspond to ``RequiredSiteConfig`` or ``OptionalSiteConfig`` fields
          are promoted to the top level under their camelCase name.
        * All remaining keys become the base ``config`` for every app entry.
        * Each entry in ``MFE_CONFIG_OVERRIDES`` becomes an element of the ``apps`` array,
          with its override dict merged on top of the shared base config.

        **Usage**

          GET /api/mfe_config/v1/frontend_site

        **GET Response Values**
        ```
        {
            "siteName": "My Open edX Site",
            "baseUrl": "https://apps.example.com",
            "lmsBaseUrl": "https://courses.example.com",
            "loginUrl": "https://courses.example.com/login",
            "logoutUrl": "https://courses.example.com/logout",
            "headerLogoImageUrl": "https://courses.example.com/logo.png",
            "accessTokenCookieName": "edx-jwt-cookie-header-payload",
            "languagePreferenceCookieName": "openedx-language-preference",
            "userInfoCookieName": "edx-user-info",
            "csrfTokenApiPath": "/csrf/api/v1/token",
            "refreshAccessTokenApiPath": "/login_refresh",
            "segmentKey": null,
            "commonAppConfig": {
                "CREDENTIALS_BASE_URL": "https://credentials.example.com",
                "STUDIO_BASE_URL": "https://studio.example.com",
                ...
            },
            "apps": [
                {
                    "appId": "org.openedx.frontend.app.authn",
                    "config": {
                        "ACTIVATION_EMAIL_SUPPORT_LINK": null,
                        "ALLOW_PUBLIC_ACCOUNT_CREATION": true
                    }
                },
                {
                    "appId": "org.openedx.frontend.app.learnerDashboard",
                    "config": {
                        "LEARNING_BASE_URL": "http://apps.local.openedx.io:2000",
                        "ENABLE_PROGRAMS": false
                    }
                }
            ]
        }
        ```
        """
        if not settings.ENABLE_MFE_CONFIG_API:
            return HttpResponseNotFound()

        # Collect configuration from all sources.
        mfe_config = get_mfe_config()
        mfe_config_overrides = get_mfe_config_overrides()

        # Split MFE_CONFIG into site-level (translated to camelCase) and app-level.
        # Legacy config seeds common_app_config at lowest precedence.
        site_config = {}
        common_app_config = get_legacy_config()
        for key, value in mfe_config.items():
            if key in SITE_CONFIG_TRANSLATION_MAP:
                site_config[SITE_CONFIG_TRANSLATION_MAP[key]] = value
            else:
                common_app_config[key] = value

        # Always include the shared app config so that unmapped MFE_CONFIG
        # keys are available even when no per-app overrides are defined.
        site_config["commonAppConfig"] = common_app_config

        # Build the apps array: each app only gets its own overrides:
        # frontend-base merges commonAppConfig into each app's config.
        # Site-level keys are stripped from per-app overrides so they don't
        # leak into app config.
        apps = []
        for mfe_name in sorted(mfe_config_overrides):
            overrides = {
                k: v
                for k, v in mfe_config_overrides[mfe_name].items()
                if k not in SITE_CONFIG_TRANSLATION_MAP
            }
            apps.append(
                {
                    "appId": mfe_name_to_app_id(mfe_name),
                    "config": overrides,
                }
            )

        if apps:
            site_config["apps"] = apps

        return JsonResponse(site_config, status=status.HTTP_200_OK)
