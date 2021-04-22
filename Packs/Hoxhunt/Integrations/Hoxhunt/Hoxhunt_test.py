import datetime
import json
from copy import deepcopy

import dateparser
import pytest


DATEPARSER_SETTINGS = {
    'TIMEZONE': 'UTC'
}

TEST_CLIENT_KWARGS = {
    'api_key': 'test_api_key',
    'api_url': 'https://app.hoxhunt.dev/graphql-external'
}


def _values_match_on_minute_level(expected: datetime.datetime, actual: datetime.datetime) -> bool:
    def strip(val):
        return val.replace(second=0, microsecond=0)
    return strip(expected) == strip(actual)


def test_to_camel_case():
    from Hoxhunt import to_camel_case
    assert 'thisIsTheKey' == to_camel_case('ThisIsTheKey')

    with pytest.raises(IndexError):
        to_camel_case('')


def test_to_pascal_case():
    from Hoxhunt import to_pascal_case
    assert 'ThisIsTheKey' == to_pascal_case('thisIsTheKey')

    with pytest.raises(IndexError):
        to_pascal_case('')


def test_argument_validator_id_validation():
    from Hoxhunt import ArgumentValidator

    raw_value = '1234'
    value = ArgumentValidator({'id': raw_value}).validate_id('id')
    assert raw_value == value

    with pytest.raises(ValueError):
        ArgumentValidator({'id': 1234}).validate_id('id')

    with pytest.raises(ValueError):
        ArgumentValidator({}).validate_id('id')


def test_argument_validator_boolean_validation_required():
    from Hoxhunt import ArgumentValidator

    true_values = (True, 'true', 'True', 'yes')
    false_values = (False, 'false', 'False', 'no')

    for expected_value, raw_values in (
            (True, true_values),
            (False, false_values)
    ):
        for raw_value in raw_values:
            value = ArgumentValidator({'bool': raw_value}).validate_boolean('bool', required=True)
            assert expected_value == value

    invalid_values = (1, '1', 0, '0')

    for raw_value in invalid_values:
        with pytest.raises(ValueError):
            ArgumentValidator({'bool': raw_value}).validate_boolean('bool', required=True)

    with pytest.raises(ValueError):
        ArgumentValidator({}).validate_boolean('bool', required=True)


def test_argument_validator_boolean_validation_optional():
    from Hoxhunt import ArgumentValidator

    true_values = (True, 'true', 'True', 'yes')
    false_values = (False, 'false', 'False', 'no')

    for expected_value, raw_values in (
            (True, true_values),
            (False, false_values)
    ):
        for raw_value in raw_values:
            value = ArgumentValidator({'bool': raw_value}).validate_boolean('bool')
            assert expected_value == value

    invalid_values = (1, '1', 0, '0')

    for raw_value in invalid_values:
        with pytest.raises(ValueError):
            ArgumentValidator({'bool': raw_value}).validate_boolean('bool')

    value = ArgumentValidator({}).validate_boolean('bool')
    assert value is None


def test_argument_validator_datetime_validation_required():
    from Hoxhunt import ArgumentValidator

    two_weeks_ago = dateparser.parse('2 weeks', settings=DATEPARSER_SETTINGS)
    month_ago = dateparser.parse('1 month', settings=DATEPARSER_SETTINGS)
    beginning_of_this_month = datetime.datetime.now()

    for expected_value, raw_value in (
            (two_weeks_ago, '2 weeks'),
            (month_ago, '1 month'),
            (beginning_of_this_month, beginning_of_this_month.isoformat())
    ):
        value = ArgumentValidator({'dt': raw_value}).validate_datetime('dt', required=True)

        is_match = _values_match_on_minute_level(expected_value, value)
        assert is_match is True

    with pytest.raises(ValueError):
        ArgumentValidator({'dt': 'invalid'}).validate_datetime('dt', required=True)

    with pytest.raises(ValueError):
        ArgumentValidator({}).validate_datetime('dt', required=True)


def test_argument_validator_datetime_validation_optional():
    from Hoxhunt import ArgumentValidator

    two_weeks_ago = dateparser.parse('2 weeks', settings=DATEPARSER_SETTINGS)
    month_ago = dateparser.parse('1 month', settings=DATEPARSER_SETTINGS)
    beginning_of_this_month = datetime.datetime.now()

    for expected_value, raw_value in (
            (two_weeks_ago, '2 weeks'),
            (month_ago, '1 month'),
            (beginning_of_this_month, beginning_of_this_month.isoformat())
    ):
        value = ArgumentValidator({'dt': raw_value}).validate_datetime('dt')

        is_match = _values_match_on_minute_level(expected_value, value)
        assert is_match is True

    with pytest.raises(ValueError):
        ArgumentValidator({'dt': 'invalid'}).validate_datetime('dt')

    value = ArgumentValidator({}).validate_datetime('dt')
    assert value is None


