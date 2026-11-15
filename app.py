"""PrivacyGate: compose, review, fix and copy."""
from pathlib import Path
import streamlit as st
from components.simple import render

st.set_page_config(page_title='PrivacyGate · Review before sharing', page_icon=':material/shield:', layout='wide')
st.html(Path(__file__).parent / 'styles' / 'theme.css')
render()
