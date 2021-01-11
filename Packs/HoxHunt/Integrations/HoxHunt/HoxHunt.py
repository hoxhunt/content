import json

import demistomock as demisto
from CommonServerPython import *  # noqa # pylint: disable=unused-wildcard-import
from CommonServerUserPython import *  # noqa

import dateparser
import requests
import traceback

from typing import Dict, Any, List, Tuple

# Disable insecure warnings
requests.packages.urllib3.disable_warnings()  # pylint: disable=no-member


''' CONSTANTS '''

DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

''' CLIENT CLASS '''


StrDict = Dict[str, str]
AnyDict = Dict[str, Any]


class HoxHuntException(Exception):
    def __init__(self, err: requests.exceptions.HTTPError):
        super().__init__(err)
        self.status_code = err.response.status_code
        self.response = err.response.json()

    def __str__(self):
        return f'<HTTP {self.status_code}>: {self.response}'


class HoxHuntAPIClient:
    AUTH_HEADER_NAME = 'Authorization'
    AUTH_TOKEN_TYPE = 'Authtoken'

    DEFAULT_SORT = 'createdAt_ASC'

    def __init__(self, api_url: str, api_key: str):
        super().__init__()
        self.api_url = api_url
        self.api_key = api_key

    def do_test_request(self) -> None:
        self._do_request(
            query="""
            query getMe {
                currentUser {
                    emails {
                        address
                    }
                }
            }
            """
        )

    def do_get_incidents_request(self, page_size: int) -> List[AnyDict]:
        response = self._do_request(
            query="""
                query getIncidentsBasicInfo($first: Int, $sort: String) {
                    incidents(first: $first, sort: $sort) {
                        _id
                        createdAt
                        updatedAt
                        lastReportedAt
                        humanReadableId
                        policyName
                        severity
                        state
                        threatCount
                    }
                }
            """,
            variables={
                'first': page_size,
                'sort': self.DEFAULT_SORT
            }
        )

        return response['incidents']

    def _do_request(self, query: str, variables: AnyDict = None) -> AnyDict:
        try:
            response = requests.post(
                url=self.api_url,
                json={
                    'query': query,
                    'variables': variables or {}
                },
                headers={
                    self.AUTH_HEADER_NAME: f'{self.AUTH_TOKEN_TYPE} {self.api_key}'
                }
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise HoxHuntException(e)

        return response.json()['data']


def test_module_command(client: HoxHuntAPIClient):
    client.do_test_request()
    return 'ok'


def fetch_incidents_command(
        client: HoxHuntAPIClient,
        last_run: StrDict,
        command_args: AnyDict
) -> Tuple[StrDict, List[AnyDict]]:

    since_time = command_args.get('since_time')
    page_size = command_args.get('page_size')

    last_fetch_str = last_run.get('last_fetch')
    last_fetch = None

    if last_fetch_str:
        last_fetch = dateparser.parse(last_fetch_str)
    elif since_time:
        last_fetch = dateparser.parse(since_time)

    latest_created_at = last_fetch

    xsoar_incidents = []
    hoxhunt_incidents = client.do_get_incidents_request(page_size=page_size)

    for hoxhunt_incident in hoxhunt_incidents:
        created_at = dateparser.parse(hoxhunt_incident['createdAt'])

        xsoar_incident = {
            'name': hoxhunt_incident['humanReadableId'],
            'occurred': created_at.strftime(DATE_FORMAT),
            'rawJSON': json.dumps(hoxhunt_incident)
        }

        xsoar_incidents.append(xsoar_incident)

        if not latest_created_at or (created_at > latest_created_at):
            latest_created_at = created_at

    next_run = {'last_fetch': latest_created_at.strftime(DATE_FORMAT)}

    return next_run, xsoar_incidents


def main() -> None:
    api_url = demisto.params().get('api_url')
    api_key = demisto.params().get('api_key')

    command = demisto.command()

    demisto.debug(f'Command being called is {command}')

    client = HoxHuntAPIClient(
        api_url=api_url,
        api_key=api_key
    )

    try:

        if command == 'test-module':
            msg = test_module_command(client)
            return_results(msg)

        elif command == 'fetch-incidents':
            last_run = demisto.getLastRun()
            command_args = demisto.args()

            next_run, incidents = fetch_incidents_command(
                client=client,
                last_run=last_run,
                command_args=command_args
            )

            demisto.setLastRun(next_run)
            demisto.incidents(incidents)

    except Exception as e:
        demisto.error(traceback.format_exc())
        return_error(f'Failed to execute {command} command.\nError:\n{str(e)}')


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
