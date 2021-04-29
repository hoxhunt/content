# Hoxhunt

Use the Hoxhunt integration to ingest user-reported phishing, email compromise, or other similar incidents.

This integration is tested with **VERSION** of Hoxhunt's API. 

## Configure Hoxhunt on Cortex XSOAR

1. Navigate to **Settings** > **Integrations** > **Servers & Services**.
2. Search for Hoxhunt.
3. Click **Add instance** to create and configure a new integration instance.

| **Parameter** | **Description** | **Required** | **Notes** |
| --- | --- | --- | --- |
| `api_key` | Your personal API token, created in Hoxhunt settings. | Yes | API keys are environment-specific. If you override `api_url`, you have to specify the correct key. |
| `api_url` | Hoxhunt API URL. | No | Defaults to https://app.hoxhunt.com/graphql-external. Provide only if you want to test the integration against some other environment. |
| `max_fetch` | Maximum amount of objects that the integration commands can fetch at once. | No | Defaults to `200`. Using a larger value can cause problems with your integration instance, according to XSOAR's documentation. |

4. Click **Test** to validate the API url and token. A successful test command means that the integration can fetch the
email address set in your Hoxhunt profile.
   
## Commands

You can execute these commands from the Demisto CLI, as part of an automation, or in a playbook. After you successfully execute a command, a DBot message appears in the War Room with the command details.

### hoxhunt-get-incidents
***

Runs a query that fetches a list of Incident objects.

#### Base command

`hoxhunt-get-incidents`

#### Input

By default, Incidents are filtered using the following parameters:

- Type - either `USER_ACTED_ON_THREAT`, `BUSINESS_EMAIL_COMPROMISE`, or `CAMPAIGN`
- Severity - either `PHISH`, `SPEAR`, or `COMPROMISED_EMAIL`
- State - only `OPEN` Incidents are returned

You can also provide additional filter arguments:

| **Argument Name** | **Description** | **Required** |
| --- | --- | --- |
| is_escalated | Whether the command should fetch Incidents escalated by Hoxhunt or not. Use a boolean value, or leave empty to fetch both escalated and non-escalated Incidents. | No |
| first_reported_at | Filter Incidents that were first reported after this time. | No | 
| last_reported_at | Filter Incidents that were last reported after this time. | No |
| sort_by | Field to sort Incidents by. Possible values: `CreatedAt`, `UpdatedAt`. Prefix with `-` for reverse order. `CreatedAt` by default (oldest by creation first). | No |
| page_size | Amount of Incidents to fetch at once. Defaults to the global `max_fetch` value. | No | 
| page | Set of Incidents to fetch. Defaults to `1`. | No |

You can use timeago-style timestamps for parameters, for example: `2 weeks`, `1 month`.

#### Command Example

```!hoxhunt-get-incidents is_escalated="true" last_reported_at="2 months" page_size="50" page="2" sort_by="-CreatedAt"```

#### Context Output

| **Path** | **Type** | **Description** |
| --- | --- | --- |
| Hoxhunt.Incident.Id | string | Machine-generated ID of the Incident. |
| Hoxhunt.Incident.HumanReadableId | string | Human-readable ID of the Incident. |
| Hoxhunt.Incident.CreatedAt | string | ISO 8601 timestamp string of when the Incident was created. | 
| Hoxhunt.Incident.UpdatedAt | string | ISO 8601 timestamp string of when the Incident was last updated. | 
| Hoxhunt.Incident.FirstReportedAt | string | ISO 8601 timestamp string of when the Incident was first reported. | 
| Hoxhunt.Incident.LastUpdatedAt | string | ISO 8601 timestamp string of when the Incident was last reported. | 
| Hoxhunt.Incident.Type | string | Incident type. | 
| Hoxhunt.Incident.Severity | string | Incident severity. | 
| Hoxhunt.Incident.State | string | Incident state (always `OPEN`). | 
| Hoxhunt.Incident.ThreatCount | number | Amount of Threats associated with this Incident. | 
| Hoxhunt.Incident.EscalatedAt | string | ISO 8601 timestamp string of when the Incident was escalated by Hoxhunt. If the Incident is not escalated, this field is `null`. | 
| Hoxhunt.Incident.EscalationThreshold | number | The amount of Threats that caused the Incident to be escalated. If the Incident is not escalated, or if its `Type` is `USER_ACTED_ON_THREAT`, this field is `null`. | 

#### Context Example

```json
{
    "Hoxhunt": {
        "Incident": [
            {
                "Id": "zxc12rregsdf",
                "HumanReadableId": "hox-dangerous-incident-1",
                "CreatedAt": "2020-06-04T13:42:26.173Z",
                "UpdatedAt": "2020-06-04T13:42:26.173Z",
                "FirstReportedAt": "2020-06-04T13:42:26.173Z",
                "LastReportedAt": "2020-06-04T13:42:26.173Z",
                "Type": "CAMPAIGN",
                "Severity": "PHISH",
                "State": "OPEN",
                "ThreatCount": 10,
                "EscalatedAt": "2020-06-04T13:42:26.173Z",
                "EscalationThreshold": 5
            }
        ]
    }
}
```

#### Human Readable Output

>### Incidents:
>|Id|HumanReadableId|CreatedAt|UpdatedAt|FirstReportedAt|LastReportedAt|Type|Severity|State|ThreatCount|EscalatedAt|EscalationThreshold|
>|---|---|---|---|---|---|---|---|---|---|---|---|
>| zxc12rregsdf | hox-hungry-mongoose-12 | 2020-06-04T13:42:26.173Z | 2020-06-04T13:42:26.173Z | 2020-06-04T13:42:26.173Z | 2020-06-04T13:42:26.173Z | CAMPAIGN | PHISH | OPEN | 10 | 2020-06-04T13:42:26.173Z | 5 |

