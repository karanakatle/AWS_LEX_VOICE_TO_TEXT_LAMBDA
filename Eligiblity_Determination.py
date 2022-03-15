from helper_functions import *

""" --- Function to start the conversation in English --- """

def welcome_message(intent_request):

    last_inputTranscript=intent_request['inputTranscript']
    slots = intent_request['currentIntent']['slots']
    end_intents = try_ex(lambda: slots['end_intents'])
    output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    source = intent_request['invocationSource']
    
    if last_inputTranscript.strip() == 'english':
        message='Hi! I’m Robin. I can help you to see if you can get food with CalFresh, health care with Medi-Cal, or cash assistance with CalWORKs. Would you like to do that?'
        message_markdown = 'Hi! I’m Robin. I can help you to see if you can get food with CalFresh, health care with Medi-Cal, or cash assistance with CalWORKs. Would you like to do that?'
        return elicit_slot(output_session_attributes,hello_intent,'end_intents', message, 'SSML', message_markdown=message_markdown, responseCard=[{"text": "YES","value": "Yes"},{"text": "NO","value": "No"}],last_input=last_inputTranscript, title="Proceed to prescreening?")

    if source == 'DialogCodeHook':
        logger.debug("We are in DialogCodeHook")
        if end_intents:
            if end_intents=='Yes':
                message = 'Also, this is just a screening. No matter the result, you can still apply to see if you qualify.\
                 <p>Now, I am going to ask you a few questions.</p>\
                 Does your household currently live in the state of California?'
                message_markdown='Also, this is just a screening. No matter the result, you can still apply to see if you qualify.<br>\
                                <br>\
                                Now, I’m going to ask you a few questions. <br>\
                                <br> \
                                Does your household currently live in the state of California?'
                return elicit_slot(output_session_attributes,eligibility_en_intent,'stateres', message,'SSML',message_markdown=message_markdown,responseCard=[{"text": "YES","value": "Yes"},{"text": "NO","value": "No"}],last_input=last_inputTranscript, title="Stateres")
                
            elif end_intents=='No':
                message = 'Okay. There are other programs that your county offers. Would you like to learn more about them?'
                return elicit_slot(output_session_attributes,eligibility_en_intent,'otherprograms', message,'SSML',responseCard=[{"text": "YES","value": "Yes"},{"text": "NO","value": "No"}], last_input=last_inputTranscript, title='Other Programs')
                
        elif (end_intents == None) or (end_intents==None and intent_request['currentIntent']['slotDetails']['end_intents']['originalValue']!=None):
            message='Hi! I’m Robin. I can help you to see if you can get food with CalFresh, health care with Medi-Cal, or cash assistance with CalWORKs. Would you like to do that?'
            message_markdown = 'Hi! I’m Robin. I can help you to see if you can get food with CalFresh, health care with Medi-Cal, or cash assistance with CalWORKs. Would you like to do that?'
            return elicit_slot(output_session_attributes,hello_intent,'end_intents', message, 'SSML',message_markdown=message_markdown, responseCard=[{"text": "YES","value": "Yes"},{"text": "NO","value": "No"}],last_input=last_inputTranscript, title="Proceed to prescreening?") 
            
        return {
                'sessionAttributes': output_session_attributes,
                'dialogAction': {
                'type': 'Delegate',
                'slots': slots
            }
        }         


""" --- Function that control the bot's behavior --- """

