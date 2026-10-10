"""Reusable UI components."""
import streamlit as st


def page_header(kicker, title, copy):
    st.markdown(
        f'''<div class="ari-page-head">
        <div class="ari-label">{kicker}</div>
        <h1 class="ari-page-title">{title}</h1>
        <p class="ari-page-copy">{copy}</p>
        </div>''',
        unsafe_allow_html=True,
    )


def section_head(title, copy):
    st.markdown(
        f'''<div class="ari-section-head">
        <div class="ari-section-title">{title}</div>
        <div class="ari-section-copy">{copy}</div>
        </div>''',
        unsafe_allow_html=True,
    )


def footer():
    st.markdown(
        '''<div class="ari-footer">
        <strong>PaperPulse</strong><br>
        A structured workspace for evidence extraction, comparative analysis and literature synthesis.<br>
        Powered by BioCode Innovators · Developed by Abeera Iftikhar<br>
        Bridging Biology, Data Science, and Computational Intelligence
        </div>''',
        unsafe_allow_html=True,
    )

