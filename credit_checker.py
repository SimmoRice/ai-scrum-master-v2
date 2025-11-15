"""
Credit Balance Checker for Anthropic API

Checks if there are sufficient credits before running expensive operations.
"""
import os
import logging
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class InsufficientCreditsError(Exception):
    """Raised when Anthropic API credits are too low"""
    pass


class CreditChecker:
    """Check Anthropic API credit balance before operations"""

    def __init__(self):
        """Initialize credit checker with Anthropic client"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.client = Anthropic(api_key=api_key)
        self._last_balance = None

    def check_credits(self, min_balance: float = 1.0) -> bool:
        """
        Check if credit balance is sufficient

        Args:
            min_balance: Minimum required balance in USD (default: $1.00)

        Returns:
            True if balance is sufficient, False otherwise

        Raises:
            InsufficientCreditsError: If credits are below minimum threshold
        """
        try:
            # Note: Anthropic API doesn't provide a direct balance check endpoint
            # We'll catch the error during actual API calls instead
            # This is a placeholder for future API support

            # For now, we return True and rely on error handling during execution
            return True

        except Exception as e:
            logger.warning(f"Could not check credit balance: {e}")
            # If we can't check, allow the operation to proceed
            # The actual API call will fail with a clear error if credits are low
            return True

    @staticmethod
    def is_low_credit_error(error_message: str) -> bool:
        """
        Check if an error message indicates low credits

        Args:
            error_message: Error message from API or Claude Code

        Returns:
            True if error is due to low credits
        """
        low_credit_indicators = [
            "credit balance is too low",
            "insufficient credits",
            "credit limit exceeded",
            "balance too low",
        ]

        error_lower = error_message.lower()
        return any(indicator in error_lower for indicator in low_credit_indicators)

    @staticmethod
    def handle_low_credit_error(error_message: str) -> None:
        """
        Handle low credit errors with appropriate logging and exception

        Args:
            error_message: Error message from API or Claude Code

        Raises:
            InsufficientCreditsError: Always raises this exception
        """
        logger.error("=" * 60)
        logger.error("💳 ANTHROPIC API CREDITS TOO LOW")
        logger.error("=" * 60)
        logger.error("The system cannot proceed because your Anthropic account")
        logger.error("has insufficient credits to make API calls.")
        logger.error("")
        logger.error("To fix this:")
        logger.error("1. Go to https://console.anthropic.com/settings/billing")
        logger.error("2. Add credits to your account")
        logger.error("3. Workers will automatically resume once credits are added")
        logger.error("=" * 60)

        raise InsufficientCreditsError(
            "Anthropic API credit balance is too low. "
            "Please add credits at https://console.anthropic.com/settings/billing"
        )


# Global instance for easy access
credit_checker = CreditChecker()