### hoxhunt-get-incident-threats
***

Runs a query that fetches a list of Threat objects associated with an Incident.

#### Base command

`hoxhunt-get-incident-threats`

#### Input

| **Argument Name** | **Description** | **Required** |
| --- | --- | --- |
| incident_id | The human-readable ID of the Incident you wish to query Threats for. | Yes |
| sort_by | Field to sort Threats by. Possible values: `CreatedAt`, `UpdatedAt`. `CreatedAt` by default (oldest first by creation). Prefix with `-` for newest-first order. | No |
| page_size | Amount of Threats to fetch at once. Defaults to the global `max_fetch` value. | No | 
| page | Set of Threats to fetch. Defaults to `1`. | No |

#### Command Example

```!hoxhunt-get-incident-threats incident_id="hox-dangerous-incident-1"```

#### Context Output

| **Path** | **Type** | **Description** |
| --- | --- | --- |
| Hoxhunt.Threat.Id | string | Machine-generated ID of the Threat. | 
| Hoxhunt.Threat.CreatedAt | string | ISO 8601 timestamp string of when the Threat was created. | 
| Hoxhunt.Threat.UpdatedAt | string | ISO 8601 timestamp string of when the Threat was last updated. |
| Hoxhunt.Threat.Severity | string | The Threat's severity. Possible values are the same as with Incidents. |
| Hoxhunt.Threat.From.Name | string | An email sender name field value. |
| Hoxhunt.Threat.From.Address | string | An email sender address field value. |
| Hoxhunt.Threat.Attachments.Name | string | An attachment file name value. |
| Hoxhunt.Threat.Attachments.Type | string | An attachment content type value. |
| Hoxhunt.Threat.Attachments.Hash | string | An attachment content hash value. |
| Hoxhunt.Threat.Attachments.Size | number | An attachment content size in bytes. |
| Hoxhunt.Threat.Hops.From | string | The address the hop originated from. |
| Hoxhunt.Threat.Hops.By | string | The address the hop was directed to. |
| Hoxhunt.Threat.Links.Href | string | A possibly malicious link value. |
| Hoxhunt.Threat.Links.Label | string | A possibly malicious link label value. |
| Hoxhunt.Threat.UserModifiers.ActedOnThreat | boolean | Whether the user acted on the threat. |
| Hoxhunt.Threat.UserModifiers.RepliedToEmail | boolean | Whether the user replied to the email message. |
| Hoxhunt.Threat.UserModifiers.DownloadedFile | boolean | Whether the user downloaded an attachment. |
| Hoxhunt.Threat.UserModifiers.OpenedAttachment | boolean | Whether the user opened a downloaded attachment. |
| Hoxhunt.Threat.UserModifiers.VisitedLink | boolean | Whether the user visited a link in the email message. |
| Hoxhunt.Threat.UserModifiers.EnteredCredentials | boolean | Whether the user entered their credentials to a page they opened from a link in the email message. |
| Hoxhunt.Threat.UserModifiers.MarkedAsSpam | boolean | Whether the user marked the email message as spam. |
| Hoxhunt.Threat.UserModifiers.Other | boolean | Whether the user reacted to the email message in some other way. |

#### Context Example

```json
{
    "Hoxhunt": {
        "Threat": [
            {
                "Id": "rth675iofjy",
                "CreatedAt": "2020-06-04T13:42:26.173Z",
                "UpdatedAt": "2020-06-04T13:42:26.173Z",
                "Severity": "PHISH",
                "From": {
                  "Name": "Bad Guy",
                  "Address": "suspicious.email@example.com"
                },
                "Attachments": [
                  {
                    "Name": "this-is-definitely-not-a-virus.zip",
                    "Type": "application/zip",
                    "Hash": "f87c4bd3b606b34fdcef2b3f01bc0e9f",
                    "Size": 32
                  }
                ],
                "Hops": [
                  {
                    "From": "malware-server.com:1234",
                    "By": "other-malware-server.com:4321"
                  }
                ],
                "Links": [
                  {
                    "Href": "https://free-cat-pictures.xyz/register",
                    "Label": "CLICK HERE FOR FREE HD CAT PICS!!"
                  }
                ],
                "UserModifiers": {
                  "ActedOnThreat": true,
                  "RepliedToEmail": true,
                  "DownloadedFile": true,
                  "OpenedAttachment": true,
                  "VisitedLink": true,
                  "EnteredCredentials": true,
                  "MarkedAsSpam": false,
                  "Other": true
                }
            }
        ]
    }
}
```

#### Human Readable Output

>### Incidents:
>|Id|CreatedAt|UpdatedAt|Severity|From|Attachments|Hops|Links|UserModifiers|
>|---|---|---|---|---|---|---|---|---|
>| zxc12rregsdf | 2020-06-04T13:42:26.173Z | 2020-06-04T13:42:26.173Z | PHISH | {"Name": "Bad Guy", "Address": "suspicious.email@example.com"} | [{"Name": "this-is-definitely-not-a-virus.zip", "Type": "application/zip", "Hash": "f87c4bd3b606b34fdcef2b3f01bc0e9f", "Size": 32}] | [{"From": "malware-server.com:1234", "By": "other-malware-server.com:4321"}] | [{"Href": "https://free-cat-pictures.xyz/register", "Label": "CLICK HERE FOR FREE HD CAT PICS!!"}] | {"ActedOnThreat": true, "RepliedToEmail": true, "DownloadedFile": true, "OpenedAttachment": true, "VisitedLink": true, "EnteredCredentials": true, "MarkedAsSpam": false, "Other": true} |
