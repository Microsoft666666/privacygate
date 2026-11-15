import pytest
from suggestions import suggest_fixes, apply_fixes, restore_reply
from submission_service import evaluate_submission
from policy import review_fingerprint

@pytest.mark.parametrize('style,expected',[('Placeholder','[EMAIL_1]'),('Plain description','my email'),('Fictional look-alike','student1@example.com')])
def test_styles_restore(style,expected):
 text='Email alex@example.org or call 949-555-0134.'
 fixes,mapping=suggest_fixes(text,style=style)
 revised=apply_fixes(text,fixes)
 assert expected in revised
 assert restore_reply(revised,mapping) == text
 assert evaluate_submission(revised,'AI Chatbot',ignore_values=set(mapping.values())).accepted


def test_generated_values_are_exact_and_fingerprinted():
 generated={'student1@example.com'}
 assert evaluate_submission('student1@example.com','Public Forum',ignore_values=generated).accepted
 assert evaluate_submission('student2@example.com','Public Forum',ignore_values=generated).action == 'BLOCK'
 assert review_fingerprint('x','AI Chatbot',ignore_values=generated) != review_fingerprint('x','AI Chatbot')

@pytest.mark.parametrize('style',['Plain description','Fictional look-alike'])
def test_secrets_never_get_realistic_replacements(style):
 fixes,_=suggest_fixes('password: '+'secretvalue',style=style)
 assert fixes[0].replacement == '[SECRET_1]'
