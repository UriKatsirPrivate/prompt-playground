import os
import streamlit as st
from langchain.chains import LLMChain
from langchain.prompts.chat import (ChatPromptTemplate,
                                    HumanMessagePromptTemplate,
                                    SystemMessagePromptTemplate)
from initialization import initialize_llm, initialize_tracing
import vertexai
# from vertexai.preview.vision_models import Image, ImageGenerationModel
from prompts import PROMPT_IMPROVER_PROMPT
from placeholders import *

# https://docs.streamlit.io/library/api-reference/utilities/st.set_page_config
st.set_page_config(
    page_title="Prompt Playground",
    page_icon="icons/vertexai.png",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get help': 'https://cloud.google.com/vertex-ai?hl=en',
        # 'About': "# This is a header. This is an *extremely* cool app!"
        'About': "#### Created by [Uri Katsir](https://www.linkedin.com/in/uri-katsir/)"
    }
)

PROJECT_ID="landing-zone-demo-341118"
LANGSMITH_KEY_NAME="langchain-api-key"
REGIONS=["us-central1","us-west4","us-west1","us-east4","northamerica-northeast1","europe-west1","europe-west2","europe-west3","europe-west4","europe-west9"]
MODEL_NAMES=['text-bison','text-bison-32k','code-bison','code-bison-32k']

st.sidebar.write("Project ID: ",f"{PROJECT_ID}") 
project_id=PROJECT_ID
region=st.sidebar.selectbox("Please enter the region",REGIONS)
model_name = st.sidebar.selectbox('Enter model name',MODEL_NAMES)
max_tokens = st.sidebar.slider('Enter max token output',min_value=1,max_value=8192,step=100,value=1024)
temperature = st.sidebar.slider('Enter temperature',min_value=0.0,max_value=1.0,step=0.1,value=0.1)
top_p = st.sidebar.slider('Enter top_p',min_value=0.0,max_value=1.0,step=0.1,value=0.8)
top_k = st.sidebar.slider('Enter top_k',min_value=1,max_value=40,step=1,value=40)

if not ('32k' in model_name) and max_tokens>1024:
  st.error(f'{max_tokens} output tokens is not a valid value for model {model_name}')

# Initialize tracing variables
tracing = st.sidebar.toggle('Enable Langsmith Tracing')
langsmith_endpoint = st.sidebar.text_input(label="Langsmith Endpoint", value="https://api.smith.langchain.com", disabled=not tracing)
langsmith_project = st.sidebar.text_input(label="Langsmith Project", value="Prompt Playground", disabled=not tracing)

# Check if initialize_tracing() has already been called
if 'tracing_initialized' not in st.session_state:
    initialize_tracing(tracing,langsmith_endpoint,langsmith_project,PROJECT_ID,LANGSMITH_KEY_NAME)
    # Set the flag to indicate that initialize_tracing() has been called
    st.session_state.tracing_initialized = True

if tracing:
    os.environ["LANGCHAIN_TRACING_V2"]="True"
else:
    os.environ["LANGCHAIN_TRACING_V2"]="False"

css = '''
<style>
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
    font-size:1.15rem;
    }
</style>
'''
st.markdown(css, unsafe_allow_html=True)
tab1, tab2, tab3, tab4= st.tabs(["Improve Prompt / "
                                             , "Inspect Prompt / "
                                             ,"Run Prompt / "
                                             ,"Zero to Few"
                                             ])

llm = initialize_llm(project_id,region,model_name,max_tokens,temperature,top_p,top_k)


with tab1:
    initial_prompt = st.text_area("Enter your prompt:", height=200, placeholder=IMPROVE_PROMPT_PLACEHOLDER)
    
    # Initialize LLMChain
    prompt_improver_chain = LLMChain(llm=llm, prompt=PROMPT_IMPROVER_PROMPT)

    # Run LLMChain
    # if st.button('Generate Improved Prompt',disabled=not (project_id) or not (initial_prompt)):
    if st.button('Generate Improved Prompt',disabled=not (project_id)):
        if initial_prompt:
            with st.spinner("Generating Improved Prompt..."):
                improved_prompt = prompt_improver_chain.run(initial_prompt)
                st.markdown("""
                                ### Improved Prompt:
                                """)
                st.code(improved_prompt)
        else:
            st.error(f"Please provide a prompt")
