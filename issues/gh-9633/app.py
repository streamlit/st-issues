import streamlit as st
import time

class DataFetcher:
    def __init__(self):
        self.counter = 0

    @st.cache_data(show_spinner="Fetching data...", ttl=None)
    def _get_data(_self, param):
        _self.counter += 1
        # Simulate a time-consuming operation
        time.sleep(2)
        # Use the param in the returned data
        return f"Data for '{param}'. Fetch count: {_self.counter}"

    def fetch_and_display(self, param):
        start_time = time.time()
        data = self._get_data(param)
        end_time = time.time()
        
        st.write(data)
        st.write(f"Fetch time: {end_time - start_time:.2f} seconds")

    def clear_cache(self):
        self._get_data.clear()

def main():
    st.title("Streamlit Cache Clear Bug Demo")

    data_fetcher = DataFetcher()

    param = st.text_input("Enter a data category", value="users")

    if st.button("Fetch Data"):
        data_fetcher.fetch_and_display(param)

    if st.button("Clear Cache"):
        data_fetcher.clear_cache()
        st.success("Cache cleared (or not?)")

    st.write("Note: If cache is working, only the first fetch for each unique category should take ~2 seconds.")
    st.write("If cache is cleared successfully, the next fetch after clearing should take ~2 seconds for all categories.")

if __name__ == "__main__":
    main()
