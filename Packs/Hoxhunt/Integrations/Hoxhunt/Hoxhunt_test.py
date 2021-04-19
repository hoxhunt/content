import datetime

import dateparser
import pytest

from Hoxhunt import ArgumentValidator


def _values_match_on_minute_level(expected: datetime.datetime, actual: datetime.datetime) -> bool:
    def strip(val):
        return val.replace(second=0, microsecond=0)
    return strip(expected) == strip(actual)


def test_argument_validator_id_validation():
    raw_value = '1234'
    value = ArgumentValidator({'id': raw_value}).validate_id('id')
    assert raw_value == value

    with pytest.raises(ValueError):
        ArgumentValidator({'id': 1234}).validate_id('id')

    with pytest.raises(ValueError):
        ArgumentValidator({}).validate_id('id')


def test_argument_validator_boolean_validation_required():
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
    two_weeks_ago, month_ago = dateparser.parse('2 weeks'), dateparser.parse('1 month')
    beginning_of_this_month = datetime.datetime.now()

    for expected_value, raw_value in (
            (two_weeks_ago, '2 weeks'),
            (month_ago, '1 month'),
            (beginning_of_this_month, beginning_of_this_month.isoformat())
    ):
        value = ArgumentValidator({'dt': raw_value}).validate_datetime('dt', required=True)
        assert _values_match_on_minute_level(expected_value, value)

    with pytest.raises(ValueError):
        ArgumentValidator({'dt': 'invalid'}).validate_datetime('dt', required=True)

    with pytest.raises(ValueError):
        ArgumentValidator({}).validate_datetime('dt', required=True)


def test_argument_validator_datetime_validation_optional():
    two_weeks_ago, month_ago = dateparser.parse('2 weeks'), dateparser.parse('1 month')
    beginning_of_this_month = datetime.datetime.now()

    for expected_value, raw_value in (
            (two_weeks_ago, '2 weeks'),
            (month_ago, '1 month'),
            (beginning_of_this_month, beginning_of_this_month.isoformat())
    ):
        value = ArgumentValidator({'dt': raw_value}).validate_datetime('dt')
        assert _values_match_on_minute_level(expected_value, value)

    with pytest.raises(ValueError):
        ArgumentValidator({'dt': 'invalid'}).validate_datetime('dt')

    value = ArgumentValidator({}).validate_datetime('dt')
    assert value is None


def test_argument_validator_number_validation_required():
    for raw_value in (1234, '1234'):
        expected_value = int(raw_value)

        value = ArgumentValidator({'num': raw_value}).validate_int('num', required=True)
        assert expected_value == value

    with pytest.raises(ValueError):
        ArgumentValidator({'num': 'invalid'}).validate_int('num', required=True)

    with pytest.raises(ValueError):
        ArgumentValidator({}).validate_datetime('num', required=True)


def test_argument_validator_number_validation_optional():
    for raw_value in (1234, '1234'):
        expected_value = int(raw_value)

        value = ArgumentValidator({'num': raw_value}).validate_int('num')
        assert expected_value == value

    with pytest.raises(ValueError):
        ArgumentValidator({'num': 'invalid'}).validate_int('num')

    value = ArgumentValidator({}).validate_datetime('num')
    assert value is None


def test_argument_validator_sort_validation_required():
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