def determine_compensation(intent_request):

    last_inputTranscript=intent_request['inputTranscript']
    slots = intent_request['currentIntent']['slots']
    stateres = try_ex(lambda: slots['stateres'])
    hsize = try_ex(lambda: slots['hhmembers'])
    income = try_ex(lambda: slots['hhIncome'])
    pregnant = try_ex(lambda: slots['hhpregnant'])
    otherprograms = try_ex(lambda: slots['otherprograms'])
    eligible = try_ex(lambda: slots['eligible'])
    noteligible = try_ex(lambda: slots['noteligible'])
    output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    source = intent_request['invocationSource']
    connection = psycopg2.connect(user=username,password=passw,host=Host,port=Port,database=Database)
    cursor = connection.cursor()
    insert_query="INSERT INTO ie_ssp_owner_aie.cp_app_screener (household_reside_in_state_ind,pregnancy_or_child_under_18_ind,household_monthly_income,create_dt,screening_result_ma_ind,screening_result_calfresh_ind,screening_result_calworks_ind,create_user_id,household_members_num) VALUES ('{0}','{1}','{2}',current_timestamp,'{3}','{4}','{5}','{6}','{7}')"
    insert_query_state_no_condition="INSERT INTO ie_ssp_owner_aie.cp_app_screener (household_reside_in_state_ind,create_dt,screening_result_ma_ind,screening_result_calfresh_ind,screening_result_calworks_ind,create_user_id) VALUES ('{0}',current_timestamp,'{1}','{2}','{3}','{4}')"

    if source == 'DialogCodeHook':
        logger.debug('English Intent')
        if income:
            income = str(income)
            is_number = check_number(income)
            if not is_number:
                repeat_message="I am sorry, please give your income as a number, no letters. Like this: $1,000.00"
                return retry_counter(intent_request,repeat_message,'hhIncome',eligibility_en_intent,slots=slots)
        elif income == None and intent_request['recentIntentSummaryView'][0]['slotToElicit']=='hhIncome':
            repeat_message="I am sorry, please give your income as a number, no letters. Like this: $1,000.00"
            return retry_counter(intent_request,repeat_message,'hhIncome',eligibility_en_intent,slots=slots)
            
        if stateres:
            if stateres=='No':
                cursor.execute(insert_query_state_no_condition.format(stateres[0],'n','n','n',intent_request['userId']))
                connection.commit()
                message='Based on your answers, you may not qualify for CalFresh, Medi-Cal, or CalWORKs. But, there may be other programs you may qualify for. Would you still like to apply?'
                return elicit_slot(output_session_attributes,eligibility_en_intent,'noteligible', message, 'SSML',responseCard=[{"text": "YES","value": "Yes"},{"text": "NO","value": "No"}],title='Not Eligible')
        elif stateres == None and intent_request['sessionAttributes']['last_slot_elicit']=='stateres':
            return handle_error(intent_request)

        if otherprograms:
            if otherprograms == 'Yes':
                message='Okay. You can learn more about the programs your county offers here. Would you like to restart to see if you can get Medi-Cal, CalFresh, or CalWORKs?'
                message_markdown = 'Okay. [You can learn more about the programs your county offers here.]('+help_link+' "Program Descriptions") <br>\
                        <br> \
                        Would you like to restart to see if you can get Medi-Cal, CalFresh, or CalWORKs?'
                return elicit_slot(output_session_attributes,end_message_intent,'endconv',message, "SSML", message_markdown=message_markdown,responseCard=[{"text": "YES","value": "Yes"},{"text": "NO","value": "No"}],last_input=last_inputTranscript,title='EndConv')
            elif otherprograms == 'No':
                message='Thank you for chatting with me today. Have a good day! You can close the chat window when you are ready.'
                message_markdown = 'Thank you for chatting with me today. Have a good day!<br>\
                                    <br>\
                                    You can close the chat window when you are ready.'
                return close(output_session_attributes,'Fulfilled',message,'SSML',message_markdown)
        elif otherprograms==None and intent_request['recentIntentSummaryView'][0]['slotToElicit']=='otherprograms':
            return handle_error(intent_request)

        if noteligible:
            if noteligible == 'Yes':
                message="Great! I can help you with that! We need your personal and financial details. It will take 30-60 minutes to apply.\
                                Here are some documents you might need to upload at the end. If you don't have them right now, you can still apply and upload them later.\
                                Ready?\
                                <p>Apply Now</p>"
                message_markdown = 'Great! I can help you with that! \
                                We need your personal and financial details. It will take 30-60 minutes to apply.<br>\
                                <br>\
                                [Here are some documents you might need to upload at the end.]('+help_link+' "Program Description") If you don’t have them right now, you can still apply and upload them later.<br>\
                                <br>\
                                Ready? \
                                [Apply Now]('+apply_now_link+' "Before We Begin")'      
                return close(output_session_attributes,'Fulfilled',message,"SSML",message_markdown)
                    
            elif noteligible == 'No':
                message='Okay. You can learn more about the programs your county offers here. Would you like to restart to see if you can get Medi-Cal, CalFresh, or CalWORKs?'
                message_markdown = 'Okay. [You can learn more about the programs your county offers here.]('+help_link+' "Program Descriptions") <br>\
                        <br> \
                        Would you like to restart to see if you can get Medi-Cal, CalFresh, or CalWORKs?'
                return elicit_slot(output_session_attributes,end_message_intent,'endconv',message, "SSML",message_markdown=message_markdown, responseCard=[{"text": "YES","value": "Yes"},{"text": "NO","value": "No"}],last_input=last_inputTranscript,title='EndConv')
        elif noteligible==None and intent_request['recentIntentSummaryView'][0]['slotToElicit']=='noteligible':
            return handle_error(intent_request)

        if eligible:
            if eligible == "Yes":
                message = "Great! I can help you with that! We need your personal and financial details. It will take 30-60 minutes to apply.\
                                Here are some documents you might need to upload at the end. If you don't have them right now, you can still apply and upload them later.\
                                Ready?\
                                <p>Apply Now</p>"
                message_markdown = 'Great! I can help you with that! \
                                We need your personal and financial details. It will take 30-60 minutes to apply.<br>\
                                <br>\
                                [Here are some documents you might need to upload at the end.]('+help_link+' "Program Description") If you don’t have them right now, you can still apply and upload them later.<br>\
                                <br>\
                                Ready? \
                                [Apply Now]('+apply_now_link+' "Before We Begin")'           
                return close(output_session_attributes,'Fulfilled',message,"SSML",message_markdown)
                
            elif eligible == "No":
                message='Okay. You can learn more about the programs your county offers here. Would you like to restart to see if you can get Medi-Cal, CalFresh, or CalWORKs?'
                message_markdown = 'Okay. [You can learn more about the programs your county offers here.]('+help_link+' "Program Descriptions") <br>\
                        <br> \
                        Would you like to restart to see if you can get Medi-Cal, CalFresh, or CalWORKs?'               
                return elicit_slot(output_session_attributes,end_message_intent,'endconv',message, "SSML",message_markdown=message_markdown,responseCard=[{"text": "YES","value": "Yes"},{"text": "NO","value": "No"}],last_input=last_inputTranscript,title='EndConv')               
        elif eligible==None and intent_request['recentIntentSummaryView'][0]['slotToElicit']=='eligible':
            return handle_error(intent_request)
       
        if hsize:
            hsize=str(hsize)
            is_size = check_hsize(hsize)
            print('xxxxxxxxxxxxxxx')
            print(is_size)
            print(intent_request['recentIntentSummaryView'][0]['slotToElicit'])
            print(check_input(hsize))
            print(hsize)
            print(check_input(last_inputTranscript))
            print(last_inputTranscript)
            if not is_size:
                repeat_message = "I'm sorry, I still didn't get that. Please put the number of people in your household, such as the number 1 or 2 etc."
                return retry_counter(intent_request,repeat_message,'hhmembers',eligibility_en_intent)
            elif is_size and update_hsize(hsize)==0 and last_inputTranscript in ["0",'zero']:
                repeat_message = "I am sorry, household size should be at least 1 person. Please try again."
                return retry_counter(intent_request,repeat_message,'hhmembers',eligibility_en_intent)
            elif check_input(last_inputTranscript)==False and intent_request['recentIntentSummaryView'][0]['slotToElicit']=='hhmembers' and intent_request['outputDialogMode']!='Voice':
                repeat_message = "I'm sorry, I still didn't get that. Please put the number of people in your household, such as the number 1 or 2 etc."
                return retry_counter(intent_request,repeat_message,'hhmembers',eligibility_en_intent,slots=slots)
            elif check_input(hsize)==False and intent_request['recentIntentSummaryView'][0]['slotToElicit']=='hhmembers' and intent_request['outputDialogMode']=='Voice':
                repeat_message = "I'm sorry, I still didn't get that. Please put the number of people in your household, such as the number 1 or 2 etc."
                return retry_counter(intent_request,repeat_message,'hhmembers',eligibility_en_intent,slots=slots) 
        elif hsize==None and intent_request['recentIntentSummaryView'][0]['slotToElicit']=='hhmembers':
            repeat_message = "I'm sorry, I still didn't get that. Please put the number of people in your household, such as the number 1 or 2 etc."
            return retry_counter(intent_request,repeat_message,'hhmembers',eligibility_en_intent,slots=slots)

        if pregnant==None and intent_request['recentIntentSummaryView'][0]['slotToElicit']=='hhpregnant':
            return handle_error(intent_request)
                
        return {
            'sessionAttributes': output_session_attributes,
            'dialogAction': {
                'type': 'Delegate',
                'slots': slots
            }
        }

    else:
        
        if pregnant == 'No' and stateres == 'Yes':
            if update_hsize(hsize)<=8:
                cursor.execute("Select * from ie_ssp_owner_aie.cp_app_chatbot_decision WHERE household_size=cast("+hsize.replace(',','')+" AS varchar) AND program_name='calfresh';")
                data=cursor.fetchall()
                threshold_income_value = float(data[0][1])
                if update_num(income)>=threshold_income_value:
                    cursor.execute(insert_query.format(stateres[0],pregnant[0],update_num(income),'y','n','n',intent_request['userId'],update_hsize(hsize)))
                    connection.commit()

                    message = 'It looks like you might qualify for Medi-Cal<break time="1s"/>. Would you like to apply?'
                    return elicit_slot(output_session_attributes,eligibility_en_intent,'eligible', message, 'SSML',slots=slots,responseCard=[{"text": "YES","value": "Yes"},{"text": "NO","value": "No"}],last_input=last_inputTranscript, title="Eligible")

                elif update_num(income)<threshold_income_value:
                    cursor.execute(insert_query.format(stateres[0],pregnant[0],update_num(income),'y','y','n',intent_request['userId'],update_hsize(hsize)))
                    connection.commit()

                    message = 'It looks like you might qualify for Medi-Cal and CalFresh.<break time="1s"/> Would you like to apply?'
                    return elicit_slot(output_session_attributes,eligibility_en_intent,'eligible', message, 'SSML',slots=slots,responseCard=[{"text": "YES","value": "Yes"},{"text": "NO","value": "No"}],last_input=last_inputTranscript, title="Eligible")

            elif update_hsize(hsize)>8:
                difference_hsize=update_hsize(hsize)-8
                cursor.execute("Select * from ie_ssp_owner_aie.cp_app_chatbot_decision WHERE household_size='8' AND program_name='calfresh';")
                data1=cursor.fetchall()
                cursor.execute("Select * from ie_ssp_owner_aie.cp_app_chatbot_decision WHERE household_size='additional per person' AND program_name='calfresh';")
                data2=cursor.fetchall()
                threshold_income_value = float(data1[0][1])+(difference_hsize*float(data2[0][1]))
                if update_num(income)>=threshold_income_value:
                    cursor.execute(insert_query.format(stateres[0],pregnant[0],update_num(income),'y','n','n',intent_request['userId'],update_hsize(hsize)))
                    connection.commit()
                    message = 'It looks like you might qualify for Medi-Cal<break time="1s"/>. Would you like to apply?'
                    return elicit_slot(output_session_attributes,eligibility_en_intent,'eligible', message, 'SSML',slots=slots,responseCard=[{"text": "YES","value": "Yes"},{"text": "NO","value": "No"}],last_input=last_inputTranscript, title="Eligible")

                elif update_num(income)<threshold_income_value:
                    cursor.execute(insert_query.format(stateres[0],pregnant[0],update_num(income),'y','y','n',intent_request['userId'],update_hsize(hsize)))
                    connection.commit()

                    message = 'It looks like you might qualify for Medi-Cal and CalFresh.<break time="1s"/> Would you like to apply?'
                    return elicit_slot(output_session_attributes,eligibility_en_intent,'eligible', message, 'SSML',slots=slots,responseCard=[{"text": "YES","value": "Yes"},{"text": "NO","value": "No"}],last_input=last_inputTranscript, title="Eligible")

        elif pregnant == 'Yes' and stateres == 'Yes':
            if update_hsize(hsize)<=8:
                cursor.execute("Select * from ie_ssp_owner_aie.cp_app_chatbot_decision WHERE household_size=cast("+hsize.replace(',','')+" AS varchar) AND program_name='calfresh';")
                data_calfresh = cursor.fetchall()
                cursor.execute("Select * from ie_ssp_owner_aie.cp_app_chatbot_decision WHERE household_size=cast("+hsize.replace(',','')+" AS varchar) AND program_name='calworks';")
                data_calworks = cursor.fetchall()
                threshold_income_value_calfresh = float(data_calfresh[0][1])
                threshold_income_value_calworks = float(data_calworks[0][1])
                if update_num(income)>=threshold_income_value_calfresh and update_num(income)>=threshold_income_value_calworks:
                    cursor.execute(insert_query.format(stateres[0],pregnant[0],update_num(income),'y','n','n',intent_request['userId'],update_hsize(hsize)))
                    connection.commit()
                    message = 'It looks like you might qualify for Medi-Cal<break time="1s"/>. Would you like to apply?'
                    return elicit_slot(output_session_attributes,eligibility_en_intent,'eligible', message, 'SSML',slots=slots,responseCard=[{"text": "YES","value": "Yes"},{"text": "NO","value": "No"}],last_input=last_inputTranscript, title="Eligible")

                elif update_num(income)<threshold_income_value_calfresh and update_num(income)<threshold_income_value_calworks:
                    cursor.execute(insert_query.format(stateres[0],pregnant[0],update_num(income),'y','y','y',intent_request['userId'],update_hsize(hsize)))
                    connection.commit()

                    message = 'It looks like you might qualify for Medi-Cal, CalFresh and CalWORKs.<break time="1s"/> Would you like to apply?'
                    return elicit_slot(output_session_attributes,eligibility_en_intent,'eligible', message,'SSML',slots=slots,responseCard=[{"text": "YES","value": "Yes"},{"text": "NO","value": "No"}],last_input=last_inputTranscript, title="Eligible")
                    
                elif update_num(income)>=threshold_income_value_calfresh and update_num(income)<threshold_income_value_calworks:
                    cursor.execute(insert_query.format(stateres[0],pregnant[0],update_num(income),'y','n','y',intent_request['userId'],update_hsize(hsize)))
                    connection.commit()
                   
                    message = 'It looks like you might qualify for Medi-Cal and CalWORKs. <break time="1s"/>Would you like to apply?'
                    return elicit_slot(output_session_attributes,eligibility_en_intent,'eligible', message, 'SSML',slots=slots, responseCard=[{"text": "YES","value": "Yes"},{"text": "NO","value": "No"}],last_input=last_inputTranscript, title="Eligible")
                
                elif update_num(income)<threshold_income_value_calfresh and update_num(income)>=threshold_income_value_calworks:
                    cursor.execute(insert_query.format(stateres[0],pregnant[0],update_num(income),'y','y','n',intent_request['userId'],update_hsize(hsize)))
                    connection.commit()

                    message = 'It looks like you might qualify for Medi-Cal and CalFresh.<break time="1s"/> Would you like to apply?'
                    return elicit_slot(output_session_attributes,eligibility_en_intent,'eligible', message, 'SSML',slots=slots,responseCard=[{"text": "YES","value": "Yes"},{"text": "NO","value": "No"}],last_input=last_inputTranscript, title="Eligible")

                    
            elif update_hsize(hsize)>8 and update_hsize(hsize)<=10:
                cursor.execute("Select * from ie_ssp_owner_aie.cp_app_chatbot_decision WHERE household_size=cast("+hsize.replace(',','')+" AS varchar) AND program_name='calworks';")
                data_calworks = cursor.fetchall()
                cursor.execute("Select * from ie_ssp_owner_aie.cp_app_chatbot_decision WHERE household_size='8' AND program_name='calfresh';")
                data_calfresh = cursor.fetchall()
                difference_hsize=update_hsize(hsize)-8
                cursor.execute("Select * from ie_ssp_owner_aie.cp_app_chatbot_decision WHERE household_size='additional per person' AND program_name='calfresh';")
                additional_calfresh_data=cursor.fetchall()
                threshold_income_value_calworks = float(data_calworks[0][1])
                threshold_income_value_calfresh = float(data_calfresh[0][1])+(difference_hsize*float(additional_calfresh_data[0][1]))
                if update_num(income)>=threshold_income_value_calfresh and update_num(income)>=threshold_income_value_calworks:
                    cursor.execute(insert_query.format(stateres[0],pregnant[0],update_num(income),'y','n','n',intent_request['userId'],update_hsize(hsize)))
                    connection.commit()
                    message = 'It looks like you might qualify for Medi-Cal<break time="1s"/>. Would you like to apply?'
                    return elicit_slot(output_session_attributes,eligibility_en_intent,'eligible', message, 'SSML',slots=slots,responseCard=[{"text": "YES","value": "Yes"},{"text": "NO","value": "No"}],last_input=last_inputTranscript, title="Eligible")

                elif update_num(income)<threshold_income_value_calfresh and update_num(income)<threshold_income_value_calworks:
                    cursor.execute(insert_query.format(stateres[0],pregnant[0],update_num(income),'y','y','y',intent_request['userId'],update_hsize(hsize)))
                    connection.commit()

                    message = 'It looks like you might qualify for Medi-Cal, CalFresh and CalWORKs.<break time="1s"/> Would you like to apply?'
                    return elicit_slot(output_session_attributes,eligibility_en_intent,'eligible', message,'SSML',slots=slots,responseCard=[{"text": "YES","value": "Yes"},{"text": "NO","value": "No"}],last_input=last_inputTranscript, title="Eligible")
  
                elif update_num(income)>=threshold_income_value_calfresh and update_num(income)<threshold_income_value_calworks:
                    cursor.execute(insert_query.format(stateres[0],pregnant[0],update_num(income),'y','n','y',intent_request['userId'],update_hsize(hsize)))
                    connection.commit()
                    
                    message = 'It looks like you might qualify for Medi-Cal and CalWORKs. <break time="1s"/>Would you like to apply?'
                    return elicit_slot(output_session_attributes,eligibility_en_intent,'eligible', message, 'SSML',slots=slots, responseCard=[{"text": "YES","value": "Yes"},{"text": "NO","value": "No"}],last_input=last_inputTranscript, title="Eligible")
                
                elif update_num(income)<threshold_income_value_calfresh and update_num(income)>=threshold_income_value_calworks:
                    cursor.execute(insert_query.format(stateres[0],pregnant[0],update_num(income),'y','y','n',intent_request['userId'],update_hsize(hsize)))
                    connection.commit()

                    message = 'It looks like you might qualify for Medi-Cal and CalFresh.<break time="1s"/> Would you like to apply?'
                    return elicit_slot(output_session_attributes,eligibility_en_intent,'eligible', message, 'SSML',slots=slots,responseCard=[{"text": "YES","value": "Yes"},{"text": "NO","value": "No"}],last_input=last_inputTranscript, title="Eligible")

                    
                            
            elif update_hsize(hsize)>10:
                difference_hsize_calworks=update_hsize(hsize)-10
                difference_hsize_calfresh=update_hsize(hsize)-8
                cursor.execute("Select * from ie_ssp_owner_aie.cp_app_chatbot_decision WHERE household_size='10' AND program_name='calworks';")
                data_calworks = cursor.fetchall()
                cursor.execute("Select * from ie_ssp_owner_aie.cp_app_chatbot_decision WHERE household_size='8' AND program_name='calfresh';")
                data_calfresh = cursor.fetchall()
                cursor.execute("Select * from ie_ssp_owner_aie.cp_app_chatbot_decision WHERE household_size='additional per person' AND program_name='calfresh';")
                additional_calfresh_data=cursor.fetchall()
                cursor.execute("Select * from ie_ssp_owner_aie.cp_app_chatbot_decision WHERE household_size='additional per person' AND program_name='calworks';")
                additional_calworks_data=cursor.fetchall()
                threshold_income_value_calworks = float(data_calworks[0][1])+float(difference_hsize_calworks*float(additional_calworks_data[0][1]))
                threshold_income_value_calfresh = float(data_calfresh[0][1])+float(difference_hsize_calfresh*float(additional_calfresh_data[0][1]))
                if update_num(income)>=threshold_income_value_calfresh and update_num(income)>=threshold_income_value_calworks:
                    cursor.execute(insert_query.format(stateres[0],pregnant[0],update_num(income),'y','n','n',intent_request['userId'],update_hsize(hsize)))
                    connection.commit()
                    
                    message = 'It looks like you might qualify for Medi-Cal<break time="1s"/>. Would you like to apply?'
                    return elicit_slot(output_session_attributes,eligibility_en_intent,'eligible', message, 'SSML',slots=slots,responseCard=[{"text": "YES","value": "Yes"},{"text": "NO","value": "No"}],last_input=last_inputTranscript, title="Eligible")

                        
                elif update_num(income)<threshold_income_value_calfresh and update_num(income)<threshold_income_value_calworks:
                    cursor.execute(insert_query.format(stateres[0],pregnant[0],update_num(income),'y','y','y',intent_request['userId'],update_hsize(hsize)))
                    connection.commit()

                    message = 'It looks like you might qualify for Medi-Cal, CalFresh and CalWORKs.<break time="1s"/> Would you like to apply?'
                    return elicit_slot(output_session_attributes,eligibility_en_intent,'eligible', message,'SSML',slots=slots,responseCard=[{"text": "YES","value": "Yes"},{"text": "NO","value": "No"}],last_input=last_inputTranscript, title="Eligible")
  
                elif update_num(income)>=threshold_income_value_calfresh and update_num(income)<threshold_income_value_calworks:
                    cursor.execute(insert_query.format(stateres[0],pregnant[0],update_num(income),'y','n','y',intent_request['userId'],update_hsize(hsize)))
                    connection.commit()
                    message = 'It looks like you might qualify for Medi-Cal and CalWORKs. <break time="1s"/>Would you like to apply?'
                    return elicit_slot(output_session_attributes,eligibility_en_intent,'eligible', message, 'SSML',slots=slots, responseCard=[{"text": "YES","value": "Yes"},{"text": "NO","value": "No"}],last_input=last_inputTranscript, title="Eligible")
                
                elif update_num(income)<threshold_income_value_calfresh and update_num(income)>=threshold_income_value_calworks:
                    cursor.execute(insert_query.format(stateres[0],pregnant[0],update_num(income),'y','y','n',intent_request['userId'],update_hsize(hsize)))
                    connection.commit()

                    message = 'It looks like you might qualify for Medi-Cal and CalFresh.<break time="1s"/> Would you like to apply?'
                    return elicit_slot(output_session_attributes,eligibility_en_intent,'eligible', message, 'SSML',slots=slots,responseCard=[{"text": "YES","value": "Yes"},{"text": "NO","value": "No"}],last_input=last_inputTranscript, title="Eligible")

