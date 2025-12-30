# n8n Integration Guide

This document explains how to integrate the Financial Reconciliation Agent with n8n for automated workflows.

## Overview

The reconciliation system generates JSON payloads that can be consumed by n8n workflows. n8n can:
- Trigger reconciliation runs (scheduled or event-based)
- Process reconciliation results
- Create tickets in Jira/ServiceNow
- Send email notifications
- Store reports in cloud storage

## Integration Points

### 1. Trigger Reconciliation

**Webhook Endpoint:** `POST /reconcile`

**n8n Workflow:**
```
Schedule Trigger → HTTP Request → Reconciliation API
```

**Example n8n HTTP Request Node:**
- Method: POST
- URL: `http://your-api:8000/reconcile`
- Body (JSON):
```json
{
  "bank_file_url": "https://storage.example.com/bank_statement.csv",
  "ledger_file_url": "https://storage.example.com/ledger.csv",
  "reconciliation_config": {
    "amount_tolerance": 5.00,
    "date_window_days": 7
  }
}
```

### 2. Process Reconciliation Results

**Response Format:**
```json
{
  "reconciliation_id": "uuid",
  "status": "completed",
  "report_url": "/reports/reconciliation_report_xxx.csv",
  "tickets": [
    {
      "ticket_type": "discrepancy",
      "title": "Missing In Ledger: GAS $176.89",
      "priority": "medium",
      "severity": "medium",
      ...
    }
  ],
  "summary": {
    "matched": 18,
    "unmatched": 2,
    "discrepancies": 2
  }
}
```

**n8n Workflow:**
```
HTTP Request → Process Results → Conditional (if discrepancies) → Create Tickets
```

### 3. Create Tickets in Jira

**n8n Workflow:**
```
Process Results → Loop Over Tickets → Jira Node
```

**Jira Node Configuration:**
- Operation: Create Issue
- Project: RECON
- Issue Type: Task
- Summary: `{{ $json.title }}`
- Description: `{{ $json.description }}`
- Priority: `{{ $json.priority }}`
- Labels: `{{ $json.labels }}`

**Ticket Format (from `/tickets` endpoint):**
```json
{
  "fields": {
    "project": {"key": "RECON"},
    "summary": "Missing In Ledger: GAS $176.89",
    "description": "...",
    "priority": {"name": "Medium"},
    "labels": ["reconciliation", "missing_in_ledger"]
  }
}
```

### 4. Create Tickets in ServiceNow

**n8n Workflow:**
```
Process Results → Loop Over Tickets → ServiceNow Node
```

**ServiceNow Node Configuration:**
- Operation: Create Record
- Table: incident
- Fields:
  - `short_description`: `{{ $json.title }}`
  - `description`: `{{ $json.description }}`
  - `priority`: `{{ $json.priority }}`
  - `category`: "Financial Reconciliation"

### 5. Send Email Notifications

**n8n Workflow:**
```
Process Results → Conditional (if critical) → Email Node
```

**Email Node Configuration:**
- To: accounting-team@example.com
- Subject: `[CRITICAL] Reconciliation Discrepancies Found`
- Body: Use HTML template with discrepancy details

### 6. Store Reports in Cloud Storage

**n8n Workflow:**
```
Process Results → HTTP Request (download report) → Google Drive/S3 Node
```

**Example:**
1. Download CSV report from `report_url`
2. Upload to Google Drive folder: `/Reconciliation Reports/2024/`
3. Share with accounting team

## Complete n8n Workflow Example

```
┌─────────────────┐
│ Schedule Trigger│ (Daily at 9 AM)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ HTTP Request    │ POST /reconcile
│ (Trigger API)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ IF Node         │ Check if discrepancies > 0
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
   YES       NO
    │         │
    ▼         ▼
┌─────────┐ ┌──────────┐
│ Loop    │ │ Email    │ "Reconciliation complete - no issues"
│ Tickets │ │ (Success)│
└────┬────┘ └──────────┘
     │
     ▼
┌─────────────────┐
│ Jira Node       │ Create ticket for each discrepancy
│ (Create Issue)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Email Node      │ Send summary to accounting team
│ (Alert)         │
└─────────────────┘
```

## API Endpoints for n8n

### POST /reconcile
Trigger reconciliation run.

**Request:**
```json
{
  "bank_file_url": "string",
  "ledger_file_url": "string",
  "reconciliation_config": {}
}
```

**Response:**
```json
{
  "reconciliation_id": "uuid",
  "status": "completed",
  "report_url": "string",
  "tickets": [],
  "summary": {}
}
```

### GET /reports/{reconciliation_id}
Get reconciliation report.

**Response:** CSV file download

### GET /tickets/{reconciliation_id}?format=jira
Get tickets in specified format.

**Formats:** `jira`, `servicenow`, `n8n`, `generic`, `email`

**Response:**
```json
[
  {
    "fields": {...}  // Jira format
  }
]
```

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

## Environment Variables

Set these in n8n environment or workflow variables:

- `RECONCILIATION_API_URL`: Base URL of reconciliation API
- `JIRA_PROJECT_KEY`: Jira project key (default: RECON)
- `EMAIL_RECIPIENTS`: Comma-separated email addresses
- `SLACK_WEBHOOK_URL`: Optional Slack notifications

## Error Handling

n8n workflows should handle:
- API timeouts (set timeout to 5 minutes)
- Rate limiting (add delays between requests)
- Partial failures (continue processing other tickets)
- Retry logic for transient errors

## Monitoring

Monitor n8n workflows for:
- Reconciliation run frequency
- Ticket creation success rate
- Email delivery status
- API response times

## Best Practices

1. **Scheduled Runs**: Run reconciliation daily/weekly based on business needs
2. **Error Notifications**: Send alerts for failed reconciliations
3. **Ticket Deduplication**: Check if ticket already exists before creating
4. **Report Archival**: Store reports in cloud storage for audit trail
5. **Cost Monitoring**: Track LLM API usage and costs

