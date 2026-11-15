"""Fictional, in-memory demonstrations. Credential shapes are assembled at runtime."""
QUICK_CONTACT = "Hi, I'm Alex. Please help improve this scholarship essay. I volunteered at our community garden and organized weekend activities. If you need to reach me, my email is alex@example.com and my phone number is 949-555-0134."
SCENARIOS = {
 'Quick contact': dict(destination='AI Chatbot', text=QUICK_CONTACT),
 'College essay': dict(destination='AI Chatbot',text="Hi, I'm Alex Chen from Northwood High School in Irvine, born 03/07/2009. Please improve my scholarship essay about organizing a community garden. My email is alex@example.com and my phone is 949-555-0134."),
 'Coding help': dict(destination='AI Chatbot',text='Why does this Python configuration fail?\napi_key = "'+'sk-'+'ab'*15+'"\ndatabase_url = "postgres://app:'+'pw'*5+'@localhost/app"'),
 'Public forum post': dict(destination='Public Forum',text='Please polish my lost-item post. Return it to 123 Main St, Irvine, CA 92618. Call 949-555-0134 or email alex@example.com.'),
 'Harmless text': dict(destination='AI Chatbot',text='Please help make this paragraph clearer: our garden club planted tomatoes and shared the harvest with neighbors.'),
}