""" --- Function to end the conversation in English --- """

def end_conversation(intent_request):

    last_inputTranscript=intent_request['inputTranscript']
    slots = intent_request['currentIntent']['slots']
    endconv = try_ex(lambda: slots['endconv'])
    output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    source = intent_request['invocationSource']

    if source == 'DialogCodeHook':
        logger.debug("We are in DialogCodeHook")
        if endconv:
            if endconv == 'Yes':
                message = 'Also, this is just a screening. No matter the result, you can still apply to see if you qualify.\
                 <p>Now, I am going to ask you a few questions.</p>\
                 Does your household currently live in the state of California?'
                message_markdown='Also, this is just a screening. No matter the result, you can still apply to see if you qualify.<br>\
                                <br>\
                                Now, I’m going to ask you a few questions. <br>\
                                <br> \
                                Does your household currently live in the state of California?'
                try:
                    output_session_attributes=delete_output_attributes(names,output_session_attributes)
                except:
                    output_session_attributes=output_session_attributes

                return elicit_slot(output_session_attributes,eligibility_en_intent,'stateres', message, 'SSML',message_markdown=message_markdown,responseCard=[{"text": "YES","value": "Yes"},{"text": "NO","value": "No"}],last_input=last_inputTranscript, title="Stateres")
    
            elif endconv == 'No':
                message='Thank you for chatting with me today. Have a good day! You can close the chat window when you are ready.'
                message_markdown = 'Thank you for chatting with me today. Have a good day!<br>\
                                <br>\
                                You can close the chat window when you are ready.'
                return close(output_session_attributes,'Fulfilled',message,'SSML',message_markdown)
                    
        elif (endconv == None) or (endconv==None and intent_request['currentIntent']['slotDetails']['endconv']['originalValue']!=None):
            return handle_error(intent_request)
            
        return {
                'sessionAttributes': output_session_attributes,
                'dialogAction': {
                'type': 'Delegate',
                'slots': slots
            }
        }
