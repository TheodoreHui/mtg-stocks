import re
import requests
from tqdm import tqdm
from unidecode import unidecode


def format_card_name(card_name:str):
    """
    Formats a card name to be used in a URL for querying from EDHREC.
    """
    first_card = card_name.split("//")[0].strip() # If the card is a split card, only use the first card
    non_alphas_regex = "[^\w\s-]" # Remove everything that's not alphanumeric or space or hyphen
    formatted_name = unidecode(first_card) # remove diacritics
    formatted_name = re.sub(non_alphas_regex, "", formatted_name)
    formatted_name = formatted_name.lower() # Make lowercase
    formatted_name = formatted_name.replace(" ", "-")  # Replace spaces with hyphens
    formatted_name = re.sub(r"-+", "-", formatted_name) # do not have multiple hyphens
    # print(f"In format_commander_name and formatted name is {formatted_name}")
    return formatted_name

def request_json(name:str, redirect=''):
    """
    Request JSON data from EDHREC for a card.

    Parameters:
    - name: card name
    - is_commander: boolean indicating whether the card is a commander
    - redirect: string indicating a redirect URL (optional)

    Returns:
    - json data on successful retrieval
    """
    formatted_name = format_card_name(name)
    if redirect:
        print(f"Redirected to {redirect}")
        json_url = f"https://json.edhrec.com/pages{redirect}.json"
    else:
        json_url = f"https://json.edhrec.com/pages/commanders/{formatted_name}.json"
    response = requests.get(json_url)
    if response.status_code == 200:
        json_data = response.json()
        if 'redirect' in json_data:
            return request_json(name, redirect=json_data['redirect'])
        # print(f"JSON request successful!")
        return json_data
    else:
        json_url = f"https://json.edhrec.com/pages/cards/{formatted_name}.json"
        response = requests.get(json_url)
        if response.status_code == 200:
            json_data = response.json()
            if 'redirect' in json_data:
                return request_json(name, redirect=json_data['redirect'])
            return json_data
        else:
            print(f"JSON request for \"{name}\" ({formatted_name}) failed! Try different card name")

def find_comp(data, sim_cards, colors, power = 3):
    """
    Finds complementary cards by scraping edhrec and scoring by edhrec's "synergy" metric

    Parameters:
    - data: raw card dataframe
    - sim_cards: cards to search on edhrec 
    - power: exponent to affect how much synergy vs repetition weights on the score (higher power ->  higher synergy, lower power -> higher repetition)

    Returns:
    - list of tuples of top 100 most comp cards, sorted in descending order of predicted synergy

    """
    valid_names = set(data['name'])
    scores = {}
    for card in tqdm(sim_cards[:100]):
        #print(card)
        json_data = request_json(card[1])
        #print(json_data)
        if json_data:
            for cmdr in json_data['container']['json_dict']['cardlists'][0]['cardviews']:
                syn_colors = data[data['name'] == cmdr['name']]['color_identity'].str.join("").tolist()
                if all([color in colors for color in syn_colors]):
                    scores[cmdr['name']] = 1

            for syn_list in json_data['container']['json_dict']['cardlists'][1:]:
                for synergy in syn_list['cardviews']:
                    if synergy['name'] in valid_names:
                        try:
                            syn_colors = data[data['name'] == synergy['name']]['color_identity'].str.join("").tolist()
                            #print(syn_colors, type(syn_colors))
                            if all([color in colors for color in syn_colors]):
                                if synergy['name'] in scores:
                                    scores[synergy['name']] += synergy['synergy'] ** power
                                else:
                                    scores[synergy['name']] = synergy['synergy'] ** power
                        except:
                            continue

        
        
                
            #print(sorted(json_data['cardlist'], key=lambda card: card['num_decks'], reverse=True))
    return sorted(scores.items(), key=lambda score: score[1], reverse=True)[:100]