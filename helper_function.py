import json
import time
import os
import logging
import boto3
import psycopg2
from helper_functions import *
import re

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


hello_intent = os.environ['Hello_message']
hello_intent_es = os.environ['Hello_message_es']
hello_intent_zh = os.environ['Hello_message_zh']
hello_intent_hm = os.environ['Hello_message_hm']
hello_intent_hy = os.environ['Hello_message_hy']
hello_intent_km = os.environ['Hello_message_km']
hello_intent_ko = os.environ['Hello_message_ko']
hello_intent_lo = os.environ['Hello_message_lo']
hello_intent_pt = os.environ['Hello_message_pt']
hello_intent_ru = os.environ['Hello_message_ru']
hello_intent_tl = os.environ['Hello_message_tl']
hello_intent_vi = os.environ['Hello_message_vi']
eligibility_en_intent = os.environ['Eligibility_en']
eligibility_es_intent = os.environ['Eligibility_es']
eligibility_hm_intent = os.environ['Eligibility_hm']
eligibility_hy_intent = os.environ['Eligibility_hy']
eligibility_km_intent = os.environ['Eligibility_km']
eligibility_ko_intent = os.environ['Eligibility_ko']
eligibility_lo_intent = os.environ['Eligibility_lo']
eligibility_pt_intent = os.environ['Eligibility_pt']
eligibility_ru_intent = os.environ['Eligibility_ru']
eligibility_tl_intent = os.environ['Eligibility_tl']
eligibility_vi_intent = os.environ['Eligibility_vi']
eligibility_zh_intent = os.environ['Eligibility_zh']
end_message_intent = os.environ['End_message']
end_message_intent_es = os.environ['End_message_es']
end_message_intent_hm = os.environ['End_message_hm']
end_message_intent_zh = os.environ['End_message_zh']
end_message_intent_km = os.environ['End_message_km']
end_message_intent_ko = os.environ['End_message_ko']
end_message_intent_lo = os.environ['End_message_lo']
end_message_intent_hy = os.environ['End_message_hy']
end_message_intent_pt = os.environ['End_message_pt']
end_message_intent_ru = os.environ['End_message_ru']
end_message_intent_tl = os.environ['End_message_tl']
end_message_intent_vi = os.environ['End_message_vi']
error_handle_intent = os.environ['Error_message']
apply_now_link = os.environ['Apply_Now_link']
help_link = os.environ['Help_link']
Port = os.environ["Port"]
Database = os.environ["DbName"]
Host = os.environ["JdbcUrl"]
secret_name = os.environ['SECRET_NAME']
region_name = os.environ["REGION"]
session = boto3.session.Session()
client = session.client(service_name='secretsmanager',region_name=region_name)
get_secret_value_response = client.get_secret_value(SecretId=secret_name)
secret_dict = json.loads(get_secret_value_response['SecretString'])
username = secret_dict['username']
passw = secret_dict['password']

names =[]

""" --- Helpers to build responses which match the structure of the necessary dialog actions --- """
def try_ex(func):
    """
    Call passed in function in try block. If KeyError is encountered return None.
    This function is intended to be used to safely access dictionary.

    Note that this function would have negative impact on performance.
    """

    try:
        return func()
    except KeyError:
        return None


def delete_output_attributes(names, attributes):
    for i in names:
        try:
            del attributes[i]
        except:
            pass
    
    return attributes


def elicit_slot(session_attributes, intent_name,slot_to_elicit,message,type,message_markdown=None,slots=None,responseCard=None,last_input=None,title=None):
    session_attributes['last_input']=last_input
    session_attributes['last_message']=message
    try:
        session_attributes['last_res_card']=json.dumps(responseCard)
    except:
        pass
    session_attributes['last_slot_elicit']=slot_to_elicit

    if slot_to_elicit=='endconv':
        try:
            session_attributes=delete_output_attributes(names,session_attributes)
        except:
            session_attributes=session_attributes
    if responseCard:
        x={
            "contentType": "application/vnd.amazonaws.card.generic",
            "genericAttachments": [
              {
                "attachmentLinkUrl": None,
                "buttons": responseCard,
                "imageUrl": None,
                "subTitle": None,
                "title": title
              }
            ],
            "version": "1"
          }
    else:
        x={}
    if message_markdown:
        y = {
            "markdown": message_markdown
        }
    else:
        y={}
    response = {'sessionAttributes': session_attributes,
                'dialogAction': {
                'type': 'ElicitSlot',
                'intentName': intent_name,
                'slots': slots,
                'slotToElicit': slot_to_elicit,
                'message': 
                                {
                                    'contentType': type,
                                    'content': '<speak>'+message+'</speak>'
                                }
                            }   
                        }
    response['sessionAttributes']['appContext'] =json.dumps({'responseCard': x,'altMessages':y})

    return response

