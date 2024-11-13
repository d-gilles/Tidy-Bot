# Imports
import requests
import pandas as pd
import re
import json
import boto3
import os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Metabase API connection
METABASE_URL = "https://<your_metabase_instance>.com" 

# Retrieve the API key from SSM Parameter Store
ssm = boto3.client('ssm')
parameter_name = '/production/metabase/api_key' 
response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
API_KEY = response['Parameter']['Value']

headers = {
    'Content-Type': 'application/json',
    "X-API-KEY": API_KEY  
}

def get_query_result(sql_query: str, API_KEY: str = API_KEY, db_id: int = 166) -> pd.DataFrame:
    """
    Executes a SQL query via the Metabase API against a database connected to Metabase.
    By default, it uses the Metabase internal database (ID 166).

    Args:
        sql_query (str): The SQL query to execute.
        API_KEY (str): The API key for authenticating with the Metabase API. Defaults to a global `API_KEY`.
        db_id (int): The ID of the database against which to run the query. Defaults to 166 (Metabase internal DB).

    Returns:
        pd.DataFrame: The query result as a Pandas DataFrame.
    """
    # Payload for the query to the Metabase API
    query_payload = {
        'database': db_id,  # Database ID
        'native': {
            'query': sql_query  # The actual SQL query
        },
        'type': 'native'
    }
    
    # Send POST request to the Metabase API to execute the query
    response = requests.post(f'{METABASE_URL}/api/dataset', json=query_payload, headers=headers)
    
    # Parse the JSON response and extract the data
    data = response.json()['data']
    
    # Extract column names and rows
    column_names = [col['name'] for col in data['cols']]
    rows = data['rows']
    
    # Return the data as a Pandas DataFrame
    return pd.DataFrame(rows, columns=column_names) #,response

def get_query_from_card(card_id: int) -> str:
    """
    Retrieves the SQL query from a Metabase card using its card ID.

    Args:
        card_id (int): The ID of the card to fetch the query from.

    Returns:
        str: The SQL query as a string.
    """
    # SQL to get the query stored in the card
    query = f""" 
        SELECT dataset_query::json->'native'->>'query' AS sql_query
        FROM report_card
        WHERE id = {card_id};
    """
    
    # Execute the query and return the SQL query from the card
    query_from_card = get_query_result(query).sql_query[0]
    return query_from_card

def get_card_result(card_id: int) -> pd.DataFrame:
    """
    Executes the SQL query from a Metabase card, resolving any nested models, 
    and returns the result as a Pandas DataFrame.

    Args:
        card_id (int): The ID of the card containing the query to execute.

    Returns:
        pd.DataFrame: The result of the query as a DataFrame.
    """
    # Get the query from the card
    query_from_card = get_query_from_card(card_id)
    
    # If the query contains a placeholder for a model, replace it with the actual query
    if "{{#1024-metabase-usage-base}}" in query_from_card:
        model = get_query_from_card(1024)  # Retrieve the model query
        # Replace the placeholder in the query with the actual model query
        updated_query = re.sub(r"{{#1024-metabase-usage-base}}", f"({model})", query_from_card)
        # Evaluate the query string to resolve any nested references
        query_including_model = eval(f'f"""{updated_query}"""')
        return get_query_result(query_including_model)
    
    else:
        # If no model replacement is needed, execute the query directly
        return get_query_result(query_from_card)

def manage_tag(type: str, id: int, new_name: str) -> requests.Response:
    """
    Updates the name of an object (e.g., card, dashboard) in Metabase using the API.

    Args:
        type (str): The type of the object to update (e.g., 'card', 'dashboard').
        id (int): The ID of the object to update.
        new_name (str): The new name to assign to the object.

    Returns:
        requests.Response: The HTTP response from the Metabase API.
    """
    payload = {
        "name": new_name  # New name for the object
    }
    
    # Send a PUT request to the Metabase API to update the object
    response = requests.put(f"{METABASE_URL}/api/{type}/{id}", headers=headers, json=payload)
    
    # Check if the update was successful
    if response.status_code == 200:
        print(f'Updated name of {type} {id} to "{new_name}"')
    else:
        print(f"Failed to update {type} {id}: {response.status_code}, {response.text}")
    
    return response

def change_many_items(df: pd.DataFrame, tag: str, remove: bool = False, suffix: bool = False):
    """
    Adds or removes a tag from the names of multiple Metabase items (cards, dashboards).

    Args:
        df (pd.DataFrame): The DataFrame containing the items to update.
        tag (str): The tag to add or remove.
        remove (bool, optional): Whether to remove the tag. Defaults to False (i.e., add the tag).
    """
    # If removing the tag, filter and update the names
    if remove:
        print(f'Removing tag {tag}')
        if not suffix:
            selection = df[df['name'].str.contains(re.escape(f'[{tag}]'), regex=True)]
            selection['name'] = selection['name'].str.replace(re.escape(f'[{tag}]'), '', regex=True)
        else:
            selection = df[df['name'].str.contains(re.escape(f' - {tag}'), regex=True)]
            selection['name'] = selection['name'].str.replace(re.escape(f' - {tag}'), '', regex=True)
        
        df = selection
    else:
        if not suffix:
            # If adding the tag, prepend the tag to each name
            print(f'Adding tag {tag}')
            df['name'] = [f'[{tag}]{name}' for name in df['name']]
        else:
            # If adding the tag, prepend the tag to each name
            print(f'Adding tag {tag}')
            df['name'] = [f'{name} - {tag}' for name in df['name']]
    
    # If no items are found with the tag, print a message
    if df.shape[0] == 0:
        print(f'No items found for tag {tag}. Done')
        return
    
    # Iterate over the items and update each one
    for index, row in df.iterrows():
        if df.loc[index, 'entity_type'] == 'table':
            print('Not changing tables')
            continue
        else:
            type = df.loc[index, 'entity_type']
            new_name = df.loc[index, 'name']
            id = df.loc[index, 'entity_id']
            manage_tag(type, id, new_name)

def get_test_set(card_id: int = 1039) -> pd.DataFrame:
    """
    Loads a test dataset of Metabase usage data.

    Returns:
        pd.DataFrame: The test dataset as a DataFrame.
    """
    # Execute a query to get the test dataset (using card 1039 as an example)
    df_metabase_usage = get_card_result(card_id)
    
    return df_metabase_usage

def last_day_of_next_quarter(date):
    today = date
    current_quarter = (today.month - 1) // 3 + 1
    next_quarter = current_quarter + 1
    
    if next_quarter > 4:
        next_quarter = 1
        year = today.year + 1
    else:
        year = today.year

    # Calculate the last month of the next quarter
    last_month_of_next_quarter = next_quarter * 3
    last_day = datetime(year, last_month_of_next_quarter, 1)+ relativedelta(months=1) + timedelta(days=-1)

    return last_day.strftime('%y-%m-%d')