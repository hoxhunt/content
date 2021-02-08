import demistomock as demisto
from CommonServerPython import *  # noqa # pylint: disable=unused-wildcard-import
from CommonServerUserPython import *  # noqa

import json
import dateparser
import requests
import traceback

from typing import Dict, Any, List, Optional, Tuple

# Disable insecure warnings
requests.packages.urllib3.disable_warnings()  # pylint: disable=no-member

DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

StrDict = Dict[str, str]
AnyDict = Dict[str, Any]


class IncidentStates:
    OPEN = 'OPEN'
    RESOLVED = 'RESOLVED'


class IncidentTypes:
    COMPROMISED_EMAIL = 'BUSINESS_EMAIL_COMPROMISE'
    CAMPAIGN = 'CAMPAIGN'
    USER_ACTED = 'USER_ACTED_ON_THREAT'


class IncidentSeverities:
    INCONCLUSIVE = 'INCONCLUSIVE'
    FALSE_POSITIVE = 'FALSE_POSITIVE'
    SPAM = 'SPAM'
    PHISHING = 'PHISH'
    SPEAR_PHISHING = 'SPEAR'
    COMPROMISED_EMAIL = 'COMPROMISED_EMAIL'


class HoxhuntAPIException(Exception):
    def __init__(self, err: requests.exceptions.HTTPError):
        super().__init__(err)
        self.status_code = err.response.status_code
        self.response = err.response.json()

    def __str__(self):
        return f'<HTTP {self.status_code}>: {self.response}'


class HoxhuntAPIClient:
    AUTH_HEADER_NAME = 'Authorization'
    AUTH_TOKEN_TYPE = 'Authtoken'

    DEFAULT_SORT_FIELD = 'updatedAt'

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

    def do_fetch_incidents_request(self, page_size: int, since: Optional[str]) -> List[AnyDict]:
        return self._do_request(
            query="""
                query getIncidentsBasicInfo(
                        $search: String,
                        $filter: Incident_filter,
                        $first: Int,
                        $sort: [Incident_sort]
                ) {
                    incidents(
                            search: $search,
                            filter: $filter, 
                            first: $first, 
                            sort: $sort
                    ) {
                        _id
                        createdAt
                        updatedAt
                        firstReportedAt
                        lastReportedAt
                        humanReadableId
                        policyName
                        severity
                        state
                        threatCount
                        escalation {
                            escalatedAt
                            creationThreshold
                        }
                    }
                }
            """,
            variables=self._get_incidents_query_variables(
                page_size=page_size,
                since=since
            )
        ) \
            .get('incidents')

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
            raise HoxhuntAPIException(e)

        return response.json().get('data')

    def _get_incidents_query_variables(self, page_size: int, since: Optional[str]) -> StrDict:
        timestamp_filter = {f'{self.DEFAULT_SORT_FIELD}_gt': since} if since else {}

        return {
            'search': 'is:escalated',
            'filter': {
                'policyName_in': [
                    IncidentTypes.COMPROMISED_EMAIL,
                    IncidentTypes.CAMPAIGN,
                    IncidentTypes.USER_ACTED
                ],
                'severity_in': [
                    IncidentSeverities.PHISHING,
                    IncidentSeverities.SPEAR_PHISHING,
                    IncidentSeverities.COMPROMISED_EMAIL
                ],
                'state_eq': IncidentStates.OPEN,
                **timestamp_filter
            },
            'first': page_size,
            'sort': f'{self.DEFAULT_SORT_FIELD}_ASC'
        }


def test_module_command(client: HoxhuntAPIClient):
    client.do_test_request()
    return 'ok'


def fetch_incidents_command(
        client: HoxhuntAPIClient,
        page_size: int,
        last_run: StrDict,
        since_time: Optional[str]
) -> Tuple[StrDict, List[AnyDict]]:
    last_fetch_str = last_run.get('last_fetch') or since_time
    last_fetch = dateparser.parse(last_fetch_str) if last_fetch_str else None

    xsoar_incidents = []
    latest_updated_at = last_fetch

    hoxhunt_incidents = client.do_fetch_incidents_request(
        page_size=page_size,
        since=last_fetch_str
    )

    for hoxhunt_incident in hoxhunt_incidents:
        updated_at = dateparser.parse(hoxhunt_incident['updatedAt'])

        xsoar_incident = {
            'name': hoxhunt_incident['humanReadableId'],
            'occurred': hoxhunt_incident['createdAt'],
            'rawJSON': json.dumps(hoxhunt_incident)
        }

        xsoar_incidents.append(xsoar_incident)

        if not latest_updated_at or (updated_at > latest_updated_at):
            latest_updated_at = updated_at

    next_run = {'last_fetch': latest_updated_at.strftime(DATE_FORMAT)}

    return next_run, xsoar_incidents


class Commands:
    TEST = 'test-module'
    FETCH_INCIDENTS = 'fetch-incidents'


def main() -> None:
    command = demisto.command()

    client = HoxhuntAPIClient(
        api_url=demisto.params().get('api_url'),
        api_key=demisto.params().get('api_key')
    )

    try:

        demisto.debug(f'Command being called is {command}')

        if command == Commands.TEST:
            msg = test_module_command(client)
            return_results(msg)

        elif command == Commands.FETCH_INCIDENTS:
            last_run = demisto.getLastRun()
            since_time = demisto.params().get('since_time')
            page_size = int(demisto.params().get('page_size'))

            next_run, incidents = fetch_incidents_command(
                client=client,
                page_size=page_size,
                last_run=last_run,
                since_time=since_time
            )

            demisto.setLastRun(next_run)
            demisto.incidents(incidents)

    except Exception as e:
        demisto.error(traceback.format_exc())
        return_error(f'Failed to execute {command} command.\nError:\n{str(e)}')


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