def retry_counter(t, message, elicited_slot='',intent_name='', flag_var='retry_1', valid_list=['yes','no'],res_card=None,slots=None):
    sess=t['sessionAttributes']
    flag_var='retry_1_'+elicited_slot+'_'+t['currentIntent']['name']
    try:
        sess[flag_var]
    except:
        sess[flag_var] = 0
    if elicited_slot=='':
        elicited_slot=sess['last_slot_elicit']
    output_session_attributes = t['sessionAttributes'] if t['sessionAttributes'] is not None else {}
    if intent_name=='':
        intent_name=t['currentIntent']['name']
    if message == '':
        message = sess['last_message']
    message_markdown = message
    slots=t['currentIntent']['slots']
    if flag_var not in names:
        names.append(flag_var)
    if int(sess[flag_var])<3:
        sess[flag_var] = int(sess[flag_var])+1
        return elicit_slot(sess,intent_name, elicited_slot,message,'SSML',message_markdown,slots)
    else:
        sess=delete_output_attributes(names,sess) 
        return handle_error(t)


def close(session_attributes, fulfillment_state, message, type, message_markdown):
    if type:
        contentType=type
    try:
        session_attributes=delete_output_attributes(names,session_attributes)
    except:
        session_attributes=session_attributes

    y = {
        "markdown": message_markdown
    }
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': 'Fulfilled',
            'message': {
                        'contentType': contentType,
                         'content': '<speak>'+message+'</speak>'
                    }
                }
            }
    
    response['sessionAttributes']['appContext'] =json.dumps({'altMessages':y})
    return response

def valid_numlist(input_num):
    num_list = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "$", ".", ","]
    for i in input_num:
        if i not in num_list:
            return False
    return True


def check_number(input_num):
    if valid_numlist(input_num):
        dollar1 = re.findall('\$',input_num).count('$')==1
        dollar0 = re.findall('\$',input_num).count('$')==0
        if dollar1 and (input_num.startswith('$') or input_num.endswith('$')):
            pattern = re.compile(r'^\$?[0-9]\d*(?:,?\d+)*(?:\.\d{0,5})?\$?$')
            if re.match(pattern,input_num):
                return True
            else:
                return False
        elif dollar0:
            pattern = re.compile(r'^\$?[0-9]\d*(?:,?\d+)*(?:\.\d{0,5})?\$?$')
            if re.match(pattern,input_num):
                return True
            else:
                return False
        else:
            return False
    else:
        return False
    
def check_hsize(input_num):
    num_list = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    for i in input_num:
        if i not in num_list:
            return False
    return True    

def check_input(text):
    if text not in ['0','zero']:
        if text.isnumeric():
            return True
        else:
            return False
    else:
        return False
    
def update_num(input_num):
    return float(str(input_num).replace('$','').replace(',',''))
    
def update_hsize(input_num):
    return float(str(input_num).replace(',',''))


