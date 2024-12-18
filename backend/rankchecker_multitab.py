import webbrowser

# Base URL for Google UK
base_url = "https://www.google.co.uk/?gl=uk"

# Open the base URL in 10 new browser tabs
for _ in range(10):
    webbrowser.open_new_tab(base_url)

print("Opened 10 new browser tabs with Google UK!")
