import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
import re

# Define file paths
input_csv_path = r"C:\Users\z003yh0e\OneDrive - Siemens Energy\Desktop\Reliability Data Engineer\Training\ETL to Power BI End-to-End Training\NBA MVP Data\datasets\mvp_data.csv"
output_csv_path = r"C:\Users\z003yh0e\OneDrive - Siemens Energy\Desktop\Reliability Data Engineer\Training\ETL to Power BI End-to-End Training\NBA MVP Data\datasets\mvp.csv"

# Load the existing MVP dataset
df = pd.read_csv(input_csv_path)

# Function to retrieve and clean player description from Wikipedia
def get_wikipedia_description(player_name):
    try:
        # Construct Wikipedia search URL
        search_url = f"https://en.wikipedia.org/wiki/{player_name.replace(' ', '_')}"
        response = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract first paragraph of the player's Wikipedia article
        paragraphs = soup.find_all("p")
        if not paragraphs:
            return f"No Wikipedia data found for {player_name}"

        for para in paragraphs:
            text = para.get_text().strip()
            if len(text) > 100:  # Ensure it's a meaningful paragraph
                # Remove citations (e.g., [1], [citation needed], etc.)
                text_cleaned = re.sub(r"\[\d+\]", " ", text)  # Remove numeric citations
                text_cleaned = re.sub(r"\[.*?\]", " ", text_cleaned)  # Remove any other brackets

                # Normalize spacing issues
                text_cleaned = re.sub(r"([.,!?])([A-Za-z])", r"\1 \2", text_cleaned)  # Ensure space after punctuation
                text_cleaned = re.sub(r"\s+", " ", text_cleaned)  # Convert multiple spaces to single space
                text_cleaned = text_cleaned.strip()  # Final cleanup

                return text_cleaned

        return f"No valid description found for {player_name}"

    except Exception as e:
        return f"Error retrieving data for {player_name}: {e}"

# Apply Wikipedia description extraction to each player
df["PlayerInfo"] = df["Player"].apply(get_wikipedia_description)

# Save the updated dataset
df.to_csv(output_csv_path, index=False, encoding="utf-8-sig")

print(f"Updated dataset saved to {output_csv_path}")