def test_argument_validator_number_validation_required():
    from Hoxhunt import ArgumentValidator

    for raw_value in (1234, '1234'):
        expected_value = int(raw_value)

        value = ArgumentValidator({'num': raw_value}).validate_int('num', required=True)
        assert expected_value == value

    with pytest.raises(ValueError):
        ArgumentValidator({'num': 'invalid'}).validate_int('num', required=True)

    with pytest.raises(ValueError):
        ArgumentValidator({}).validate_datetime('num', required=True)


def test_argument_validator_number_validation_optional():
    from Hoxhunt import ArgumentValidator

    for raw_value in (1234, '1234'):
        expected_value = int(raw_value)

        value = ArgumentValidator({'num': raw_value}).validate_int('num')
        assert expected_value == value

    with pytest.raises(ValueError):
        ArgumentValidator({'num': 'invalid'}).validate_int('num')

    value = ArgumentValidator({}).validate_datetime('num')
    assert value is None


def test_argument_validator_sort_validation_required():
    from Hoxhunt import ArgumentValidator

    for field_name in ArgumentValidator.SORT_PARAM_MAPPING.keys():
        for raw_value in (field_name, f'-{field_name}'):
            expected_field_name = ArgumentValidator.SORT_PARAM_MAPPING[field_name]
            is_reversed = raw_value[0] == '-'

            value = ArgumentValidator({'sort': raw_value}).validate_sort('sort', required=True)
            assert f'{expected_field_name}_{"DESC" if is_reversed else "ASC"}' == value

    with pytest.raises(ValueError):
        ArgumentValidator({'sort': 'InvalidField'}).validate_sort('sort', required=True)

    with pytest.raises(ValueError):
        field_name_with_appended_dash = f'{list(ArgumentValidator.SORT_PARAM_MAPPING.keys())[0]}-'
        ArgumentValidator({'sort': field_name_with_appended_dash}).validate_sort('sort', required=True)

    with pytest.raises(ValueError):
        ArgumentValidator({}).validate_sort('sort', required=True)


def test_argument_validator_sort_validation_optional():
    from Hoxhunt import ArgumentValidator

    for field_name in ArgumentValidator.SORT_PARAM_MAPPING.keys():
        for raw_value in (field_name, f'-{field_name}'):
            expected_field_name = ArgumentValidator.SORT_PARAM_MAPPING[field_name]
            is_reversed = raw_value[0] == '-'

            value = ArgumentValidator({'sort': raw_value}).validate_sort('sort')
            assert f'{expected_field_name}_{"DESC" if is_reversed else "ASC"}' == value

    with pytest.raises(ValueError):
        ArgumentValidator({'sort': 'InvalidField'}).validate_sort('sort')

    with pytest.raises(ValueError):
        field_name_with_appended_dash = f'{list(ArgumentValidator.SORT_PARAM_MAPPING.keys())[0]}-'
        ArgumentValidator({'sort': field_name_with_appended_dash}).validate_sort('sort')

    value = ArgumentValidator({}).validate_sort('sort')
    assert value is None


def test_custom_json_encoder():
    from Hoxhunt import CustomJSONEncoder

    volatile_dict = {'dt': datetime.datetime.now()}

    json_result = json.dumps(volatile_dict, cls=CustomJSONEncoder)
    assert 'dt' in json_result

    with pytest.raises(TypeError):
        json.dumps(volatile_dict)


def test_convert_incident_func():
    from Hoxhunt import convert_incident
    from test_data.data import get_incidents_result

    expected_keys = {
        'Id', 'HumanReadableId', 'CreatedAt', 'UpdatedAt', 'FirstReportedAt', 'LastReportedAt', 'Type', 'Severity',
        'State', 'ThreatCount', 'EscalatedAt', 'EscalationThreshold'
    }

    hoxhunt_incident = get_incidents_result['data']['incidents'][0]
    xsoar_incident = convert_incident(hoxhunt_incident)

    assert expected_keys == set(xsoar_incident.keys())
    assert xsoar_incident['EscalatedAt'] == hoxhunt_incident['escalation']['escalatedAt']
    assert xsoar_incident['EscalationThreshold'] == hoxhunt_incident['escalation']['escalationThreshold']

    non_escalated_hoxhunt_incident = deepcopy(hoxhunt_incident)
    non_escalated_hoxhunt_incident.update({'escalation': None})
    non_escalated_xsoar_incident = convert_incident(non_escalated_hoxhunt_incident)

    assert expected_keys == set(non_escalated_xsoar_incident.keys())
    assert non_escalated_xsoar_incident['EscalatedAt'] is None
    assert non_escalated_xsoar_incident['EscalationThreshold'] is None


