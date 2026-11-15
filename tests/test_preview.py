from components.preview import findings_preview
from detector import detect

def test_preview_escapes_every_segment():
 text='<script>alert(1)</script> alex@example.com'
 html=findings_preview(text,detect(text,ner=False))
 assert '&lt;script&gt;' in html and '<script>' not in html
 assert '⟦Email address⟧' in html

def test_preview_masks_secret():
 secret='sk-'+'ab'*15
 html=findings_preview(secret,detect(secret,ner=False))
 assert secret not in html and 'sk…ab' in html
