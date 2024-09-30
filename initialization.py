import os
# from langchain.llms import VertexAI
# from langchain_community.llms import VertexAI
from langchain_google_vertexai import VertexAI
from google.cloud import secretmanager

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