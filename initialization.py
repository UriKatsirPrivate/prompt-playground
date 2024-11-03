import os
# from langchain.llms import VertexAI
# from langchain_community.llms import VertexAI
from langchain_google_vertexai import VertexAI
from google.cloud import secretmanager

import vertexai.preview.generative_models as generative_models

import vertexai
from vertexai.preview.prompts import Prompt
from vertexai.preview.generative_models import (
    GenerationConfig,
    GenerativeModel,
    HarmCategory,
    HarmBlockThreshold,
    Part,
    Tool,
)

# Initialize LLM
def initialize_llm(project_id,region,model_name,max_output_tokens,temperature,top_p):
    
    # Initialize VertexAI and set up the LLM
    return VertexAI(
        project=project_id,
        location=region,
        model_name=model_name,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        top_p=top_p,
        # top_k=top_k,
        verbose=True,
    )

def initialize_llm_vertex(project_id,region,model_name,max_output_tokens,temperature,top_p):
    
    vertexai.init(project=project_id, location=region)

    generation_config = GenerationConfig(temperature=temperature,
                                     top_p=top_p,
                                     max_output_tokens=max_output_tokens,)
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.OFF,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.OFF,
    }

    model = GenerativeModel(model_name=model_name,generation_config=generation_config,safety_settings=safety_settings)
    return model,generation_config,safety_settings






def get_from_secrets_manager(secret_name,gcp_project):
    # if langsmith_key:
    #     return langsmith_key

    # print("token")
    client = secretmanager.SecretManagerServiceClient()

    # name = f"projects/{PROJECT_ID}/secrets/langchain-api-key/versions/1"
    name = f"projects/{gcp_project}/secrets/{secret_name}/versions/1"

    # Access the secret version.
    response = client.access_secret_version(request={"name": name})

    # Extract the payload.
    payload = response.payload.data.decode("UTF-8")

    return payload