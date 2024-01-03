import os
import streamlit as st
from langchain.chains import LLMChain
from langchain.prompts.chat import (ChatPromptTemplate,
                                    HumanMessagePromptTemplate,
                                    SystemMessagePromptTemplate)
from initialization import initialize_llm, initialize_tracing
import vertexai
from vertexai.preview.vision_models import Image, ImageGenerationModel
from langchain import hub
from prompts import PROMPT_IMPROVER_PROMPT
from placeholders import *
from system_prompts import *
import requests

# https://docs.streamlit.io/library/api-reference/utilities/st.set_page_config
st.set_page_config(
    page_title="The Prompt Playground",
    page_icon="icons/vertexai.png",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get help': 'https://github.com/UriKatsirPrivate/prompt-playground',
        'About': "#### Created by [Uri Katsir](https://www.linkedin.com/in/uri-katsir/)"
    }
)

# PROJECT_ID=st.sidebar.text_input(label="Project ID",value="Your Project ID")
LANGSMITH_KEY_NAME="langchain-api-key"
REGIONS=["us-central1","europe-west4","us-west4","us-west1","us-east4","northamerica-northeast1","europe-west1","europe-west2","europe-west3","europe-west9"]
MODEL_NAMES=['gemini-pro','text-bison-32k','text-bison','code-bison','code-bison-32k']

