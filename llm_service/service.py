"""
LLM explanation service using OpenAI GPT-4o-mini.
"""

import os
import json
import logging
from typing import Optional, Dict, List
from decimal import Decimal
from datetime import date

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI package not available. LLM explanations will be disabled.")

from .models import ExplanationRequest, ExplanationResponse
from .prompts import PromptTemplates

logger = logging.getLogger(__name__)


class LLMExplanationService:
    """Service for generating LLM-based explanations."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.0,
        max_tokens: int = 500,
        enable_cache: bool = True
    ):
        """
        Initialize LLM explanation service.
        
        Args:
            api_key: OpenAI API key (default: from OPENAI_API_KEY env var)
            model: Model to use (default: gpt-4o-mini)
            temperature: Temperature for generation (0.0 for deterministic)
            max_tokens: Maximum tokens per request
            enable_cache: Whether to cache explanations
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package is required. Install with: pip install openai")
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.enable_cache = enable_cache
        
        self.client = None
        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
        
        # Cost tracking
        self.total_tokens_used = 0
        self.total_requests = 0
        self.cache: Dict[str, ExplanationResponse] = {}
    
    def explain_discrepancy(
        self,
        request: ExplanationRequest
    ) -> ExplanationResponse:
        """
        Generate explanation for a discrepancy.
        
        Args:
            request: Explanation request with discrepancy details
        
        Returns:
            ExplanationResponse with explanation and suggested action
        """
        if not self.client:
            return ExplanationResponse(
                explanation="LLM service not available. Please configure OpenAI API key.",
                suggested_action=request.machine_reason or "Review transaction manually.",
                error="API key not configured"
            )
        
        # Check cache
        cache_key = self._get_cache_key(request)
        if self.enable_cache and cache_key in self.cache:
            logger.debug(f"Using cached explanation for {cache_key}")
            return self.cache[cache_key]
        
        try:
            # Prepare request data
            request_data = {
                "discrepancy_type": request.discrepancy_type,
                "transaction_description": request.transaction_description,
                "amount": str(request.amount) if request.amount else None,
                "date": request.date.isoformat() if request.date else None,
                "machine_reason": request.machine_reason,
                "severity": request.severity,
                "amount_difference": str(request.amount_difference) if request.amount_difference else None,
                "date_difference_days": request.date_difference_days,
                "related_transaction_info": request.related_transaction_info,
            }
            
            # Get prompt
            user_prompt = PromptTemplates.get_prompt(request_data)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": PromptTemplates.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}  # Force JSON response
            )
            
            # Parse response
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            # Track usage
            self.total_tokens_used += tokens_used
            self.total_requests += 1
            
            # Parse JSON response
            try:
                parsed = json.loads(content)
                explanation = parsed.get("explanation", "No explanation provided.")
                suggested_action = parsed.get("suggested_action", "Review transaction manually.")
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                logger.warning("Failed to parse JSON response, using raw content")
                explanation = content
                suggested_action = request.machine_reason or "Review transaction manually."
            
            result = ExplanationResponse(
                explanation=explanation,
                suggested_action=suggested_action,
                tokens_used=tokens_used,
                model_used=self.model
            )
            
            # Cache result
            if self.enable_cache:
                self.cache[cache_key] = result
            
            return result
        
        except Exception as e:
            logger.error(f"Error generating LLM explanation: {e}", exc_info=True)
            return ExplanationResponse(
                explanation=f"Error generating explanation: {str(e)}",
                suggested_action=request.machine_reason or "Review transaction manually.",
                error=str(e)
            )
    
    def explain_batch(
        self,
        requests: List[ExplanationRequest],
        max_concurrent: int = 5
    ) -> List[ExplanationResponse]:
        """
        Generate explanations for multiple discrepancies.
        
        Args:
            requests: List of explanation requests
            max_concurrent: Maximum concurrent requests (for rate limiting)
        
        Returns:
            List of explanation responses
        """
        results = []
        
        # Process in batches to respect rate limits
        for i in range(0, len(requests), max_concurrent):
            batch = requests[i:i + max_concurrent]
            batch_results = []
            
            for request in batch:
                result = self.explain_discrepancy(request)
                batch_results.append(result)
            
            results.extend(batch_results)
        
        return results
    
    def _get_cache_key(self, request: ExplanationRequest) -> str:
        """Generate cache key for request."""
        return f"{request.discrepancy_type}:{request.transaction_description}:{request.amount}:{request.date}"
    
    def get_usage_stats(self) -> Dict:
        """Get usage statistics."""
        return {
            "total_requests": self.total_requests,
            "total_tokens_used": self.total_tokens_used,
            "cached_responses": len(self.cache),
            "estimated_cost_usd": self._estimate_cost()
        }
    
    def _estimate_cost(self) -> float:
        """Estimate cost based on tokens used."""
        # GPT-4o-mini pricing (as of 2024): $0.15 per 1M input tokens, $0.60 per 1M output tokens
        # Rough estimate: assume 50/50 input/output split
        input_cost_per_1k = 0.00015
        output_cost_per_1k = 0.0006
        
        # Rough estimate: assume average 200 input + 300 output = 500 tokens per request
        if self.total_requests == 0:
            return 0.0
        
        avg_tokens = self.total_tokens_used / self.total_requests
        estimated_input = avg_tokens * 0.4
        estimated_output = avg_tokens * 0.6
        
        cost = (estimated_input * input_cost_per_1k + estimated_output * output_cost_per_1k) * self.total_requests
        return round(cost, 4)
    
    def clear_cache(self):
        """Clear explanation cache."""
        self.cache.clear()
        logger.info("Explanation cache cleared")