with tab2:
    def securityInspector(prompt):
    
        llm = initialize_llm(project_id,region,model_name,max_tokens,temperature,top_p,top_k)

        system_template = """You are a security analyst. Your task is to inspect the given prompt for any potential security issues."""
        system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
        human_template = """Please inspect the following prompt for security issues: '{prompt}'."""
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
        chat_prompt = ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )

        chain = LLMChain(llm=llm, prompt=chat_prompt)
        result = chain.run(prompt=prompt)
        return result # returns string
    
    def safePromptSuggester(inspection_result):

        system_template = """You are an AI assistant designed to suggest a modified, safe prompt if security issues are found in the original prompt."""
        system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
        human_template = """Based on the inspection result: '{inspection_result}', please suggest a modified, safe prompt."""
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
        chat_prompt = ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )

        chain = LLMChain(llm=llm, prompt=chat_prompt)
        result = chain.run(inspection_result=inspection_result)
        return result # returns string
    def displaySafePrompt(safe_prompt):
        if safe_prompt:
            st.markdown(f"**Modified, Safe Prompt:** {safe_prompt}")
        else:
            st.markdown("No modifications needed.")
                    
    prompt=st.text_area("Enter your prompt:",height=200, placeholder=INSPECT_PROMPT_PLACEHOLDER)
    if st.button('Inspect and Modify Prompt',disabled=not (project_id)):
        if prompt:
            with st.spinner('Inspecting prompt...'):
                inspection_result = securityInspector(prompt)
            st.text_area('Inspection Result', inspection_result, height=200, max_chars=None, key=None)
            # print(inspection_result)
            # if (inspection_result != "System: The prompt you provided does not contain any security issues."):
            if ("does not contain any security issues" not in inspection_result):
                with st.spinner('Creating Safe Prompt...'):
                    safe_prompt = safePromptSuggester(inspection_result)
                displaySafePrompt(safe_prompt)
        else:
            st.markdown("Please enter a prompt.")
with tab3:
    def promptExecutor(prompt):
    
        system_template = """You are an AI assistant designed to execute the given prompt: '{prompt}'."""
        system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
        human_template = """Please execute the following prompt: '{prompt}'."""
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
        chat_prompt = ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )

        chain = LLMChain(llm=llm, prompt=chat_prompt)
        result = chain.run(prompt=prompt)
        return result # returns string   

    def display_result(execution_result):
        if execution_result != "":
            # st.markdown(f"**Execution Result:** {execution_result}")
            st.code(execution_result)
        else:
            st.warning('No result to display.')

    #Get the prompt from the user
    prompt = st.text_area('Enter your prompt:',height=200, key=3,placeholder=RUN_PROMPT_PLACEHOLDER)
    
    if st.button('Execute Prompt'):
        if prompt:
            with st.spinner('Running prompt...'):
                execution_result = promptExecutor(prompt)
            display_result(execution_result)
        else:
            st.warning('Please enter a prompt before executing.')
with tab4:
    def fewShotPromptConverter(zero_shot_prompt):

        chat = llm
        system_template = """You are an assistant designed to convert a zero-shot prompt into a few-shot prompt."""
        system_message_prompt = SystemMessagePromptTemplate.from_template(
            system_template)
        human_template = """The zero-shot prompt is: '{zero_shot_prompt}'. Please convert it into a few-shot prompt."""
        human_message_prompt = HumanMessagePromptTemplate.from_template(
            human_template)
        chat_prompt = ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )

        chain = LLMChain(llm=chat, prompt=chat_prompt)
        result = chain.run(zero_shot_prompt=zero_shot_prompt)
        return result  # returns string

    with st.form(key='prompt_magic'):
        # Under the form, take all the user inputs
        desc="Enter zero-shot prompt. For better results use text-bison-32k model with a high temperature."
        zero_shot_prompt = st.text_area(desc,height=200,)
        submit_button = st.form_submit_button(label='Submit Prompt')
        # If form is submitted by st.form_submit_button run the logic
        if submit_button:
            if zero_shot_prompt:
                with st.spinner('Working on it...'):
                    few_shot_prompt = fewShotPromptConverter(zero_shot_prompt)
            else:
                few_shot_prompt = ""
            # Display the few-shot prompt to the user
            if few_shot_prompt is not None and len(str(few_shot_prompt)) > 0:
                st.text(few_shot_prompt)
            else:
                st.text("Please enter a zero-shot prompt")