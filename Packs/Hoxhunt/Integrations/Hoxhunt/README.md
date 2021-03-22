# Hoxhunt

Use the Hoxhunt integration to ingest user-reported phishing, email compromise, or other similar incidents.

This integration is tested with **VERSION** of Hoxhunt's API. 

## Configure Hoxhunt on Cortex XSOAR

1. Navigate to **Settings** > **Integrations** > **Servers & Services**.
2. Search for Hoxhunt.
3. Click **Add instance** to create and configure a new integration instance.

| **Parameter** | **Description** | **Required** |
| --- | --- | --- |
| api_url | Hoxhunt's API URL \(e.g., https://domain-to-api.com/) | True |
| api_key | Your personal API token, created in Hoxhunt settings | True |
| max_fetch | Maximum amount of objects that the integration commands can fetch at once | True |

4. Click **Test** to validate the API url and token. A successful test command means that the integration can fetch the
email address set in your Hoxhunt profile.
   
**Note:** Cortex XSOAR recommends that no more than `200` objects should be fetched at once. Using a larger `max_fetch` value can cause problems with your integration instance.
   
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
| is_escalated | Whether the command should fetch Incidents escalated by Hoxhunt or not. `True` by default. | No |
| first_reported_at | Filter Incidents that were first reported after this time. | No | 
| last_reported_at | Filter Incidents that were first reported after this time. | No |

You can use timeago-style timestamps for parameters, for example: `2 weeks`, `1 month`.

#### Context Output

| **Path** | **Type** | **Description** |
| --- | --- | --- |
| Hoxhunt.Incident.ID | string | Machine-generated ID of the Incident. |
| Hoxhunt.Incident.HumanReadableId | string | Human-readable ID of the Incident. |
| Hoxhunt.Incident.CreatedAt | date | ISO 8601 timestamp string of when the Incident was created. | 
| Hoxhunt.Incident.UpdatedAt | date | ISO 8601 timestamp string of when the Incident was last updated. | 
| Hoxhunt.Incident.FirstReportedAt | date | ISO 8601 timestamp string of when the Incident was first reported by a user. | 
| Hoxhunt.Incident.LastUpdatedAt | date | ISO 8601 timestamp string of when the Incident was last reported by a user. | 
| Hoxhunt.Incident.Type | string | Incident type. | 
| Hoxhunt.Incident.Severity | string | Incident severity. | 
| Hoxhunt.Incident.State | string | Incident state (always `OPEN`). | 
| Hoxhunt.Incident.ThreatCount | number | The amount of Threats associated with this Incident. | 
| Hoxhunt.Incident.EscalatedAt | date | ISO 8601 timestamp string of when the Incident was escalated by Hoxhunt. If the Incident is not escalated, this field is `null`. | 
| Hoxhunt.Incident.EscalationThreshold | number | The amount of Threats that caused the Incident to be escalated. If the Incident is not escalated, this field is `null`.| 

#### Command Example

```!hoxhunt-get-incidents is_escalated="true" first_reported_at="2 months" last_reported_at="2 months"```

#### Context Example

