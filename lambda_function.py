import json
import tidybot as tb  
from datetime import datetime
import logging
import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

sentry_sdk.init(
    integrations=[AwsLambdaIntegration()],
    release='TidyBot@0.1'
    )

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def lambda_handler(event, context):
    results = {
        "p1_items": None, #product 1
        "p2_items": None, #product 2
        "engineering_items": None,
        "delete_items": None,
        "delete_later_items": None,
        "review_items": None,
        "errors": []
    }
    
    if event.get('card',False) and event.get('tag', False):
        card = event["card"]
        tag = event["tag"]
        print(f'Card Id and tag are give, changing given Items from card {card}.')
        
        suffix = event.get("suffix", False)
        remove = event.get("remove", False)
        try:
            tb.change_many_items(tb.get_card_result(card),tag,suffix=suffix,remove=remove )
            status_code = 200 
            
        except Exception as e:
            logger.error(f"Error tagging giving items: {e}")
            results['errors'].append(f"Requested items: {e}")
            status_code = 500
        
        return {
            'statusCode': status_code
            }
    try:
        p1_items = tb.get_card_result(1030)
        tb.change_many_items(p1_items, 'Ⓚ', suffix=True)
        results['p1_items'] = "Success"
    except Exception as e:
        logger.error(f"Error tagging p1 items: {e}")
        results['errors'].append(f"p1 items: {e}")
    
    try:
        p2_items = tb.get_card_result(1032)
        tb.change_many_items(p2_items, '🅟', suffix=True)
        results['p2_items'] = "Success"
    except Exception as e:
        logger.error(f"Error tagging p2 items: {e}")
        results['errors'].append(f"p2 items: {e}")
    
    try:
        engineering_items = tb.get_card_result(1031)
        tb.change_many_items(engineering_items, '⚙️', suffix=True)
        results['engineering_items'] = "Success"
    except Exception as e:
        logger.error(f"Error tagging Engineering items: {e}")
        results['errors'].append(f"Engineering items: {e}")
    
    try:
        delete_items = tb.get_card_result(1038)
        tb.change_many_items(delete_items, 'delete')
        results['delete_items'] = "Success"
    except Exception as e:
        logger.error(f"Error tagging delete items: {e}")
        results['errors'].append(f"Delete items: {e}")
    
    try:
        date = datetime.today()
        delete_tag = f'delete at {tb.last_day_of_next_quarter(date)}'
        delete_later_items = tb.get_card_result(1026)
        tb.change_many_items(delete_later_items, delete_tag)
        results['delete_later_items'] = "Success"
    except Exception as e:
        logger.error(f"Error tagging delete later items: {e}")
        results['errors'].append(f"Delete later items: {e}")
    
    try:
        review_items = tb.get_card_result(1037)
        tb.change_many_items(review_items, 'review')
        results['review_items'] = "Success"
    except Exception as e:
        logger.error(f"Error tagging review items: {e}")
        results['errors'].append(f"Review items: {e}")
    
    status_code = 200 if not results['errors'] else 500
    
    
    return {
        'statusCode': status_code,
        'body': results
    }