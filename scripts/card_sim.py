import numpy as np
import pickle
import pandas as pd
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

def load_data(fp):
    """
    Reads in data.

    :param fp: filepath of data stored in pickle
    :returns: data stored in pickle
    """
    '''with open(fp, "rb") as f:
        data = pickle.load(f)
    return data'''
    def clean(x):
        try:
            out = eval(x)
        except:
            out = np.NaN
        return out

    return pd.read_csv(fp, converters={'color_identity':clean})


def clean_data(cards):
    """
    Performs multiple transformations on data, such as filtering, tokenizing text, and extracting keywords.
    
    :param cards: DataFrame containing information of each non-commander card, such as name, text, and color
    :param commanders: DataFrame containing information of each commander card, such as name, text, and color
    :returns: tuple containing all cleaned data, cleaned non-commander card data, and cleaned commander data
    """
    # filtering out non-legal cards in commander
    '''
    legal = pd.read_csv('../data/cardLegalities.csv').loc[:,['commander', 'uuid']]
    cards = cards.merge(legal,on='uuid')
    cards = cards[cards['commander'] == 'Legal']

    cards_clean = cards.loc[cards["text"].apply(lambda x: not (isinstance(x, float) and np.isnan(x))), ["name", "text", "color_identity", "type", "supertypes", 
        "subtypes", 'rarity', 'set', 'id']]
    '''
    def clean(x):
        try:
            out = eval(x)
        except:
            out = np.NaN
        return out

    cards['color_identity'] = cards['color_identity'].map(clean)

    return cards

def cosine_similarity(vector1, vector2):
    """
    Computes the cosine similarity between two vectors.
    
    Args:
    vector1 (torch.Tensor): A tensor representing the first vector.
    vector2 (torch.Tensor): A tensor representing the second vector.
    
    Returns:
    float: The cosine similarity between vector1 and vector2.
    """
    # Ensure the vectors are 1-dimensional
    
    # Compute the dot product between the two vectors
    dot_product = np.dot(vector1, vector2)
    
    # Compute the magnitudes (norms) of the vectors
    norm1 = np.linalg.norm(vector1)
    norm2 = np.linalg.norm(vector2)
    
    # Compute the cosine similarity
    cos_similarity = dot_product / (norm1 * norm2)
    
    return cos_similarity.item()

def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def find_sim(data, cmdr_colors, text):
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    # Create a boolean mask based on the condition
    mask = np.where(
        data['color_identity'].apply(lambda x: not isinstance(x, list)) | 
        (data['color_identity'].apply(lambda card_colors: isinstance(card_colors, list) and any([color in cmdr_colors for color in card_colors]))),
        True, False
    )

    # Apply the mask to filter the DataFrame
    filtered_cards = data[mask]
    encoded = model.encode(text)

    # Define the function to compute similarity
    def compute_similarity(row):
        try:
            similarity = cosine_similarity(encoded, model.encode(row.type + " " + str(row.supertypes) + " " + str(row.subtypes) + " " + str(row.text)))
        except TypeError as e:
            print(row)
        return similarity, row.name, row.type

    # Convert DataFrame to list of tuples for use with map
    rows = list(filtered_cards.itertuples(index=False))

    # Enable tqdm progress bar for the map function
    tqdm.pandas()
    scores = list(map(compute_similarity, tqdm(rows, desc="Computing similarities")))

    sorted_scores = sorted(scores, key=lambda x: x[0], reverse=True)
    
    return sorted_scores

