import demistomock as demisto
from CommonServerPython import *  # noqa # pylint: disable=unused-wildcard-import
from CommonServerUserPython import *  # noqa

import json
import requests
import traceback

from typing import Callable, Dict, Any, List, Optional

# Disable insecure warnings
requests.packages.urllib3.disable_warnings()  # pylint: disable=no-member

AnyDict = Dict[str, Any]

ListOfDicts = List[AnyDict]


class ArgumentValidator:
    SORT_PARAM_MAPPING = {
        'CreatedAt': 'createdAt',
        'UpdatedAt': 'updatedAt'
    }

    def __init__(self, args: AnyDict):
        self.args = args

    def validate_id(self, arg_name: str) -> str:
        raw_value = self.args.get(arg_name)

        try:
            if raw_value is None or not isinstance(raw_value, str):
                raise ValueError
            return raw_value
        except ValueError:
            raise ValueError('Invalid ID: "{}"="{}"'.format(arg_name, raw_value))

    def validate_boolean(self, arg_name: str, required: bool = False) -> Optional[bool]:
        """
        More verbose error message in case the user specifies an invalid boolean value.
        Clearly the `argToBoolean` function has been written by someone else than `arg_to_datetime`
        or `arg_to_number`.
        """
        raw_value = self.args.get(arg_name)

        try:
            if raw_value is not None:
                return argToBoolean(raw_value)
            if required:
                raise ValueError
            return raw_value
        except ValueError:
            raise ValueError('Invalid boolean: "{}"="{}"'.format(arg_name, raw_value))

    def validate_datetime(self, arg_name: str, required: bool = False) -> Optional[datetime]:
        raw_value = self.args.get(arg_name)
        return arg_to_datetime(raw_value, arg_name=arg_name, required=required)

    def validate_int(self, arg_name: str, required: bool = False) -> Optional[int]:
        raw_value = self.args.get(arg_name)
        return arg_to_number(raw_value, arg_name=arg_name, required=required)

    def validate_sort(self, arg_name: str, required: bool = False) -> Optional[str]:
        raw_value = self.args.get(arg_name)

        try:
            if raw_value is None:
                if required:
                    raise ValueError
                return raw_value
            is_reversed = raw_value[0] == '-'
            param = raw_value[1:] if is_reversed else raw_value
            value = self.SORT_PARAM_MAPPING[param]
        except (IndexError, KeyError, ValueError):
            raise ValueError('Invalid sorting parameter: "{}"="{}"'.format(arg_name, raw_value))

        return f'{value}_{"DESC" if is_reversed else "ASC"}'


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


class HoxhuntQueryException(Exception):
    pass


class CustomJSONEncoder(json.JSONEncoder):
    """
    By default, the requests library doesn't encode dates or datetimes to JSON when using the `json` keyword argument.
    Let's do that ourselves.
    """
    def default(self, o: Any) -> Any:
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


