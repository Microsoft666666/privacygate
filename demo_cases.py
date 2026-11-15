"""Deliberately fictional examples; never loaded without user action."""
DEMOS = {
    "Student essay": "I’m Alex, a fictional student writing about our community garden. Please help polish my essay. Contact me at alex@example.com or 949-555-0134.",
    "Payment info": "Fictional checkout test only: card 4111 1111 1111 1111. Receipt: alex@example.com. Do not use actual payment information in this demo.",
    "Harmless text": "Our community garden taught me to listen, collaborate, and keep trying. In 2026, we grew tomatoes and donated 25 baskets.",
}

DEMOS["Social post"] = "Fictional post: Alex Chen is organizing a garden meetup. Ask Alex Chen at alex@example.com or 949-555-0134."
DEMO_DESTINATIONS = {"Student essay": "AI Chatbot", "Payment info": "AI Chatbot",
                     "Harmless text": "AI Chatbot", "Social post": "Public Forum"}
DEMO_GUIDES = {
    "Student essay": "Expected: phone blocks; email warns. Scan → deselect email → redact phone → acknowledge email → simulate. Switch to Public Forum to see the email block.",
    "Payment info": "TEST-ONLY payment support note. Expected: Luhn-valid test card blocks. Scan → inspect checksum explanation → replace card and email → simulate.",
    "Harmless text": "Benign school/garden request. Expected: no supported patterns. Scan → review yourself → simulate. No-pattern does not guarantee privacy.",
    "Social post": "Expected: public policy blocks email and phone. Scan → enter Alex Chen with the Name label → mark phrase → redact all → simulate. Names are user-marked, never automatically inferred.",
}
