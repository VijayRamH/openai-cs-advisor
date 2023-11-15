############################################################
# Simulation for a customer support advisor. Provides
# inputs on specific customer data (for a particular date)
# and also helps diagnose issues with reporting capability.
############################################################

# Load required modules
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI

# Load all keys required and instantiate openai
load_dotenv(find_dotenv(), override=True)
client = OpenAI()

################################################################################################
# Define custom functions to deal with CS requests
# get_customer_usage_data()   -> retrieve customer data
# analyse_data_anomaly()      -> analyse retrieved data for anomalies (if any)
# generate_error_pdf_report() -> generate error report in pdf format if any anomalies were found
################################################################################################

def get_customer_usage_data_for_specific_inlet(email, date, inlet):
  #Ideally you would connect to a datastore and pull this out.
  #For simulation this function reads from one of the 2 files in the
  #project folder /files and loads them up
  return "Data for customer is available as an array [100,200,300]"

def analyse_data_anomaly(data):
  #return "Data has some anomalies. Leakage anomalies"
  return "Data looks good. No issues"

def generate_error_pdf_report(data):
  return "Leakage issues seen as data is increasing constantly"

def generate_clear_pdf_report(data):
  return "Data looks good. Sensors are working fine."

cs_functions = [
  {
    "type": "function",
    "function": {
      "name": "get_customer_usage_data_for_specific_inlet",
      "description": "Get or pull data for a particular customer for a particular date for a particular inlet debugging or support purpose as requested by the user. If no inlet is provided assume it is called COM",
      "parameters": {
            "type": "object",
            "properties": {
                "customer_email": {
                    "type": "string",
                    "description": "The email id used by the customer"
                },
                "date": {
                    "type": "string",
                    "description": "The date for which customer data needs to be retrieved. It must be in MMDDYYYY format"
                },
                "inlet": {
                    "type": "string",
                    "description": "The inlet for which customer data needs to be retrieved."
                },                
            },
            "required": ["customer_email", "date", "inlet"]
        }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "analyse_data_anomaly",
      "description": "Analyse customer data for any anomaly and report back the same if present",
      "parameters": {
          "type": "object",
          "properties": {
              "data": {
                  "type": "string",
                  "description": "A list of customer data points required for analysis to identify anomalies if any"
              }
          },
          "required": ["data"]
      },
    }
  },
  {
    "type": "function",
    "function": {
      "name": "generate_error_pdf_report",
      "description": "Generate an pdf report on the identfied anomalies in customer data",
      "parameters": {
            "type": "object",
            "properties": {
                "anomaly_data": {
                    "type": "string",
                    "description": "List of errors identified that need to be output in an error pdf report format"
                }
            },
            "required": ["anomaly_data"]
      }
    },  
  },
  {
    "type": "function",
    "function": {
      "name": "generate_clear_pdf_report",
      "description": "Generate an pdf report including clean data for the customer",
      "parameters": {
            "type": "object",
            "properties": {
                "clean_data": {
                    "type": "string",
                    "description": "Clean data to be output in a pdf report format"
                }
            },
            "required": ["clean_data"]
      }
    },  
  }  
]

#print(function_descriptions_multiple)

#--------------------------------------
# Create the cs assistant
#--------------------------------------
my_assistant = client.beta.assistants.create(
  name="WEGoT CS Assistant",
  instructions="You are a customer support agent. Use the provided functions to answer questions that are posted to you by the user who is a customer service representative trying to debug issues for their clients.",
  model="gpt-3.5-turbo-1106",
  tools=cs_functions
)

print(f"[CS-Assist] Created assistant {my_assistant.id}")

#--------------------------------------
# Create a thread
#--------------------------------------
chat_thread = client.beta.threads.create()
print(f"[CS-Assist] Created thread {chat_thread.id}")

