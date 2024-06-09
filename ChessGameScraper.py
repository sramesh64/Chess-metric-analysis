import os
import time
import json
import pandas as pd
from datetime import datetime, timedelta
import chess.pgn
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

#IMPORTANT: To use tool, enter your chess.com login username and password below
USERNAME = "example_username"
PASSWORD = "example_password"


def create_download_folder():
    # Get the current project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))

    # Create a new folder for downloads
    download_folder = os.path.join(project_dir, "downloads")
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
    
    return project_dir, download_folder

def configure_chrome(download_folder):
    # Configure Chrome options to set the download directory
    chrome_options = Options()
    prefs = {
        "download.default_directory": download_folder,  # Set download directory to project folder
        "download.prompt_for_download": False,          # Disable download prompt
        "directory_upgrade": True,                      # Ensure download directory is updated
    }
    chrome_options.add_experimental_option("prefs", prefs)
    return chrome_options

def login_chess_com(driver):
    driver.get("https://www.chess.com/login")
    time.sleep(1)  # Wait for page to load

    # Log in
    username = driver.find_element(By.XPATH, '//input[@aria-label="Username or Email" and @type="email"]')
    password = driver.find_element(By.XPATH, '//input[@type="password"]')
    username.send_keys(USERNAME)
    password.send_keys(PASSWORD)
    password.send_keys(Keys.RETURN)

    time.sleep(1)  # Wait for login to complete

def download_pgn_for_each_week(driver, start_date, end_date):
    start_date = datetime.strptime(start_date, '%m/%d/%Y')
    end_date = datetime.strptime(end_date, '%m/%d/%Y')

    while start_date > datetime.strptime('2024-01-01', '%Y-%m-%d'):  # Change the condition as needed
        url = f"https://www.chess.com/games/archive?gameOwner=my_game&gameType=recent&endDate%5Bdate%5D={end_date}&startDate%5Bdate%5D={start_date}&timeSort=desc"
        driver.get(url)
        time.sleep(1)  # Wait for page to load

        try:
            specific_button = WebDriverWait(driver, 1).until(EC.element_to_be_clickable((By.XPATH, '//input[@aria-label="Select All Games"]')))
            specific_button.click()
            
            download_button = WebDriverWait(driver, 1).until(
                EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Download" and not(@disabled)]'))
            )
            download_button.click()
            print(f"Successfully Downloaded games for the week of {start_date} to {end_date}!")
            time.sleep(1)  # Wait for download to complete
            start_date -= timedelta(weeks=1)
            end_date -= timedelta(weeks=1)
        except Exception:
            print(f"Chess.com bot-prevention system stopping download for the week of {start_date} to {end_date}. Trying again")

def extract_game_data(download_folder):
    games_data = []

    # Loop through all PGN files in the download folder
    for filename in os.listdir(download_folder):
        if filename.endswith(".pgn"):
            file_path = os.path.join(download_folder, filename)
            with open(file_path, 'r', encoding='utf-8') as pgn_file:
                while True:
                    game = chess.pgn.read_game(pgn_file)
                    if game is None:
                        break

                    # Extract relevant data from the game
                    game_data = {
                        "Event": game.headers.get("Event", ""),
                        "Site": game.headers.get("Site", ""),
                        "Date": game.headers.get("Date", ""),
                        "Round": game.headers.get("Round", ""),
                        "White": game.headers.get("White", ""),
                        "Black": game.headers.get("Black", ""),
                        "Result": game.headers.get("Result", ""),
                        "WhiteElo": game.headers.get("WhiteElo", ""),
                        "BlackElo": game.headers.get("BlackElo", ""),
                        "ECO": game.headers.get("ECO", ""),
                        "Opening": game.headers.get("Opening", ""),
                        "TimeControl": game.headers.get("TimeControl", ""),
                        "Termination": game.headers.get("Termination", ""),
                    }
                    games_data.append(game_data)
    return games_data

def save_to_csv(games_data, csv_file_path):
    games_df = pd.DataFrame(games_data)
    games_df.to_csv(csv_file_path, index=False)
    return games_df

def calculate_metrics(games_df):
    # Convert 'Date' column to datetime
    games_df['Date'] = pd.to_datetime(games_df['Date'], format='%Y.%m.%d')

    # Calculate the day of the week
    games_df['DayOfWeek'] = games_df['Date'].dt.day_name()

    # Filter for games played by the user
    user_games = games_df[(games_df['White'] == USERNAME) | (games_df['Black'] == USERNAME)]

    # Define a function to determine the outcome for the user
    def get_outcome(row):
        if row['White'] == USERNAME:
            if row['Result'] == '1-0':
                return 'win'
            elif row['Result'] == '0-1':
                return 'loss'
            else:
                return 'draw'
        elif row['Black'] == USERNAME:
            if row['Result'] == '0-1':
                return 'win'
            elif row['Result'] == '1-0':
                return 'loss'
            else:
                return 'draw'
        return 'unknown'

    # Apply the function to get the outcome
    user_games['Outcome'] = user_games.apply(get_outcome, axis=1)

    # Calculate win rate by day of the week
    win_rate_by_day = user_games.groupby('DayOfWeek')['Outcome'].value_counts(normalize=True).unstack().fillna(0)
    win_rate_by_day['win_rate'] = win_rate_by_day['win']

    # Calculate win/loss/draw rate by colour played
    user_games['Colour'] = user_games.apply(lambda x: 'white' if x['White'] == USERNAME else 'black', axis=1)
    outcome_by_colour = user_games.groupby('Colour')['Outcome'].value_counts(normalize=True).unstack().fillna(0)

    # Ensure the outcomes sum to 1 for each color
    outcome_by_colour_percent = outcome_by_colour.div(outcome_by_colour.sum(axis=1), axis=0)

    results = {
        'win_rate_by_day': win_rate_by_day['win_rate'].to_dict(),
        'outcome_by_colour': {
            'white': {
                'win': outcome_by_colour_percent.loc['white', 'win'],
                'loss': outcome_by_colour_percent.loc['white', 'loss'],
                'draw': outcome_by_colour_percent.loc['white', 'draw']
            },
            'black': {
                'win': outcome_by_colour_percent.loc['black', 'win'],
                'loss': outcome_by_colour_percent.loc['black', 'loss'],
                'draw': outcome_by_colour_percent.loc['black', 'draw']
            }
        }
    }

    return results

def save_to_json(results, json_file_path):
    with open(json_file_path, 'w') as json_file:
        json.dump(results, json_file)
    print(f"Metrics calculated and saved to {json_file_path}")

def main():
    project_dir, download_folder = create_download_folder()
    chrome_options = configure_chrome(download_folder)

    # Initialize the Chrome driver with the configured options
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # Log in to Chess.com
    login_chess_com(driver)

    # Download PGN files for the specified date range
    start_date = '06/02/2024'
    end_date = '06/08/2024'
    download_pgn_for_each_week(driver, start_date, end_date)

    # Close the browser
    driver.quit()

    # Extract game data from downloaded PGN files
    games_data = extract_game_data(download_folder)

    # Define the path to save the CSV file
    csv_file_path = os.path.join(project_dir, "chess_games_data.csv")

    # Save the extracted data to a CSV file
    games_df = save_to_csv(games_data, csv_file_path)

    # Calculate metrics and save to JSON file
    results = calculate_metrics(games_df)

    # Define the path to save the JSON file
    json_file_path = os.path.join(project_dir, 'user_metrics.json')

    # Save the results to a JSON file
    save_to_json(results, json_file_path)

if __name__ == "__main__":
    main()
