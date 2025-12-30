"""
Accounting ticket generation for issue tracking systems.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from enum import Enum

from discrepancy.models import Discrepancy, DiscrepancySeverity
from reporting.models import Ticket

logger = logging.getLogger(__name__)


class TicketFormat(str, Enum):
    """Supported ticket formats."""
    JIRA = "jira"
    SERVICENOW = "servicenow"
    GENERIC = "generic"
    EMAIL = "email"
    N8N = "n8n"  # JSON format for n8n webhooks


class TicketGenerator:
    """Generates tickets for various issue tracking systems."""
    
    def __init__(self, default_assignee: Optional[str] = None):
        """
        Initialize ticket generator.
        
        Args:
            default_assignee: Default assignee for tickets
        """
        self.default_assignee = default_assignee
    
    def generate_tickets_from_discrepancies(
        self,
        discrepancies: List[Discrepancy],
        reconciliation_id: str,
        min_severity: DiscrepancySeverity = DiscrepancySeverity.LOW
    ) -> List[Ticket]:
        """
        Generate tickets from discrepancies.
        
        Args:
            discrepancies: List of discrepancies
            reconciliation_id: Reconciliation run ID
            min_severity: Minimum severity to create tickets for
        
        Returns:
            List of generated tickets
        """
        tickets = []
        
        severity_order = {
            DiscrepancySeverity.CRITICAL: 4,
            DiscrepancySeverity.HIGH: 3,
            DiscrepancySeverity.MEDIUM: 2,
            DiscrepancySeverity.LOW: 1
        }
        
        min_severity_level = severity_order.get(min_severity, 1)
        
        for disc in discrepancies:
            disc_severity_level = severity_order.get(disc.severity, 1)
            
            # Skip if below minimum severity
            if disc_severity_level < min_severity_level:
                continue
            
            ticket = self._create_ticket_from_discrepancy(disc, reconciliation_id)
            tickets.append(ticket)
        
        logger.info(f"Generated {len(tickets)} tickets from {len(discrepancies)} discrepancies")
        return tickets
    
    def _create_ticket_from_discrepancy(
        self,
        disc: Discrepancy,
        reconciliation_id: str
    ) -> Ticket:
        """Create a ticket from a discrepancy."""
        # Determine ticket type
        if disc.discrepancy_type.value in ["possible_fraud", "amount_mismatch"]:
            ticket_type = "discrepancy"
        elif disc.discrepancy_type.value in ["missing_in_bank", "missing_in_ledger"]:
            ticket_type = "review_required"
        else:
            ticket_type = "action_item"
        
        # Generate title
        title = self._generate_title(disc)
        
        # Generate description
        description = self._generate_description(disc, reconciliation_id)
        
        # Map severity to priority
        priority_map = {
            DiscrepancySeverity.CRITICAL: "critical",
            DiscrepancySeverity.HIGH: "high",
            DiscrepancySeverity.MEDIUM: "medium",
            DiscrepancySeverity.LOW: "low"
        }
        priority = priority_map.get(disc.severity, "medium")
        
        # Calculate due date (critical = 1 day, high = 3 days, medium = 7 days, low = 14 days)
        due_date_days = {
            DiscrepancySeverity.CRITICAL: 1,
            DiscrepancySeverity.HIGH: 3,
            DiscrepancySeverity.MEDIUM: 7,
            DiscrepancySeverity.LOW: 14
        }
        due_date = datetime.now() + timedelta(days=due_date_days.get(disc.severity, 7))
        
        # Generate labels
        labels = [
            "reconciliation",
            disc.discrepancy_type.value,
            disc.severity.value,
            f"recon-{reconciliation_id[:8]}"
        ]
        
        ticket = Ticket(
            ticket_type=ticket_type,
            title=title,
            description=description,
            priority=priority,
            severity=disc.severity.value,
            transaction_id=disc.transaction_id,
            amount=disc.amount,
            date=disc.date,
            transaction_description=disc.description,
            discrepancy_type=disc.discrepancy_type.value,
            machine_reason=disc.machine_reason,
            llm_explanation=disc.llm_explanation,
            suggested_action=disc.suggested_action,
            labels=labels,
            assignee=self.default_assignee,
            due_date=due_date,
            custom_fields={}
        )
        
        return ticket
    
    def _generate_title(self, disc: Discrepancy) -> str:
        """Generate ticket title."""
        disc_type = disc.discrepancy_type.value.replace("_", " ").title()
        amount_str = f" ${disc.amount:.2f}" if disc.amount else ""
        desc_short = (disc.description or "Transaction")[:30]
        
        return f"{disc_type}: {desc_short}{amount_str}"
    
    def _generate_description(self, disc: Discrepancy, reconciliation_id: str) -> str:
        """Generate ticket description."""
        lines = [
            f"**Discrepancy Type:** {disc.discrepancy_type.value.replace('_', ' ').title()}",
            f"**Severity:** {disc.severity.value.upper()}",
            f"**Reconciliation ID:** {reconciliation_id}",
            "",
            "**Transaction Details:**",
            f"- Description: {disc.description or 'N/A'}" if disc.description else "- Description: N/A",
            f"- Amount: ${disc.amount:.2f}" if disc.amount else "- Amount: N/A",
            f"- Date: {disc.date.isoformat()}" if disc.date else "- Date: N/A",
            "",
            "**Issue:**",
            disc.machine_reason or "No machine reason provided",
        ]
        
        if disc.amount_difference:
            lines.append(f"- Amount Difference: ${disc.amount_difference:.2f}")
        
        if disc.date_difference_days is not None:
            lines.append(f"- Date Difference: {disc.date_difference_days} days")
        
        if disc.llm_explanation:
            lines.extend([
                "",
                "**Explanation:**",
                disc.llm_explanation
            ])
        
        if disc.suggested_action:
            lines.extend([
                "",
                "**Suggested Action:**",
                disc.suggested_action
            ])
        
        return "\n".join(lines)
    
    def format_for_jira(self, ticket: Ticket) -> Dict:
        """Format ticket for Jira API."""
        return {
            "fields": {
                "project": {"key": "RECON"},  # Should be configured
                "summary": ticket.title,
                "description": ticket.description,
                "issuetype": {"name": "Task"},
                "priority": {"name": ticket.priority.title()},
                "labels": ticket.labels,
                "assignee": {"name": ticket.assignee} if ticket.assignee else None,
                "duedate": ticket.due_date.strftime("%Y-%m-%d") if ticket.due_date else None,
                "customfield_10000": ticket.discrepancy_type,  # Example custom field
            }
        }
    
    def format_for_servicenow(self, ticket: Ticket) -> Dict:
        """Format ticket for ServiceNow API."""
        return {
            "short_description": ticket.title,
            "description": ticket.description,
            "priority": self._map_priority_to_servicenow(ticket.priority),
            "severity": ticket.severity,
            "category": "Financial Reconciliation",
            "subcategory": ticket.discrepancy_type,
            "assignment_group": "Accounting",  # Should be configured
            "assigned_to": ticket.assignee,
            "due_date": ticket.due_date.isoformat() if ticket.due_date else None,
            "work_notes": ticket.suggested_action or "",
        }
    
    def format_for_n8n(self, ticket: Ticket) -> Dict:
        """Format ticket for n8n webhook (generic JSON)."""
        return {
            "ticket": ticket.to_dict(),
            "webhook_type": "accounting_ticket",
            "timestamp": datetime.now().isoformat(),
        }
    
    def format_for_email(self, ticket: Ticket) -> Dict:
        """Format ticket for email notification."""
        return {
            "subject": f"[{ticket.severity.upper()}] {ticket.title}",
            "body": f"""
{ticket.description}