```json
{
    "Hoxhunt": {
        "Incident": [
            {
                "ID": "zxc12rregsdf",
                "HumanReadableID": "hox-hungry-mongoose-12",
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
>|ID|Human Readable Id|Created At|Updated At|First Reported At|Last Reported At|Type|Severity|State|Threat Count|Escalated At|Escalation Threshold|
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
| human_readable_id | The human-readable ID of the Incident you wish to query Threats for. | Yes |

#### Context Output

| **Path** | **Type** | **Description** |
| --- | --- | --- |
| Hoxhunt.Threat.ID | string | Machine-generated ID of the Threat. | 
| Hoxhunt.Threat.CreatedAt | date | ISO 8601 timestamp string of when the Threat was created. | 
| Hoxhunt.Threat.UpdatedAt | date | ISO 8601 timestamp string of when the Threat was last updated. |
| Hoxhunt.Threat.EmailFrom.Name | string | An email sender name field value. |
| Hoxhunt.Threat.EmailFrom.Address | string | An email sender address field value. |
| Hoxhunt.Threat.EmailAttachments.Name | string | An attachment file name value. |
| Hoxhunt.Threat.EmailAttachments.Type | string | An attachment content type value. |
| Hoxhunt.Threat.EmailAttachments.Hash | string | An attachment content hash value. |
| Hoxhunt.Threat.EmailAttachments.Size | number | An attachment content size in bytes. |
| Hoxhunt.Threat.EnrichmentHops.From | string | The address the hop originated from. |
| Hoxhunt.Threat.EnrichmentHops.By | string | The address the hop was directed to. |
| Hoxhunt.Threat.EnrichmentLinks.Href | string | A possibly malicious link value. |
| Hoxhunt.Threat.EhrichmentLinks.Label | string | A possibly malicious link label value. |
| Hoxhunt.Threat.UserModifiers.UserActedOnThreat | boolean | Whether the user acted on the threat. |
| Hoxhunt.Threat.UserModifiers.UserRepliedToEmail | boolean | Whether the user replied to the email message. |
| Hoxhunt.Threat.UserModifiers.UserDownloadedFile | boolean | Whether the user downloaded an attachment. |
| Hoxhunt.Threat.UserModifiers.UserOpenedAttachment | boolean | Whether the user opened a downloaded attachment. |
| Hoxhunt.Threat.UserModifiers.UserVisitedLink | boolean | Whether the user visited a link in the email message. |
| Hoxhunt.Threat.UserModifiers.UserEnteredCredentials | boolean | Whether the user entered their credentials to a page they opened from a link in the email message. |
| Hoxhunt.Threat.UserModifiers.UserMarkedAsSpam | boolean | Whether the user marked the email message as spam. |

#### Context Example

```json
{
    "Hoxhunt": {
        "Threat": [
            {
                "ID": "rth675iofjy",
                "CreatedAt": "2020-06-04T13:42:26.173Z",
                "UpdatedAt": "2020-06-04T13:42:26.173Z",
                "EmailFrom": [
                  {
                    "Name": "Bad Guy",
                    "Address": "suspicious.email@example.com"
                  }
                ],
                "EmailAttachments": [
                  {
                    "Name": "this-is-definitely-not-a-virus.zip",
                    "Type": "application/zip",
                    "Hash": "f87c4bd3b606b34fdcef2b3f01bc0e9f",
                    "Size": 32
                  }
                ],
                "EnrichmentHops": [
                  {
                    "From": "malware-server.com:1234",
                    "By": "other-malware-server.com:4321"
                  }
                ],
                "EnrichmentLinks": [
                  {
                    "Href": "https://free-cat-pictures.xyz/register",
                    "Label": "CLICK HERE FOR FREE HD CAT PICS!!"
                  }
                ],
                "UserModifiers": {
                  "UserActedOnThreat": true,
                  "UserRepliedToEmail": true,
                  "UserDownloadedFile": true,
                  "UserOpenedAttachment": true,
                  "UserVisitedLink": true,
                  "UserEnteredCredentials": true,
                  "UserMarkedAsSpam": false
                }
            }
        ]
    }
}
```

#### Human Readable Output

>### Incidents:
>|ID|Created At|Updated At|Email From|Email Attachments|Enrichment Hops|Enrichment Links|User Modifiers|
>|---|---|---|---|---|---|---|---|
>| zxc12rregsdf | 2020-06-04T13:42:26.173Z | 2020-06-04T13:42:26.173Z | [{"Name": "Bad Guy", "Address": "suspicious.email@example.com"}] | [{"Name": "this-is-definitely-not-a-virus.zip", "Type": "application/zip", "Hash": "f87c4bd3b606b34fdcef2b3f01bc0e9f", "Size": 32}] | [{"From": "malware-server.com:1234", "By": "other-malware-server.com:4321"}] | [{"Href": "https://free-cat-pictures.xyz/register", "Label": "CLICK HERE FOR FREE HD CAT PICS!!"}] | {"UserActedOnThreat": true, "UserRepliedToEmail": true, "UserDownloadedFile": true, "UserOpenedAttachment": true, "UserVisitedLink": true, "UserEnteredCredentials": true, "UserMarkedAsSpam": false} |
