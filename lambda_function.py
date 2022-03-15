from helper_functions import *
from Eligiblity_Determination import *
from Eligiblity_Determination_es import *
from Eligiblity_Determination_zh import *
from Eligiblity_Determination_hm import *
from Eligiblity_Determination_hy import *
from Eligiblity_Determination_km import *
from Eligiblity_Determination_ko import *
from Eligiblity_Determination_lo import *
from Eligiblity_Determination_pt import *
from Eligiblity_Determination_ru import *
from Eligiblity_Determination_tl import *
from Eligiblity_Determination_vi import *

""" --- Intents --- """

def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))
        
    intent_name = intent_request['currentIntent']['name']
    logger.debug("We are in Dispatch function with intent "+intent_name)
    intent_request['sessionAttributes'] = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}

    if intent_name !=error_handle_intent :
        try :
            intent_request['sessionAttributes']['flag']
        except:
            intent_request['sessionAttributes']['flag']=1
    
    # Dispatch to your bot's intent handlers
    if intent_name == end_message_intent:
        return end_conversation(intent_request)
    elif intent_name == end_message_intent_es:
        return end_conversation_es(intent_request)
    elif intent_name == end_message_intent_zh:
        return end_conversation_zh(intent_request)
    elif intent_name == end_message_intent_hm:
        return end_conversation_hm(intent_request)
    elif intent_name == end_message_intent_hy:
        return end_conversation_hy(intent_request)
    elif intent_name == end_message_intent_km:
        return end_conversation_km(intent_request)
    elif intent_name == end_message_intent_ko:
        return end_conversation_ko(intent_request)
    elif intent_name == end_message_intent_lo:
        return end_conversation_lo(intent_request)
    elif intent_name == end_message_intent_ru:
        return end_conversation_ru(intent_request)
    elif intent_name == end_message_intent_tl:
        return end_conversation_tl(intent_request)
    elif intent_name == end_message_intent_vi:
        return end_conversation_vi(intent_request)
    elif intent_name == end_message_intent_pt:
        return end_conversation_pt(intent_request)
    elif intent_name == hello_intent:
        return welcome_message(intent_request)
    elif intent_name == hello_intent_es:
        return welcome_message_es(intent_request)
    elif intent_name == hello_intent_zh:
        return welcome_message_zh(intent_request)
    elif intent_name == hello_intent_hm:
        return welcome_message_hm(intent_request)
    elif intent_name == hello_intent_hy:
        return welcome_message_hy(intent_request)
    elif intent_name == hello_intent_km:
        return welcome_message_km(intent_request)
    elif intent_name == hello_intent_ko:
        return welcome_message_ko(intent_request)
    elif intent_name == hello_intent_lo:
        return welcome_message_lo(intent_request)
    elif intent_name == hello_intent_pt:
        return welcome_message_pt(intent_request)
    elif intent_name == hello_intent_ru:
        return welcome_message_ru(intent_request)
    elif intent_name == hello_intent_tl:
        return welcome_message_tl(intent_request)
    elif intent_name == hello_intent_vi:
        return welcome_message_vi(intent_request)
    elif intent_name == eligibility_en_intent:
        return determine_compensation(intent_request)
    elif intent_name == eligibility_es_intent:
        return determine_compensation_es(intent_request)
    elif intent_name == eligibility_zh_intent:
        return determine_compensation_zh(intent_request)
    elif intent_name == eligibility_hm_intent:
        return determine_compensation_hm(intent_request)
    elif intent_name == eligibility_hy_intent:
        return determine_compensation_hy(intent_request)
    elif intent_name == eligibility_km_intent:
        return determine_compensation_km(intent_request)
    elif intent_name == eligibility_ko_intent:
        return determine_compensation_ko(intent_request)
    elif intent_name == eligibility_lo_intent:
        return determine_compensation_lo(intent_request)
    elif intent_name == eligibility_pt_intent:
        return determine_compensation_pt(intent_request)
    elif intent_name == eligibility_ru_intent:
        return determine_compensation_ru(intent_request)
    elif intent_name == eligibility_tl_intent:
        return determine_compensation_tl(intent_request)
    elif intent_name == eligibility_vi_intent:
        return determine_compensation_vi(intent_request)
    else:
        return handle_error(intent_request)
        
    raise Exception('Intent with name ' + intent_name + ' not supported')


""" --- Main handler --- """


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    print(json.dumps(event, indent=4))

    try :
        return dispatch(event)
    except Exception as e:
        print(e)
        try:
            return handle_error(event)
        except:
            pass