def get_project_id():
    metadata_server_url = "http://metadata.google.internal/computeMetadata/v1/"
    metadata_flavor = {'Metadata-Flavor': 'Google'}
    try:
        response = requests.get(metadata_server_url + "project/project-id", headers=metadata_flavor)
        if response.status_code == 200:
            project_id = response.text
            return project_id
        else:
            print(f"Failed to retrieve project ID. Status code: {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"Error: {e}")
        return None

PROJECT_ID=st.sidebar.text_input(label="Project ID",value="Your Project ID")
if PROJECT_ID=="" or PROJECT_ID=="Your Project ID":
    # print("getting project id")
    PROJECT_ID=get_project_id()
    
st.sidebar.write("Project ID: ",f"{PROJECT_ID}") 
project_id=PROJECT_ID
region=st.sidebar.selectbox("Please enter the region",REGIONS)
model_name = st.sidebar.selectbox('Enter model name',MODEL_NAMES)
max_tokens = st.sidebar.slider('Enter max token output',min_value=1,max_value=8192,step=100,value=8192)
temperature = st.sidebar.slider('Enter temperature',min_value=0.0,max_value=1.0,step=0.1,value=0.1)
top_p = st.sidebar.slider('Enter top_p',min_value=0.0,max_value=1.0,step=0.1,value=0.8)
top_k = st.sidebar.slider('Enter top_k',min_value=1,max_value=40,step=1,value=40)

if not ('32k' in model_name or 'gemini' in model_name) and max_tokens>1024:
  st.error(f'{max_tokens} output tokens is not a valid value for model {model_name}')

# Initialize tracing variables
tracing = st.sidebar.toggle('Enable Langsmith Tracing',disabled=True)
langsmith_endpoint = st.sidebar.text_input(label="Langsmith Endpoint", value="https://api.smith.langchain.com", disabled=not tracing)
langsmith_project = st.sidebar.text_input(label="Langsmith Project", value="prompt-playground", disabled=not tracing)

# Check if initialize_tracing() has already been called
if 'tracing_initialized' not in st.session_state and tracing:
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
tab1, tab2, tab3, tab4, tab5, tab6,tab7,tab8,tab9= st.tabs(["Fine-Tune Prompt / "
                                             , "Analysis & Enhancement /"          
                                             , "Inspect Prompt / "
                                             ,"Run Prompt / "
                                             ,"Zero to Few / "
                                             ,"Chain of Thought / "
                                             ,"Images / "
                                             ,"Decomposition / "
                                             ,"D.A.R.E Prompting"
                                             ])

llm = initialize_llm(project_id,region,model_name,max_tokens,temperature,top_p,top_k)


with tab1:
    # https://docs.smith.langchain.com/hub/dev-setup
    def supercharge_prompt(query):
        prompt = hub.pull("cajukev/prompt_practice_supercharge")
        runnable = prompt | llm
        result = runnable.invoke({
                        "goal": "improve the prompt",
                        "prompt": query,
                    })
        return result # returns string
    
    def refine_prompt(query):
        prompt = hub.pull("feisky/prompt-refine")
        runnable = prompt | llm
        result = runnable.invoke({
                        "task": query,
                        "lazy_prompt": query,
                    })
        return result # returns string
    
    def make_prompt(query):
        prompt = hub.pull("hardkothari/prompt-maker")
        runnable = prompt | llm
        result = runnable.invoke({
                        "task": query,
                        "lazy_prompt": query,
                    })
        return result # returns string

    
    initial_prompt = st.text_area("Enter your prompt:", height=200, placeholder=IMPROVE_PROMPT_PLACEHOLDER)
    
    # Initialize LLMChain
    prompt_improver_chain = LLMChain(llm=llm, prompt=PROMPT_IMPROVER_PROMPT)

    # Run LLMChain
    if st.button('Fine-Tune Prompt',disabled=not (project_id)  or project_id=="Your Project ID"):
    
        if initial_prompt:
            
            with st.spinner("Generating Prompts..."):
                col1, col2= st.columns(2,gap="medium")
                with col1:
                    improved_prompt = prompt_improver_chain.run(initial_prompt)
                    st.text_area(label="Fine-Tuned Prompt:",value=improved_prompt, height=250, max_chars=None, key=None)

                    supercharged_prompt=(supercharge_prompt(initial_prompt))
                    st.text_area("Supercharged Prompt:",supercharged_prompt, height=250, max_chars=None, key=None) 

                with col2:
                    refined_prompt=(refine_prompt(initial_prompt))
                    # st.markdown(""" ### Refined Prompt:""")
                    st.text_area("Refined Prompt:",refined_prompt, height=250, max_chars=None, key=None)    

                    made_prompt=(make_prompt(initial_prompt))
                    st.text_area("Prompt Maker:",made_prompt, height=250, max_chars=None, key=None) 
        else:
            st.error(f"Please provide a prompt")
with tab2:
    def analysis_and_enhancement(prompt):
    
        hub_prompt = hub.pull("collinsomniac/ultimate_nlp_taskprompt-inspired_by_hardkothari")

        task="improve the prompt"
        lazy_prompt= prompt

        runnable = hub_prompt | llm
        result = runnable.invoke({
                        "task": task,
                        "lazy_prompt": lazy_prompt,
                    })
        
        return result # returns string   

    def display_result(execution_result):
        if execution_result != "":
            st.text_area(label="Execution Result:",value=execution_result,height=400, key=50)
            # st.markdown(f"**Execution Result:** {execution_result}")
            # st.code(execution_result)

        else:
            st.warning('No result to display.')

    #Get the prompt from the user
    prompt = st.text_area('Enter your prompt:',height=200, key=33,placeholder="tweet about Israel")
    
    if st.button('Analysis & Enhancement',disabled=not (project_id)  or project_id=="Your Project ID"):
        if prompt:
            with st.spinner('Running prompt...'):
                execution_result = analysis_and_enhancement(prompt)
            display_result(execution_result)
        else:
            st.warning('Please enter a prompt before executing.')
with tab3:
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
    if st.button('Inspect and Modify Prompt',disabled=not (project_id)  or project_id=="Your Project ID"):
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
with tab4:
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
    
    if st.button('Execute Prompt',disabled=not (project_id)  or project_id=="Your Project ID"):
        if prompt:
            with st.spinner('Running prompt...'):
                execution_result = promptExecutor(prompt)
            display_result(execution_result)
        else:
            st.warning('Please enter a prompt before executing.')
with tab5:
    def fewShotPromptConverter(zero_shot_prompt):

        chat = llm
        system_template = """You are an assistant designed to convert a zero-shot prompt into a few-shot prompt."""
        system_message_prompt = SystemMessagePromptTemplate.from_template(
            system_template)
        human_template = """The zero-shot prompt is: '{zero_shot_prompt}'. Please convert it into a few-shot prompt.
                            Be as elaborate as possible. Make sure to include at least 3 examples.
                            """
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
        desc="Enter zero-shot prompt:"
        link="https://www.promptingguide.ai/techniques/fewshot"
        zero_shot_prompt = st.text_area(desc,height=200,help=link,placeholder=ZERO_SHOT_PROMPT_PLACEHOLDER)
        submit_button = st.form_submit_button(label='Submit Prompt',disabled=not (project_id)  or project_id=="Your Project ID")
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
with tab6:
    def cotPromptConverter(prompt):

        chat = llm
        system_template = """You are an assistant designed to convert a prompt into a chain of thought prompt."""
                            
                      
        system_message_prompt = SystemMessagePromptTemplate.from_template(
            system_template)
        human_template = """The prompt is: '{prompt}'. Please convert it into a chain of thought prompt.
        Always append 'Let's think step by step.' to the prompt.
        """
        human_message_prompt = HumanMessagePromptTemplate.from_template(
            human_template)
        chat_prompt = ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )

        chain = LLMChain(llm=chat, prompt=chat_prompt)
        result = chain.run(prompt=prompt)
        return result  # returns string

    with st.form(key='cot_prompt'):
        # Under the form, take all the user inputs
        link="https://www.promptingguide.ai/techniques/cot"
        desc="Enter prompt:"
        prompt = st.text_area(desc,height=200,help=link,placeholder=COT_PROMPT_PLACEHOLDER)
        submit_button = st.form_submit_button(label='Submit Prompt',disabled=not (project_id)  or project_id=="Your Project ID")
        # If form is submitted by st.form_submit_button run the logic
        if submit_button:
            if prompt:
                with st.spinner('Working on it...'):
                    cot_prompt = cotPromptConverter(prompt)
            else:
                cot_prompt = ""
            # Display the few-shot prompt to the user
            if prompt is not None and len(str(cot_prompt)) > 0:
                st.text(cot_prompt)
            else:
                st.text("Please enter a prompt")    