class HoxhuntAPIClient:
    AUTH_HEADER_NAME = 'Authorization'
    AUTH_TOKEN_TYPE = 'Authtoken'

    DEFAULT_SORT_BY = 'createdAt_ASC'
    MAX_PAGE_SIZE = 200

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
            """,
            getter_func=lambda response: response.get('currentUser', {})
        )

    def do_fetch_incidents_request(
            self,
            search: str = None,
            filters: AnyDict = None,
            sort: str = None,
            first: int = None,
            skip: int = None
    ) -> ListOfDicts:
        filters = filters or {}

        return self._do_request(
            query="""
                query getIncidents(
                        $search: String,
                        $filter: Incident_filter,
                        $sort: [Incident_sort],
                        $first: Int,
                        $skip: Int
                ) {
                    incidents(
                            search: $search,
                            filter: $filter,
                            sort: $sort,
                            first: $first,
                            skip: $skip
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
            getter_func=lambda response: response.get('incidents', []),
            variables={
                'search': search,
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
                    **filters
                },
                **self._get_common_parameters(sort, first, skip)
            }
        )

    def do_fetch_incident_threats_request(
            self,
            incident_id: str,
            filters: AnyDict = None,
            sort: str = None,
            first: int = None,
            skip: int = None
    ) -> ListOfDicts:
        filters = filters or {}

        return self._do_request(
            query="""
                query getIncidentThreatsWithEnrichmentsAndModifiers(
                        $incident_filter: Incident_filter,
                        $threat_filter: Threat_filter,
                        $sort: [Threat_sort],
                        $first: Int,
                        $skip: Int
                ) {
                    incidents(filter: $incident_filter) {
                        _id
                        humanReadableId
                        threats(
                                filter: $threat_filter,
                                sort: $sort,
                                first: $first,
                                skip: $skip
                        ) {
                            _id
                            createdAt
                            updatedAt
                            email {
                                from {
                                    address
                                    name
                                }
                                attachments {
                                    name
                                    type
                                    hash
                                    size
                                }
                            }
                            enrichments {
                                hops {
                                    from
                                    by
                                }
                                links {
                                    href
                                    label
                                }
                            }
                            userModifiers {
                                userActedOnThreat
                                repliedToEmail
                                downloadedFile
                                openedAttachment
                                visitedLink
                                enteredCredentials
                                userMarkedAsSpam
                                other
                            }
                        }
                    }
                }
            """,
            getter_func=lambda response: response.get('incidents', []).pop().get('threats', []),
            variables={
                'incident_filter': {'humanReadableId_eq': incident_id},
                'threat_filter': filters,
                **self._get_common_parameters(sort, first, skip)
            }
        )

    def _get_common_parameters(self, sort: str = None, first: int = None, skip: int = None) -> AnyDict:
        return {
            'sort': sort or self.DEFAULT_SORT_BY,
            'first': first or self.MAX_PAGE_SIZE,
            'skip': skip or 0
        }

    def _do_request(
            self,
            query: str,
            getter_func: Callable,
            variables: AnyDict = None
    ) -> ListOfDicts:
        """
        Note:
            This method feeds the request body to `requests.post` using the `data` keyword argument instead of `json`.
            This is because we need to override the JSON encoder class, which `requests` doesn't allow out of the box.
            This is why the Content-Type header is also set explicitly - it'd be set automatically otherwise.
        """
        data = json.dumps(
            obj={'query': query, 'variables': variables or {}},
            cls=CustomJSONEncoder
        )
        headers = {
            self.AUTH_HEADER_NAME: f'{self.AUTH_TOKEN_TYPE} {self.api_key}',
            'Content-Type': 'application/json'
        }

        try:
            response = requests.post(
                url=self.api_url,
                data=data,
                headers=headers
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise HoxhuntAPIException(e)

        parsed_response = response.json()
        data, errors = parsed_response.get('data'), parsed_response.get('errors')

        if errors:
            raise HoxhuntQueryException([err['message'].split('\n')[0] for err in errors])

        return getter_func(data)


def test_module_command(client: HoxhuntAPIClient):
    client.do_test_request()
    return 'ok'


def get_incidents_command(
        client: HoxhuntAPIClient,
        args: AnyDict,
        params: AnyDict
) -> CommandResults:
    args_validator = ArgumentValidator(args)
    params_validator = ArgumentValidator(params)

    is_escalated = args_validator.validate_boolean('is_escalated')
    search = f'{"is" if is_escalated else "not"}:escalated' if is_escalated is not None else None

    filters = {}

    first_reported_at = args_validator.validate_datetime('first_reported_at')
    last_reported_at = args_validator.validate_datetime('last_reported_at')

    if first_reported_at:
        filters['firstReportedAt_gte'] = first_reported_at
    if last_reported_at:
        filters['lastReportedAt_gte'] = last_reported_at

    sort_by = args_validator.validate_sort('sort_by') or client.DEFAULT_SORT_BY
    page_size = args_validator.validate_int('page_size') or params_validator.validate_int('max_fetch') or client.MAX_PAGE_SIZE
    page = args_validator.validate_int('page') or 1

    hoxhunt_incidents = client.do_fetch_incidents_request(
        search=search,
        filters=filters,
        sort=sort_by,
        first=page_size,
        skip=(page - 1) * page_size
    )

    return CommandResults(
        outputs_prefix='Hoxhunt.Incident',
        outputs_key_field='humanReadableId',
        outputs=hoxhunt_incidents
    )


def get_incident_threats_command(
        client: HoxhuntAPIClient,
        args: AnyDict,
        params: AnyDict
) -> CommandResults:
    args_validator = ArgumentValidator(args)
    params_validator = ArgumentValidator(params)

    incident_id = args_validator.validate_id('incident_id')

    sort_by = args_validator.validate_sort('sort_by') or client.DEFAULT_SORT_BY
    page_size = args_validator.validate_int('page_size') or params_validator.validate_int('max_fetch') or client.MAX_PAGE_SIZE
    page = args_validator.validate_int('page') or 1

    hoxhunt_threats = client.do_fetch_incident_threats_request(
        incident_id=incident_id,
        sort=sort_by,
        first=page_size,
        skip=(page - 1) * page_size
    )

    return CommandResults(
        outputs_prefix='Hoxhunt.Threat',
        outputs_key_field='_id',
        outputs=hoxhunt_threats
    )


def main() -> None:
    command = demisto.command()
    params = demisto.params()
    args = demisto.args()

    client = HoxhuntAPIClient(
        api_url=params.get('api_url'),
        api_key=params.get('api_key')
    )

    try:

        demisto.debug(f'Command being called is {command}')

        if command == 'test-module':
            msg = test_module_command(client)
            return_results(msg)

        elif command == 'hoxhunt-get-incidents':
            return_results(
                results=get_incidents_command(
                    client=client,
                    args=args,
                    params=params
                )
            )

        elif command == 'hoxhunt-get-incident-threats':
            return_results(
                results=get_incident_threats_command(
                    client,
                    args=args,
                    params=params
                )
            )

    except Exception as e:
        demisto.error(traceback.format_exc())
        return_error(f'Failed to execute {command} command.\nError:\n{str(e)}')


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
