"""
Prompt templates for LLM explanations.
"""

from typing import Dict


class PromptTemplates:
    """Templates for generating LLM prompts."""
    
    SYSTEM_PROMPT = """You are a financial reconciliation expert helping to explain discrepancies between bank statements and internal ledgers.

Your task is to provide clear, professional explanations and actionable suggestions for accounting teams.

Guidelines:
- Be concise but thorough
- Use professional accounting terminology
- Provide specific, actionable recommendations
- Focus on common causes and solutions
- Maintain a helpful, professional tone"""

    @staticmethod
    def get_prompt_for_missing(request: Dict) -> str:
        """Generate prompt for missing transaction."""
        source = "ledger" if "missing_in_bank" in request.get("discrepancy_type", "") else "bank statement"
        other_source = "bank statement" if source == "ledger" else "ledger"
        
        prompt = f"""A transaction appears in the {source} but not in the {other_source}.

Transaction Details:
- Description: {request.get('transaction_description', 'N/A')}
- Amount: ${request.get('amount', 'N/A')}
- Date: {request.get('date', 'N/A')}
- Severity: {request.get('severity', 'N/A')}

Machine-detected reason: {request.get('machine_reason', 'N/A')}

Please provide:
1. A clear explanation of why this discrepancy might have occurred
2. Specific steps to investigate and resolve this issue

Format your response as JSON:
{{
  "explanation": "Your explanation here",
  "suggested_action": "Your suggested action here"
}}"""
        return prompt
    
    @staticmethod
    def get_prompt_for_amount_mismatch(request: Dict) -> str:
        """Generate prompt for amount mismatch."""
        prompt = f"""A transaction was matched between bank statement and ledger, but the amounts differ.

Transaction Details:
- Description: {request.get('transaction_description', 'N/A')}
- Bank Amount: ${request.get('amount', 'N/A')}
- Ledger Amount: ${request.get('expected_amount', 'N/A')}
- Difference: ${request.get('amount_difference', 'N/A')}
- Date: {request.get('date', 'N/A')}
- Severity: {request.get('severity', 'N/A')}

Machine-detected reason: {request.get('machine_reason', 'N/A')}

Please provide:
1. An explanation of common causes for amount mismatches
2. Specific steps to investigate and resolve this discrepancy

Format your response as JSON:
{{
  "explanation": "Your explanation here",
  "suggested_action": "Your suggested action here"
}}"""
        return prompt
    
    @staticmethod
    def get_prompt_for_date_mismatch(request: Dict) -> str:
        """Generate prompt for date mismatch."""
        prompt = f"""A transaction was matched between bank statement and ledger, but the dates differ significantly.

Transaction Details:
- Description: {request.get('transaction_description', 'N/A')}
- Amount: ${request.get('amount', 'N/A')}
- Bank Date: {request.get('date', 'N/A')}
- Ledger Date: {request.get('expected_date', 'N/A')}
- Date Difference: {request.get('date_difference_days', 'N/A')} days
- Severity: {request.get('severity', 'N/A')}

Machine-detected reason: {request.get('machine_reason', 'N/A')}

Please provide:
1. An explanation of why date differences occur
2. Steps to verify and correct the posting dates

Format your response as JSON:
{{
  "explanation": "Your explanation here",
  "suggested_action": "Your suggested action here"
}}"""
        return prompt
    
    @staticmethod
    def get_prompt_for_duplicate(request: Dict) -> str:
        """Generate prompt for duplicate transaction."""
        prompt = f"""A duplicate transaction has been detected.

Transaction Details:
- Description: {request.get('transaction_description', 'N/A')}
- Amount: ${request.get('amount', 'N/A')}
- Date: {request.get('date', 'N/A')}
- Severity: {request.get('severity', 'N/A')}

Machine-detected reason: {request.get('machine_reason', 'N/A')}

Please provide:
1. An explanation of why duplicates occur
2. Steps to identify and remove the duplicate entry

Format your response as JSON:
{{
  "explanation": "Your explanation here",
  "suggested_action": "Your suggested action here"
}}"""
        return prompt
    
    @staticmethod
    def get_prompt_for_suspicious(request: Dict) -> str:
        """Generate prompt for suspicious/fraud pattern."""
        prompt = f"""A suspicious transaction pattern has been detected that may require investigation.

Transaction Details:
- Description: {request.get('transaction_description', 'N/A')}
- Amount: ${request.get('amount', 'N/A')}
- Date: {request.get('date', 'N/A')}
- Severity: {request.get('severity', 'N/A')}

Machine-detected reason: {request.get('machine_reason', 'N/A')}

Please provide:
1. An explanation of why this pattern is suspicious
2. Recommended investigation steps and actions

Format your response as JSON:
{{
  "explanation": "Your explanation here",
  "suggested_action": "Your suggested action here"
}}"""
        return prompt
    
    @staticmethod
    def get_prompt(request: Dict) -> str:
        """Get appropriate prompt based on discrepancy type."""
        disc_type = request.get("discrepancy_type", "").lower()
        
        if "missing" in disc_type:
            return PromptTemplates.get_prompt_for_missing(request)
        elif "amount" in disc_type:
            return PromptTemplates.get_prompt_for_amount_mismatch(request)
        elif "date" in disc_type:
            return PromptTemplates.get_prompt_for_date_mismatch(request)
        elif "duplicate" in disc_type:
            return PromptTemplates.get_prompt_for_duplicate(request)
        elif "fraud" in disc_type or "suspicious" in disc_type:
            return PromptTemplates.get_prompt_for_suspicious(request)
        else:
            # Generic prompt
            return f"""A discrepancy has been detected in the financial reconciliation.

Transaction Details:
- Description: {request.get('transaction_description', 'N/A')}
- Amount: ${request.get('amount', 'N/A')}
- Date: {request.get('date', 'N/A')}
- Type: {disc_type}
- Severity: {request.get('severity', 'N/A')}

Machine-detected reason: {request.get('machine_reason', 'N/A')}

Please provide:
1. An explanation of this discrepancy
2. Recommended actions to resolve it

Format your response as JSON:
{{
  "explanation": "Your explanation here",
  "suggested_action": "Your suggested action here"
}}"""

