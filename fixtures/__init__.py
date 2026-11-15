"""Shared fictional parity fixtures; secret markers expand only at runtime."""
TOKENS = {'{{GH_TOKEN}}': 'gh'+'p_'+'x'*36}

def expand(text):
    for marker,value in TOKENS.items():
        text=text.replace(marker,value)
    return text