def handle_error(intent_request):
    session_attributes = intent_request['sessionAttributes']
    last_message_response = intent_request['sessionAttributes']['last_message']
    last_inputTranscript=intent_request['inputTranscript']
    currentIntent_name = intent_request['currentIntent']['name']
    last_slot_elicit = intent_request['sessionAttributes']['last_slot_elicit']
    print(intent_request)
    try:
        session_attributes=delete_output_attributes(names,session_attributes)
    except:
        session_attributes=session_attributes        
    output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    source = intent_request['invocationSource']
    if currentIntent_name in [hello_intent, eligibility_en_intent, end_message_intent] or last_slot_elicit in ['end_intents','endconv','stateres','citizenship','hhmembers','hhIncome','hhpregnant','otherprograms','eligible','noteligible']:
        message = "I'm sorry. I didn't get that. Let's start over.\
                    <p>Hi! I’m Robin. I can help you to see if you can get food with CalFresh, health care with Medi-Cal, or cash assistance with CalWORKs. Would you like to do that?</p>"
        message_markdown = "I'm sorry. I didn't get that. Let's start over. <br>\
                    <br>\
                    Hi! I’m Robin. I can help you to see if you can get food with CalFresh, health care with Medi-Cal, or cash assistance with CalWORKs. Would you like to do that?"
        return elicit_slot(output_session_attributes,hello_intent,'end_intents', message, 'SSML',message_markdown=message_markdown,responseCard=[{"text": "YES","value": "Yes"},{"text": "NO","value": "No"}],last_input=last_inputTranscript, title="Back to prescreening")
        
    elif currentIntent_name in [hello_intent_es, eligibility_es_intent, end_message_intent_es] or last_slot_elicit in ['end_intents_es','endconv_es','stateres_es','citizenship_es','hhmembers_es','hhIncome_es','hhpregnant_es','otherprograms_es','eligible_es','noteligible_es']:
        message = 'Disculpe, no quedó claro. Comencemos de nuevo.<br>\
                    <br>\
                    ¡Hola! Soy Robin. Puedo ayudarlo a ver si puede recibir alimentos con CalFresh, atención médica con Medi-Cal o asistencia en efectivo con CalWORKs. ¿Le gustaría hacerlo?'
        return elicit_slot(output_session_attributes,hello_intent_es,'end_intents_es', message, type='CustomPayload',responseCard=[{"text": "SÍ","value": "Yes"},{"text": "NO","value": "No"}],last_input=last_inputTranscript, title="Back to prescreening")
                
    elif currentIntent_name in [hello_intent_zh, eligibility_zh_intent, end_message_intent_zh] or last_slot_elicit in ['end_intents_zh','endconv_zh','stateres_zh','citizenship_zh','hhmembers_zh','hhIncome_zh','hhpregnant_zh','otherprograms_zh','eligible_zh','noteligible_zh']:
        message = "抱歉，我不明白。從頭再來。 <br>\
                    <br>\
                    你好！我是 Robin，我可以幫助您了解，您是否可以透過 CalFresh 獲得食物，透過 Medi-Cal 獲得醫保，透過 CalWORKs 獲得現金援助。需要嗎？"
        return elicit_slot(output_session_attributes,hello_intent_zh,'end_intents_zh', message, type='CustomPayload',responseCard=[{"text": "是","value": "Yes"},{"text": "否","value": "No"}],last_input=last_inputTranscript,title='Back to prescreening')
                
    elif currentIntent_name in [hello_intent_hm, eligibility_hm_intent, end_message_intent_hm] or last_slot_elicit in ['end_intents_hm','endconv_hm','stateres_hm','citizenship_hm','hhmembers_hm','hhIncome_hm','hhpregnant_hm','otherprograms_hm','eligible_hm','noteligible_hm']:
        message = "Kuv thov txim, Kuv tsis tau nkag siab.Cia peb los pib dua. <br>\
                    <br>\
                    Nyob Zoo! Kuv yog Robin.Kuv tuaj yeem pab koj los saib seb koj puas tuaj yeem tau txais zaub mov nrog CalFresh, kev saib xyuas kev noj qab haus huv nrog Medi-Cal, los sis kev pab nyiaj ntsuab nrog CalWORKs.Koj puas xav ua li ntawd?"
        return elicit_slot(output_session_attributes,hello_intent_hm,'end_intents_hm', message, type='CustomPayload',responseCard=[{"text": "YOG","value": "Yes"},{"text": "TSIS YOG","value": "No"}],last_input=last_inputTranscript, title="Back to prescreening")    
                
    elif currentIntent_name in [hello_intent_hy, eligibility_hy_intent, end_message_intent_hy] or last_slot_elicit in ['end_intents_hy','endconv_hy','stateres_hy','citizenship_hy','hhmembers_hy','hhIncome_hy','hhpregnant_hy','otherprograms_hy','eligible_hy','noteligible_hy']:
        message = "Ներեցեք, ես այն չեմ ստացել: Եկե’ք նորից սկսենք:  <br>\
                    <br>\
                    Ողջո’ւյն: Ես Ռոբինն եմ: Ես կարող եմ օգնել ձեզ տեսնել, թե արդյոք կարող եք ստանալ սնունդ CalFresh-ից, առողջապահական խնամք Medi-Cal-ից կամ կանխիկ գումարային օգնություն CalWORKs-ից: Կցանկանայի՞ք դա անել:"
        return elicit_slot(output_session_attributes,hello_intent_hy,'end_intents_hy', message, type='CustomPayload',responseCard=[{"text": "ԱՅՈ","value": "Yes"},{"text": "ՈՉ","value": "No"}],last_input=last_inputTranscript, title="Back to prescreening")

    elif currentIntent_name in [hello_intent_km, eligibility_km_intent, end_message_intent_km] or last_slot_elicit in ['end_intents_km','endconv_km','stateres_km','citizenship_km','hhmembers_km','hhIncome_km','hhpregnant_km','otherprograms_km','eligible_km','noteligible_km']:
        message = "សូមទោស ខ្ញុំមិនយល់ទេ ។  ឥឡូវ យើងនឹងនាំគ្នាចាប់ផ្តើមសារជាថ្មី ។ <br>\
                    <br>\
                    សួស្តី! ខ្ញុំឈ្មោះ Robin ។  ខ្ញុំអាចជួយអ្នកក្នុងការពិនិត្យមើលថា តើអ្នកអាចទទួលបានជំនួយអាហារពីកម្មវិធី CalFresh សេវាកម្មថែទាំសុខភាពពីកម្មវិធី Medi-Cal ឬជំនួយសាច់ប្រាក់ពីកម្មវិធី CalWORKs ដែរឬទេ ។  តើអ្នកចង់ឲ្យខ្ញុំជួយទេ?"
        return elicit_slot(output_session_attributes,hello_intent_km,'end_intents_km', message, type='CustomPayload',responseCard=[{"text": "ចាស","value": "Yes"},{"text": "ទេ","value": "No"}],last_input=last_inputTranscript, title="Back to prescreening") 
        
    elif currentIntent_name in [hello_intent_ko, eligibility_ko_intent, end_message_intent_ko] or last_slot_elicit in ['end_intents_ko','endconv_ko','stateres_ko','citizenship_ko','hhmembers_ko','hhIncome_ko','hhpregnant_ko','otherprograms_ko','eligible_ko','noteligible_ko']:
        message = "죄송합니다. 입력되지 않았습니다. 다시 해봅시다. <br>\
                    <br>\
                    안녕하세요! 저는 로빈입니다. CalFresh에서 식재료를, Medi-Cal에서 의료보험을, 또는 CalWORKs에서 현금 지원을 받으실 수 있는지 알아보는 것을 도와드리겠습니다. 계속하겠습니까?"
        return elicit_slot(output_session_attributes,hello_intent_ko,'end_intents_ko', message, type='CustomPayload',responseCard=[{"text": "예","value": "Yes"},{"text": "아니오","value": "No"}],last_input=last_inputTranscript, title="Back to prescreening")       
    
    elif currentIntent_name in [hello_intent_lo, eligibility_lo_intent, end_message_intent_lo] or last_slot_elicit in ['end_intents_lo','endconv_lo','stateres_lo','citizenship_lo','hhmembers_lo','hhIncome_lo','hhpregnant_lo','otherprograms_lo','eligible_lo','noteligible_lo']:
        message = "ຂໍສະແດງຄວາມເສຍໃຈ, ຂ້າພະເຈົ້າຍັງບໍ່ໄດ້ຮັບຂໍ້ມູນ. ມາເລີ່ມຕົ້ນໃໝ່. <br>\
                    <br>\
                    ສະບາຍດີ! ຂ້າພະເຈົ້າແມ່ນໂຣບິນ. ຂ້າພະເຈົ້າຊ່ວຍທ່ານໄດ້ຖ້າທ່ານຕ້ອງການໄດ້ຮັບການຊ່ວຍເຫຼືອດ້ານອາຫານດ້ວຍ CalFresh, ການດູແລສຸຂະພາບ Medi-Cal, ຫຼື ການຊ່ວຍເຫຼືອເງິນສົດ CalWORKs. ທ່ານຕ້ອງການເຮັດຫຼືບໍ່?"
        return elicit_slot(output_session_attributes,hello_intent_lo,'end_intents_lo', message, type='CustomPayload',responseCard=[{"text": "ແມ່ນ","value": "Yes"},{"text": "ບໍ່","value": "No"}],last_input=last_inputTranscript, title="Back to prescreening")

    elif currentIntent_name in [hello_intent_pt, eligibility_pt_intent, end_message_intent_pt] or last_slot_elicit in ['end_intents_pt','endconv_pt','stateres_pt','citizenship_pt','hhmembers_pt','hhIncome_pt','hhpregnant_pt','otherprograms_pt','eligible_pt','noteligible_pt']:
        message = "Desculpe, mas ainda não entendi. Vamos começar de novo. <br>\
                    <br>\
                    Olá!  Meu nome é Robin. Posso ajudar para ver se você consegue receber assistência do programa CalFresh, seguro de saúde do Medi-Cal ou assistência em dinheiro do CalWORKs. Gostaria de tentar?"
        return elicit_slot(output_session_attributes,hello_intent_pt,'end_intents_pt', message, type='CustomPayload',responseCard=[{"text": "SIM","value": "Yes"},{"text": "NÃO","value": "No"}],last_input=last_inputTranscript, title="Back to prescreening")
        
    elif currentIntent_name in [hello_intent_ru, eligibility_ru_intent, end_message_intent_ru] or last_slot_elicit in ['end_intents_ru','endconv_ru','stateres_ru','citizenship_ru','hhmembers_ru','hhIncome_ru','hhpregnant_ru','otherprograms_ru','eligible_ru','noteligible_ru']:
        message = "Извините, что-то идет не так. Давайте начнем заново. <br>\
                    <br>\
                    Привет! Меня зовут Robin. Я могу помочь вам узнать, можете ли вы получать питание по программе CalFresh, медицинское обслуживание по программе Medi-Cal или денежную помощь по программе CalWORKs. Вы бы этого хотели?"
        return elicit_slot(output_session_attributes,hello_intent_ru,'end_intents_ru', message, type='CustomPayload',responseCard=[{"text": "ДА","value": "Yes"},{"text": "НЕТ","value": "No"}],last_input=last_inputTranscript, title="Back to prescreening")    
        
    elif currentIntent_name in [hello_intent_tl, eligibility_tl_intent, end_message_intent_tl] or last_slot_elicit in ['end_intents_tl','endconv_tl','stateres_tl','citizenship_tl','hhmembers_tl','hhIncome_tl','hhpregnant_tl','otherprograms_tl','eligible_tl','noteligible_tl']:
        message = "Paumanhin, hindi ko naintindihan iyon.Magsimula tayo muli. <br>\
                    <br>\
                    Hi! Ako si Robin. Matutulungan kitang tingnan kung makakukuha ka ng pagkain sa CalFresh, pangangalagang pangkalusugan sa Medi-Cal, o tulong na pera sa CalWORKs. Gusto mo bang gawin iyon?"
        return elicit_slot(output_session_attributes,hello_intent_tl,'end_intents_tl', message, type='CustomPayload',responseCard=[{"text": "OO","value": "Yes"},{"text": "HINDI","value": "No"}],last_input=last_inputTranscript, title="Back to prescreening")        
        
    elif currentIntent_name in [hello_intent_vi, eligibility_vi_intent, end_message_intent_vi] or last_slot_elicit in ['end_intents_vi','endconv_vi','stateres_vi','citizenship_vi','hhmembers_vi','hhIncome_vi','hhpregnant_vi','otherprograms_vi','eligible_vi','noteligible_vi']:
        message = "Xin lỗi, tôi không hiểu. Hãy làm lại từ đầu. <br>\
                    <br>\
                    Xin chào! Tôi là Robin. Tôi có thể hỗ trợ xem liệu quý vị có thể nhận trợ cấp thực phẩm với CalFresh, chăm sóc sức khỏe với Medi-Cal, hoặc trợ cấp tiền mặt với CalWORKs hay không. Quý vị có muốn làm điều đó không?"
        return elicit_slot(output_session_attributes,hello_intent_vi,'end_intents_vi', message, type='CustomPayload',responseCard=[{"text": "CÓ","value": "Yes"},{"text": "KHÔNG","value": "No"}],last_input=last_inputTranscript, title="Back to prescreening")