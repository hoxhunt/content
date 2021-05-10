test_module_result = {
    'data': {
        'currentUser': {
            'emails': {
                'address': 'test_user@example.com'
            }
        }
    }
}

get_incidents_result = {
    'data': {
        'incidents': [
            {
                '_id': 'zxc12rregsdf',
                'humanReadableId': 'hox-dangerous-incident-1',
                'createdAt': '2020-06-04T13:42:26.173Z',
                'updatedAt': '2020-06-04T13:42:26.173Z',
                'firstReportedAt': '2020-06-04T13:42:26.173Z',
                'lastReportedAt': '2020-06-04T13:42:26.173Z',
                'type': 'CAMPAIGN',
                'severity': 'PHISH',
                'state': 'OPEN',
                'threatCount': 10,
                'escalation': {
                    'escalatedAt': '2020-06-04T13:42:26.173Z',
                    'escalationThreshold': 5
                }
            }
        ]
    }
}

get_incident_threats_result = {
    'data': {
        'incidents': [
            {
                **{
                    key: value for key, value
                    in get_incidents_result['data']['incidents'][0].items()
                    if key in ('_id', 'humanReadableId')
                },
                'threats': [
                    {
                        '_id': 'rth675iofjy',
                        'createdAt': '2020-06-04T13:42:26.173Z',
                        'updatedAt': '2020-06-04T13:42:26.173Z',
                        'severity': get_incidents_result['data']['incidents'][0]['severity'],
                        'email': {
                            'from': [
                                {
                                    'name': 'Bad Guy',
                                    'address': 'suspicious.email@example.com'
                                }
                            ],
                            'attachments': [
                                {
                                    'name': 'this-is-definitely-not-a-virus.zip',
                                    'type': 'application/zip',
                                    'hash': 'f87c4bd3b606b34fdcef2b3f01bc0e9f',
                                    'size': 32
                                }
                            ]
                        },
                        'enrichments': {
                            'hops': [
                                {
                                    'From': 'malware-server.com:1234',
                                    'By': 'other-malware-server.com:4321'
                                }
                            ],
                            'links': [
                                {
                                    'Href': 'https://free-cat-pictures.xyz/register',
                                    'Label': 'CLICK HERE FOR FREE HD CAT PICS!!'
                                }
                            ],
                        },
                        'userModifiers': {
                            'userActedOnThreat': True,
                            'repliedToEmail': None,
                            'downloadedFile': True,
                            'openedAttachment': False,
                            'visitedLink': None,
                            'enteredCredentials': True,
                            'userMarkedAsSpam': False,
                            'other': True
                        }
                    }
                ]
            }
        ]
    }
}
