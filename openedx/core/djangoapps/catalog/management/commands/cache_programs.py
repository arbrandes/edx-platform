import logging

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import BaseCommand

from openedx.core.djangoapps.catalog.models import CatalogIntegration
from openedx.core.djangoapps.catalog.utils import create_catalog_api_client
from openedx.core.lib.edx_api_utils import traverse_pagination


logger = logging.getLogger(__name__)
User = get_user_model()  # pylint: disable=invalid-name

PROGRAM_UUIDS_KEY = 'program_uuids'


class Command(BaseCommand):
    """Management command used to cache program data.

    This command requests every available program from the discovery
    service, caching each in its own cache entry with an indefinite expiration.
    It is meant to be run on a scheduled basis and should be the only code
    updating these cache entries.
    """
    help = 'Backpopulate missing program credentials.'

    def add_arguments(self, parser):
        parser.add_argument(
            '-c', '--commit',
            action='store_true',
            dest='commit',
            default=False,
            help='Write data to Memcached.'
        )

    def handle(self, *args, **options):
        logger.info('Requesting programs from the discovery service.')

        catalog_integration = CatalogIntegration.current()
        username = catalog_integration.service_username

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            logger.exception('Service user {} does not exist.'.format(username))

        client = create_catalog_api_client(user, catalog_integration)

        querystring = {
            'exclude_utm': 1,
            'status': ('active', 'retired',),
        }

        endpoint = getattr(client, 'programs')
        response = endpoint.get(**querystring)

        results = traverse_pagination(response, endpoint, querystring, [])
        # TODO: Prefix these keys.
        programs = {result['uuid']: result for result in results}

        cache.set(PROGRAM_UUIDS_KEY, list(programs.keys()), None)
