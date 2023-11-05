# https://cloud.google.com/sdk/gcloud/reference/run/deploy
export GOOGLE_CLOUD_PROJECT=landing-zone-demo-341118
gcloud config set project $GOOGLE_CLOUD_PROJECT
export SERVICE_NAME=prompt-playground
export ARTIFACT_REGISTRY_NAME=prompt-playground
export REGION=europe-west4
export SERVICE_ACCOUNT_EMAIL=experts-hub-demo@landing-zone-demo-341118.iam.gserviceaccount.com

# Artifact Registry
gcloud builds submit --tag $REGION-docker.pkg.dev/$GOOGLE_CLOUD_PROJECT/$ARTIFACT_REGISTRY_NAME/$SERVICE_NAME:latest

gcloud run deploy $SERVICE_NAME \
--image $REGION-docker.pkg.dev/$GOOGLE_CLOUD_PROJECT/$ARTIFACT_REGISTRY_NAME/$SERVICE_NAME:latest \
--platform managed \
--allow-unauthenticated \
--region=$REGION \
--ingress=internal-and-cloud-load-balancing \
--min-instances=0 \
--concurrency=20 \
--service-account=$SERVICE_ACCOUNT_EMAIL \
--execution-environment=gen2    \
--cpu-boost \
--cpu=4 \
--memory=8Gi \
# --update-env-vars PROJECT_ID="landing-zone-demo-341118" \

