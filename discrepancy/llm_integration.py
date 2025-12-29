"""
Integration between discrepancy detection and LLM explanation service.
"""

import logging
from typing import Optional, List

from discrepancy.models import Discrepancy, DiscrepancyResult
try:
    from llm_service import LLMExplanationService, ExplanationRequest
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    LLMExplanationService = None
    ExplanationRequest = None

logger = logging.getLogger(__name__)


class DiscrepancyLLMIntegrator:
    """Integrates LLM explanations with discrepancy detection."""
    
    def __init__(
        self,
        llm_service: Optional[LLMExplanationService] = None,
        enable_llm: bool = True
    ):
        """
        Initialize integrator.
        
        Args:
            llm_service: LLM service instance (creates new if None)
            enable_llm: Whether to enable LLM explanations
        """
        self.enable_llm = enable_llm
        self.llm_service = llm_service
        
        if enable_llm and not llm_service:
            try:
                self.llm_service = LLMExplanationService()
            except Exception as e:
                logger.warning(f"Failed to initialize LLM service: {e}")
                self.enable_llm = False
                self.llm_service = None
    
    def enhance_with_explanations(
        self,
        discrepancies: List[Discrepancy],
        bank_tx_dict: dict = None,
        ledger_tx_dict: dict = None
    ) -> List[Discrepancy]:
        """
        Enhance discrepancies with LLM explanations.
        
        Args:
            discrepancies: List of discrepancies to enhance
            bank_tx_dict: Dictionary of bank transactions (for context)
            ledger_tx_dict: Dictionary of ledger transactions (for context)
        
        Returns:
            List of discrepancies with LLM explanations added
        """
        if not self.enable_llm or not self.llm_service:
            logger.info("LLM explanations disabled or service unavailable")
            return discrepancies
        
        enhanced = []
        
        for disc in discrepancies:
            try:
                # Create explanation request
                request = ExplanationRequest(
                    discrepancy_type=disc.discrepancy_type.value,
                    transaction_description=disc.description or "Unknown",
                    amount=disc.amount,
                    date=disc.date,
                    machine_reason=disc.machine_reason,
                    severity=disc.severity.value,
                    amount_difference=disc.amount_difference,
                    date_difference_days=disc.date_difference_days,
                    related_transaction_info=self._get_related_info(
                        disc, bank_tx_dict, ledger_tx_dict
                    )
                )
                
                # Get LLM explanation
                response = self.llm_service.explain_discrepancy(request)
                
                # Enhance discrepancy
                disc.llm_explanation = response.explanation
                if response.suggested_action:
                    disc.suggested_action = response.suggested_action
                
                logger.debug(f"Enhanced discrepancy {disc.transaction_id[:8]} with LLM explanation")
            
            except Exception as e:
                logger.warning(f"Failed to enhance discrepancy {disc.transaction_id[:8]}: {e}")
                # Keep original discrepancy without LLM enhancement
            
            enhanced.append(disc)
        
        return enhanced
    
    def _get_related_info(
        self,
        disc: Discrepancy,
        bank_tx_dict: dict,
        ledger_tx_dict: dict
    ) -> Optional[str]:
        """Get information about related transaction."""
        if not disc.related_transaction_id:
            return None
        
        # Try to find related transaction
        if disc.source == "bank" and ledger_tx_dict:
            related = ledger_tx_dict.get(disc.related_transaction_id)
            if related:
                return f"Related ledger transaction: {related.description}, ${related.amount}, {related.date}"
        elif disc.source == "ledger" and bank_tx_dict:
            related = bank_tx_dict.get(disc.related_transaction_id)
            if related:
                return f"Related bank transaction: {related.description}, ${related.amount}, {related.date}"
        
        return None

