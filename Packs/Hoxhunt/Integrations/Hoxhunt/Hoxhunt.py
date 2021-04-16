#import demistomock as demisto
from Packs.HelloWorld.Integrations.HelloWorld.CommonServerPython import *  # noqa # pylint: disable=unused-wildcard-import
from Packs.HelloWorld.Integrations.HelloWorld.CommonServerUserPython import *  # noqa

import datetime
import json
import requests
import traceback

from typing import Callable, Dict, Any, List, Optional, Tuple, Union

# Disable insecure warnings
requests.packages.urllib3.disable_warnings()  # pylint: disable=no-member

AnyDict = Dict[str, Any]

ListOfDicts = List[AnyDict]
DictOrListOfDicts = Union[AnyDict, ListOfDicts]


class ArgumentValidator:
    SORT_PARAM_MAPPING = {
        'CreatedAt': 'createdAt',
        'UpdatedAt': 'updatedAt'
    }

    def __init__(self, args: AnyDict):
        self.args = args

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
            if arg_name:
                raise ValueError('Invalid boolean: "{}"="{}"'.format(arg_name, raw_value))
            else:
                raise ValueError('"{}" is not a valid boolean'.format(raw_value))

    def validate_datetime(self, arg_name: str, required: bool = False) -> Optional[datetime.datetime]:
        raw_value = self.args.get(arg_name)
        return arg_to_datetime(raw_value, arg_name=arg_name, required=required)

    def validate_int(self, arg_name: str, required: bool = False) -> Optional[int]:
        raw_value = self.args.get(arg_name)
        return arg_to_number(raw_value, arg_name=arg_name, required=required)

    def validate_sort(self, arg_name: str = None, required: bool = False):
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
            if arg_name:
                raise ValueError('Invalid sorting parameter: "{}"="{}"'.format(arg_name, raw_value))
            else:
                raise ValueError('"{}" is not a valid sorting parameter'.format(raw_value))

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


class Commands:
    TEST_MODULE = 'test-module'
    HOXHUNT_FETCH_INCIDENTS = 'hoxhunt-fetch-incidents'
    HOXHUNT_FETCH_INCIDENT_THREATS = 'hoxhunt-fetch-incident-threats'


class CommandOutputs:
    INCIDENT = 'Hoxhunt.Incident'
    THREAT = 'Hoxhunt.Threat'


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
        if isinstance(o, datetime.datetime):
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
        sort = sort or self.DEFAULT_SORT_BY
        first = first or self.MAX_PAGE_SIZE
        skip = skip or 0

        return self._do_request(
            query="""
                query getIncidents(
                        $search: String,
                        $filter: Incident_filter,
                        $first: Int,
                        $sort: [Incident_sort],
                        $after: ID
                ) {
                    incidents(
                            search: $search,
                            filter: $filter, 
                            first: $first, 
                            sort: $sort,
                            after: $after
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
                'sort': sort,
                'first': first,
                'skip': skip
            }
        )

    def do_fetch_incident_threats_request(
            self,
            incident_id: str,
            page_size: int = None,
            since: str = None,
            until: str = None
    ) -> ListOfDicts:
        timestamp_filter = {}

        if since:
            timestamp_filter['createdAt_gte'] = since
        if until:
            timestamp_filter['createdAt_lte'] = until

        return self._do_request(
            query="""
                query getIncidentThreatsWithEnrichmentsAndModifiers(
                        $filter: Incident_filter,
                        $first: Int,
                        $skip: Int,
                        $sort: [Incident_sort]
                ) {
                    incidents(
                            filter: $filter,
                            first: $first,
                            skip: $skip,
                            sort: $sort
                    ) {
                        _id
                        humanReadableId
                        threats {
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
                            }
                        }
                    }
                }
            """,
            getter_func=lambda response: response.get('incidents', []).pop().get('threats', []),
            variables={
                'filter': {
                    'humanReadableId_eq': incident_id
                },
                # 'threatFilter': timestamp_filter,
                'first': page_size or self.MAX_PAGE_SIZE,
                'sort': 'updatedAt_ASC'
            }
        )

    def _do_request(
            self,
            query: str,
            getter_func: Callable,
            variables: AnyDict = None
    ) -> DictOrListOfDicts:
        """
        Note:
            This method feeds the request body to `requests.post` using the `data` keyword argument instead of `json`.
            This is because we need to override the JSON encoder class, which `requests` doesn't allow out of the box.
            This is why the Content-Type header is also set explicitly - it'd be set automatically otherwise.
        """
        try:
            response = requests.post(
                url=self.api_url,
                data=json.dumps(
                    obj={
                        'query': query,
                        'variables': variables or {}
                    },
                    cls=CustomJSONEncoder
                ),
                headers={
                    self.AUTH_HEADER_NAME: f'{self.AUTH_TOKEN_TYPE} {self.api_key}',
                    'Content-Type': 'application/json'
                }
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
        filters['first_reported_at_gte'] = first_reported_at
    if last_reported_at:
        filters['last_reported_at_gte'] = last_reported_at

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
        outputs_prefix=CommandOutputs.INCIDENT,
        outputs_key_field='humanReadableId',
        outputs=hoxhunt_incidents
    )


def get_incident_threats_command(
        client: HoxhuntAPIClient,
        args: AnyDict,
        params: AnyDict
) -> CommandResults:
    incident_id = args.get('incident_id')

    page_size = params.get('page_size')
    since = args.get('since_time')
    until = args.get('until_time')

    hoxhunt_threats = client.do_fetch_incident_threats_request(
        incident_id=incident_id,
        page_size=page_size,
        since=since,
        until=until
    )

    return CommandResults(
        outputs_prefix=CommandOutputs.THREAT,
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

        if command == Commands.TEST_MODULE:
            msg = test_module_command(client)
            return_results(msg)

        elif command == Commands.HOXHUNT_FETCH_INCIDENTS:
            return_results(
                results=get_incidents_command(
                    client=client,
                    args=args,
                    params=params
                )
            )

        elif command == Commands.HOXHUNT_FETCH_INCIDENT_THREATS:
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
