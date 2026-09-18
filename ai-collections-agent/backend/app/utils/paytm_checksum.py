"""
Paytm checksum utility.
Uses the official paytmchecksum library (pip install paytmchecksum).
Wraps generation and verification with proper error handling.
"""

import logging
from typing import Any

try:
    import PaytmChecksum
except ImportError:
    PaytmChecksum = None  # type: ignore

logger = logging.getLogger(__name__)


def generate_checksum(params: dict[str, Any], merchant_key: str) -> str:
    """
    Generate Paytm checksum hash for a parameter dict.
    
    Args:
        params: Dict of request parameters (all values must be strings)
        merchant_key: Paytm merchant key from settings
        
    Returns:
        Base64-encoded checksum string
    """
    if PaytmChecksum is None:
        raise ImportError("paytmchecksum library not installed. Run: pip install paytmchecksum")

    # Convert all values to strings (Paytm requirement)
    str_params = {k: str(v) for k, v in params.items()}
    checksum = PaytmChecksum.PaytmChecksum.generateSignature(str_params, merchant_key)
    logger.debug("Generated checksum for order: %s", params.get("ORDER_ID"))
    return checksum


def verify_checksum(params: dict[str, Any], merchant_key: str, checksum: str) -> bool:
    """
    Verify Paytm checksum from a webhook/callback response.
    
    Args:
        params: Dict of all response parameters EXCEPT the checksum itself
        merchant_key: Paytm merchant key
        checksum: The CHECKSUMHASH value from the response
        
    Returns:
        True if checksum is valid, False otherwise
    """
    if PaytmChecksum is None:
        logger.error("paytmchecksum library not installed; treating checksum as invalid.")
        return False

    try:
        str_params = {k: str(v) for k, v in params.items() if k != "CHECKSUMHASH"}
        is_valid = PaytmChecksum.PaytmChecksum.verifySignature(str_params, merchant_key, checksum)
        if not is_valid:
            logger.warning("Checksum verification FAILED for order: %s", params.get("ORDERID"))
        return is_valid
    except Exception as exc:
        logger.error("Checksum verification raised exception: %s", exc)
        return False