---
Priority: {ticket.priority}
Due Date: {ticket.due_date.strftime('%Y-%m-%d') if ticket.due_date else 'Not set'}
Labels: {', '.join(ticket.labels)}
            """.strip(),
            "to": ticket.assignee or "accounting-team@example.com",  # Should be configured
            "cc": [],
        }
    
    def format_for_generic(self, ticket: Ticket) -> Dict:
        """Format ticket as generic JSON."""
        return ticket.to_dict()
    
    def format_ticket(
        self,
        ticket: Ticket,
        format_type: TicketFormat
    ) -> Dict:
        """
        Format ticket for specific system.
        
        Args:
            ticket: Ticket to format
            format_type: Target format
        
        Returns:
            Formatted ticket dictionary
        """
        formatters = {
            TicketFormat.JIRA: self.format_for_jira,
            TicketFormat.SERVICENOW: self.format_for_servicenow,
            TicketFormat.N8N: self.format_for_n8n,
            TicketFormat.EMAIL: self.format_for_email,
            TicketFormat.GENERIC: self.format_for_generic,
        }
        
        formatter = formatters.get(format_type, self.format_for_generic)
        return formatter(ticket)
    
    def _map_priority_to_servicenow(self, priority: str) -> str:
        """Map priority to ServiceNow format."""
        mapping = {
            "critical": "1",
            "high": "2",
            "medium": "3",
            "low": "4"
        }
        return mapping.get(priority.lower(), "3")
    
    def save_tickets_json(
        self,
        tickets: List[Ticket],
        format_type: TicketFormat,
        filepath: str
    ):
        """Save tickets to JSON file."""
        formatted_tickets = [
            self.format_ticket(ticket, format_type)
            for ticket in tickets
        ]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(formatted_tickets, f, indent=2, default=str)
        
        logger.info(f"Saved {len(tickets)} tickets to {filepath}")

