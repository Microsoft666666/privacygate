"""Static human explanations; never interpolate sensitive values into labels."""
LABELS = {
    "EMAIL": "Email address", "US_PHONE": "US phone number", "SSN": "SSN-like identifier",
    "PAYMENT_CARD": "Payment-card candidate", "IPV4": "IPv4 address",
    "USER_PHRASE": "Your confidential phrase", "MANUAL_IDENTIFIER": "Personal identifier · marked by you",
    "MANUAL_ADDRESS": "Address · marked by you", "MANUAL_CONFIDENTIAL": "Confidential detail · marked by you",
    "PARTIAL_DETAIL": "Partially masked detail",
}
WHY = {
    "EMAIL": "Can identify a contact address and link this message to other activity.",
    "US_PHONE": "Can disclose a contact number; the same digits may instead be an unrelated ID.",
    "SSN": "Resembles a sensitive government identifier, even though the format is not identity verification.",
    "PAYMENT_CARD": "Passes a payment-card checksum; a valid checksum does not verify an account.",
    "IPV4": "May reveal network information. An identical shape can also be a software version.",
    "PARTIAL_DETAIL": "Masking keeps some original characters, which can still disclose information.",
}


def explanation(category: str, destination: str) -> str:
    audience = "A public post can be read and copied by others." if destination == "Public Forum" else (
        "Sharing with an AI service would disclose this detail to that service." if destination == "AI Chatbot"
        else "This is a local-notes simulation; sensitivity still deserves review.")
    return WHY.get(category, "You marked this exact phrase as sensitive, so it is protected even when automatic patterns miss it.") + " " + audience
