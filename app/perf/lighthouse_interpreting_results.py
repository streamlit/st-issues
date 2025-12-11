import streamlit as st

TITLE = "Streamlit Performance - Interpreting Lighthouse Results"

st.set_page_config(page_title=TITLE)

st.header(TITLE)

DOCS_1 = """
## What is Lighthouse?

[Lighthouse](https://developer.chrome.com/docs/lighthouse/overview) is an open-source, automated tool for improving the quality of web pages. It has audits for performance, accessibility, best practices, and SEO.
"""

DOCS_2 = """
Lighthouse scores are a set of metrics that provide insights into various aspects of a web page's performance. Each category is scored out of 100, with higher scores indicating better performance. The categories include:

### Performance
This score evaluates how quickly your page loads and becomes interactive. Key metrics include:
- **First Contentful Paint (FCP):** Time taken for the first piece of content to be rendered.
- **Speed Index:** How quickly the contents of a page are visibly populated.
- **Largest Contentful Paint (LCP):** Time taken for the largest content element to be rendered.
- **Total Blocking Time (TBT):** Sum of all time periods between FCP and TTI where the main thread was blocked for long enough to prevent input responsiveness.
- **Cumulative Layout Shift (CLS):** Measures visual stability by quantifying how much the page layout shifts during loading.

### Accessibility
This score assesses how accessible your web page is to users with disabilities. It checks for issues such as:
- **Contrast ratios:** Ensuring text is readable against background colors.
- **Alt text:** Providing alternative text for images.
- **ARIA roles:** Using Accessible Rich Internet Applications (ARIA) roles to enhance accessibility.

### Best Practices
This score evaluates whether your page follows best practices for web development, including:
- **HTTPS usage:** Ensuring secure connections.
- **No vulnerable libraries:** Checking for outdated or insecure libraries.
- **Browser errors:** Avoiding browser errors and warnings.

### SEO
This score measures how well your page is optimized for search engines. It includes checks for:
- **Meta tags:** Proper use of meta tags for titles and descriptions.
- **Content:** Ensuring content is indexable and relevant.
- **Mobile-friendliness:** Ensuring the page is optimized for mobile devices.
"""

DOCS_3 = """
## How to Interpret Lighthouse Scores in the Context of Streamlit

Lighthouse checks for a lot of different aspects, but not all of them are
necessarily pressing issues for Streamlit. For example, some of the checks are
more relevant for static websites or e-commerce sites, rather than for an
interactive data app like Streamlit.

Broadly speaking, we utilize Lighthouse as a tool in the toolbox for
understanding performance. It has the helpful side-effect that it also will keep
us honest on a number of other dimensions like accessibility, best practices,
and SEO.

### Q: Should we strive for a 100 on Lighthouse?

**No.** This would be a waste of time and does not directly impact our most
important customers. Instead, we should utilize this metric as a way of
understanding how the initial experience of Streamlit apps is performing over
time. If we see meaningful shifts in our Lighthouse number over time, that will
be a signal to dig in and understand what is going on.
"""


st.markdown(DOCS_1)

with st.expander("What do the Lighthouse Scores Mean?"):
    st.markdown(DOCS_2)

st.markdown(DOCS_3)