def test_convert_threat_func():
    from Hoxhunt import convert_threat
    from test_data.data import get_incident_threats_result

    expected_keys = {
        'Id', 'CreatedAt', 'UpdatedAt', 'Severity', 'From', 'Attachments', 'Hops', 'Links', 'UserModifiers'
    }
    from_expected_keys = {'Name', 'Address'}
    attachments_expected_keys = {'Name', 'Type', 'Hash', 'Size'}
    hops_expected_keys = {'From', 'By'}
    links_expected_keys = {'Href', 'Label'}
    user_modifiers_expected_keys = {
        'ActedOnThreat', 'RepliedToEmail', 'DownloadedFile', 'OpenedAttachment', 'VisitedLink',
        'EnteredCredentials', 'MarkedAsSpam', 'Other'
    }

    def _compare_keys(actual):
        assert expected_keys == set(actual.keys())
        assert from_expected_keys == set(actual['From'].keys())
        assert attachments_expected_keys == set(actual['Attachments'][0].keys())
        assert hops_expected_keys == set(actual['Hops'][0].keys())
        assert links_expected_keys == set(actual['Links'][0].keys())
        assert user_modifiers_expected_keys == set(actual['UserModifiers'].keys())

    hoxhunt_threat = get_incident_threats_result['data']['incidents'][0]['threats'][0]
    xsoar_threat = convert_threat(hoxhunt_threat)

    _compare_keys(xsoar_threat)
    assert list(xsoar_threat['UserModifiers'].values()) == list(hoxhunt_threat['userModifiers'].values())

    without_user_modifiers_hoxhunt_threat = deepcopy(hoxhunt_threat)
    without_user_modifiers_hoxhunt_threat.update({'userModifiers': None})
    without_user_modifiers_xsoar_threat = convert_threat(without_user_modifiers_hoxhunt_threat)

    _compare_keys(without_user_modifiers_xsoar_threat)
    assert all(
        without_user_modifiers_xsoar_threat['UserModifiers'][attr] is False
        for attr in user_modifiers_expected_keys
    )


def test_hoxhunt_test_module_command(requests_mock):
    from Hoxhunt import HoxhuntAPIClient, test_module_command
    from test_data.data import test_module_result

    client = HoxhuntAPIClient(**TEST_CLIENT_KWARGS)
    requests_mock.post(client.api_url, json=test_module_result)

    result = test_module_command(client)
    assert result == 'ok'


def test_hoxhunt_get_incidents_command(requests_mock):
    from Hoxhunt import HoxhuntAPIClient, convert_incident, get_incidents_command
    from test_data.data import get_incidents_result

    client = HoxhuntAPIClient(**TEST_CLIENT_KWARGS)
    requests_mock.post(client.api_url, json=get_incidents_result)

    results = get_incidents_command(client, args={}, params={})

    raw_response = get_incidents_result['data']['incidents']
    outputs = [convert_incident(incident) for incident in raw_response]

    assert results.outputs_prefix == 'Hoxhunt.Incident'
    assert results.outputs_key_field == 'HumanReadableId'
    assert results.outputs == outputs
    assert results.raw_response == raw_response


def test_hoxhunt_get_incident_threats_command(requests_mock):
    from Hoxhunt import HoxhuntAPIClient, convert_threat, get_incident_threats_command
    from test_data.data import get_incident_threats_result

    client = HoxhuntAPIClient(**TEST_CLIENT_KWARGS)
    requests_mock.post(client.api_url, json=get_incident_threats_result)

    incident = get_incident_threats_result['data']['incidents'][0]

    results = get_incident_threats_command(client, args={
        'incident_id': incident['humanReadableId']
    }, params={})

    raw_response = incident['threats']
    outputs = [convert_threat(threat) for threat in raw_response]

    assert results.outputs_prefix == 'Hoxhunt.Threat'
    assert results.outputs_key_field == 'Id'
    assert results.outputs == outputs
    assert results.raw_response == raw_response
