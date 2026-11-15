from detector import detect
from policy import review_fingerprint
from submission_service import evaluate_submission

def test_detector_api_and_ner_fingerprint():
    text = 'alex@example.com'
    assert detect(text, ner=False)[0].category == 'EMAIL'
    ack = review_fingerprint(text, 'AI Chatbot', ner=False)
    assert evaluate_submission(text, 'AI Chatbot', ack, ner=False).accepted
    assert not evaluate_submission(text, 'AI Chatbot', ack, ner=True).accepted
