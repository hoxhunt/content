import datetime
import json

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


def test_hoxhunt_test_module_command(requests_mock):
    from Hoxhunt import HoxhuntAPIClient, test_module_command
    from test_data.data import test_module_result

    client = HoxhuntAPIClient(**TEST_CLIENT_KWARGS)
    requests_mock.post(client.api_url, json=test_module_result)

    result = test_module_command(client)
    assert result == 'ok'


def test_hoxhunt_get_incidents_command(requests_mock):
    from Hoxhunt import HoxhuntAPIClient, get_incidents_command
    from test_data.data import get_incidents_result

    client = HoxhuntAPIClient(**TEST_CLIENT_KWARGS)
    requests_mock.post(client.api_url, json=get_incidents_result)

    results = get_incidents_command(client, args={}, params={})
    assert results.outputs_prefix == 'Hoxhunt.Incident'
    assert results.outputs_key_field == 'humanReadableId'
    assert results.outputs == get_incidents_result['data']['incidents']


def test_hoxhunt_get_incident_threats_command(requests_mock):
    from Hoxhunt import HoxhuntAPIClient, get_incident_threats_command
    from test_data.data import get_incident_threats_result

    client = HoxhuntAPIClient(**TEST_CLIENT_KWARGS)
    requests_mock.post(client.api_url, json=get_incident_threats_result)

    incident = get_incident_threats_result['data']['incidents'][0]

    results = get_incident_threats_command(client, args={
        'incident_id': incident['humanReadableId']
    }, params={})
    assert results.outputs_prefix == 'Hoxhunt.Threat'
    assert results.outputs_key_field == '_id'
    assert results.outputs == incident['threats']
