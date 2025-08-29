import streamlit as st

long_1 = (
    "ACME_WIDGET_RECOMMENDATION_BANNER_ALPHA_WITH_ADDITIONAL_FEATURES_AND_CUSTOMIZATION_OPTIONS"
)

long_2 = "ACME_SEARCH_RECOMMENDATION_BANNER_BETA_WITH_ENHANCED_PERSONALIZATION_AND_TARGETING_CAPABILITIES"

cols = st.columns(3)

with cols[0].container(border=True):
    st.markdown("##### Example card")
    st.markdown("Promotions:")
    st.markdown(f"- {long_1}")
    st.markdown(f"- {long_2}")