with tab7:
    def GenerateImagePrompt(description,number):
        
        system_template = GenerateImageSystemPrompt
        system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
        human_template = f"""Please generate {number} prompt(s) about: {description} ."""
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
        chat_prompt = ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )

        chain = LLMChain(llm=llm, prompt=chat_prompt)
        result = chain.run(module_string=description)
        # print (f" result is: {result}")
        return result # returns string
    
    def GenerateImage(description,num_of_images):
        try:
            vertexai.init(project=project_id, location=region)

            # model = ImageGenerationModel.from_pretrained(model_name)
            model = ImageGenerationModel.from_pretrained("imagegeneration@005")
            images = model.generate_images(
            prompt=description,
            # Optional:
            number_of_images=num_of_images,
            # seed=1,
            )
            return images
        except:
            ""
    def display_images(images):
        for image in images:
            image.save(location="./gen-img1.png", include_generation_parameters=True)
            st.image("./gen-img1.png",use_column_width="auto")
   
    link="https://cloud.google.com/vertex-ai/docs/generative-ai/image/img-gen-prompt-guide"
    desc="Write your prompt below, See help icon for a prompt guide: (Images will be generated using the Imagen 2 model)"
    description = st.text_area(desc,height=200,key=55,placeholder=GENERATE_IMAGES,help=link)
    # num_of_images=st.number_input("How many images to generate",min_value=1,max_value=8,value=4)
    
    col1, col2 = st.columns(2,gap="large")
    with col1:
        with st.form(key='prompt_magic10',clear_on_submit=False):
            num_of_prompts=st.number_input("How many prompts to generate",min_value=2,max_value=4,value=2)
            if st.form_submit_button('Generate Prompt(s)',disabled=not (project_id)  or project_id=="Your Project ID"):
                if description:
                    with st.spinner('Generating Prompt(s)...'):
                        improved_prompt = GenerateImagePrompt(description,num_of_prompts)
                    st.markdown(improved_prompt)
                else:
                    st.markdown("No prompts generated. Please enter a valid prompt.")        
    with col2:
        with st.form(key='prompt_magic1',clear_on_submit=False):                
        
            num_of_images=st.number_input("How many images to generate",min_value=1,max_value=8,value=4)
            if st.form_submit_button('Generate Image(s)',disabled=not (project_id)  or project_id=="Your Project ID"):
                if description:
                    with st.spinner('Generating Image(s)...'):
                        images = GenerateImage(description,num_of_images)
                        if images:
                            display_images(images)
                        else:
                           st.markdown("No images generated. Prompt was blocked.")     
                else:
                    st.markdown("No images generated. Please enter a valid prompt.")      
with tab8:
    def decomposition(query):
        
        # llm = initialize_llm(project_id,region,model_name,max_tokens,temperature,top_p,top_k)
        # https://docs.smith.langchain.com/hub/dev-setup
        prompt = hub.pull("smithing-gold/question-decomposition")

        runnable = prompt | llm
        result = runnable.invoke({"question": query})
        return result # returns string
        
    
    link="The general approach is to ask for self-contained questions to decompose the original user's query."                
    prompt=st.text_area("Enter your prompt:",height=200, placeholder=Decomposition_Prompt,help=link)
    if st.button('Decomposition',disabled=not (project_id)  or project_id=="Your Project ID"):
        if prompt:
            with st.spinner('decomposing...'):
                inspection_result = decomposition(prompt)
            st.text_area('Result', inspection_result, height=250, max_chars=None, key=None)
        else:
            st.markdown("Please enter a prompt.")
with tab9:
    def dare_it(query,vision,mission,context):
        
        # https://smith.langchain.com/hub/uri-katsir/dare-determine_appropriate_response?organizationId=78e845bf-d7e9-43c7-8c2d-d0decc426c62
        hub_prompt = hub.pull("uri-katsir/dare-determine_appropriate_response")

        
        runnable = hub_prompt | llm
        result = runnable.invoke({"vision": vision,"mission": mission,"context": context,"prompt": query})
        return result # returns string
        
    
    link="https://www.linkedin.com/posts/ram-seshadri-nyc-nj_how-do-you-reduce-hallucinations-ensure-activity-7085123540177285121-THrK/"
    vision_help="Enter your vision: See help icon for more information about the DARE prompting technique:"
    vision=st.text_input(vision_help ,placeholder="Marketing assistant",help=link)
    mission=st.text_input("Enter your mission:", placeholder="Help people plan marketing events",help="")
    context=st.text_area("Enter your context:",height=20, placeholder="You are a marketing assistant. Be as elaborate as makes sense",help="")
    prompt=st.text_area("Enter your prompt:",height=100, placeholder="Plan cloud run marketing workshop",help="")
    if st.button('D.A.R.E',disabled=not (project_id)  or project_id=="Your Project ID"):
        if prompt:
            with st.spinner('working on it...'):
                dare_result = dare_it(prompt,vision,mission,context)
            st.text_area('Result', dare_result, height=250, max_chars=None, key=None)
        else:
            st.markdown("Please enter a prompt.")            