#--------------------------------------
# Create a user message and send it to
# the CS assistant
#--------------------------------------
def ask_cs_assistant(query, history):
  global run
  # Create a new message on existing chat thread
  msg = client.beta.threads.messages.create(
      thread_id=chat_thread.id,
      role="user",
      content=query
    )
  print(f"[CS-Assist] Created msg {msg.id}")

  # Run user query on the thread
  run = client.beta.threads.runs.create(
      thread_id=chat_thread.id,
      assistant_id=my_assistant.id,
      instructions="Please use functions if you find them relevant to use based on user queries."
  )

  import time
  import json

  #Keep processing all custom functions till the run is completed
  #Once done exit the loop and get back to the main function to wait for the 
  #next CS request

  while True:
    time.sleep(2)
    run = client.beta.threads.runs.retrieve(
        thread_id=chat_thread.id,
        run_id=run.id
    )
    
    # If run is completed, get the final response
    if run.status == 'completed':
      print(f"[CS-Assist] Run {run.id} completed")
      messages = client.beta.threads.messages.list(
          thread_id=chat_thread.id
      )
      # Loop through messages and print content based on role
      for msg in messages.data:
        if msg.run_id == run.id:
          role = msg.role
          content = msg.content[0].text.value
          #print(f"{role.capitalize()}: {content}")
          yield content
        #Execution completed - you can come out of the function to service the next user request
      break   
    
    elif run.status == 'requires_action':
      print(f"[CS-Assist] Run {run.id} requires action")
      required_actions = json.loads(run.required_action.submit_tool_outputs.model_dump_json())
      #print(f"[CS-Assist] requires action -> {required_actions} {type(required_actions)}")
      tool_outputs = []
      for action in required_actions['tool_calls']:
        func_name = action['function']['name']
        arguments = json.loads(action['function']['arguments'])

        if func_name == "get_customer_usage_data_for_specific_inlet":
          print(f"[CS-Assist] Invoking get_customer_usage_data_for_specific_inlet() with arguments {arguments}")
          output = get_customer_usage_data_for_specific_inlet(arguments['customer_email'], arguments['date'], arguments['inlet'])
          tool_outputs.append({
            "tool_call_id" : action["id"],
            "output" : output
          })
        elif func_name == "analyse_data_anomaly":
          print(f"[CS-Assist] Invoking analyse_data_anomaly() with arguments {arguments}")
          output = analyse_data_anomaly(arguments['data'])
          tool_outputs.append({
            "tool_call_id" : action["id"],
            "output" : output
          })
        elif func_name == "generate_error_pdf_report":
          print(f"[CS-Assist] Invoking generate_error_pdf_report() with arguments {arguments}")
          output = analyse_data_anomaly(arguments['anomaly_data'])
          tool_outputs.append({
            "tool_call_id" : action["id"],
            "output" : output
          })
        elif func_name == "generate_clear_pdf_report":
          print(f"[CS-Assist] Invoking generate_clear_pdf_report() with arguments {arguments}")
          output = analyse_data_anomaly(arguments['clean_data'])
          tool_outputs.append({
            "tool_call_id" : action["id"],
            "output" : output
          })          
        else:
          raise ValueError(f'Unknown function {func_name}')

      print(f'[CS-Assist] Submitting outputs back to cs assistant')
      client.beta.threads.runs.submit_tool_outputs(
        thread_id=chat_thread.id,
        run_id=run.id,
        tool_outputs=tool_outputs
      )        

    elif run.status == 'failed':
      yield 'Error in handling your request. Please try again.'
      break

    else:
      print(f"[CS-Assist] Waiting for assistant to process. Current run status is {run.status}")
      time.sleep(3)

# #ask_cs_assistant("Please get data for customer vijay@wegot.in for the date Jun/24/2021 for MBR inlet. If data is available please check the data for any anomalies as well. If there is no issue then generate a report if there is an error then too generate an error report.")
# ask_cs_assistant("Please check if there is any anomaly in this data 100,500, 800");
# while True:
#   user_msg = input("[CS-Assist] Anything else you would like me to do? (Type exit at anytime to quit the service) -> ")
#   if user_msg == 'exit':
#     exit()
#   else:
#     ask_cs_assistant(user_msg)

import gradio as gr
demo = gr.ChatInterface(ask_cs_assistant,
                        title="CSA Customer Support Advisor",
                        description="I am a customer support advisor. I can help answer questions related to customer data and any anomalies they may contain. I can also help you reconcile the date if need be. I can run mathematical evaluations on data and give you insights on data.",
                        theme="soft",
                        examples=["Can you check user1@csa.domain's data for March 4th 2023?", "Are there any anomalies for user1@csa.domain's data for Apr/1/2021?"],
                        retry_btn=None,
                        undo_btn=None,
                        clear_btn=None).queue()

if __name__ == "__main__":
    demo.launch()    