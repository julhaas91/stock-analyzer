#!/bin/bash
set -e

# //////////////////////////////////////////////////////////////////////////////
# START tasks

source .env

print_env_variables() {
  echo "Printing all environment variables:"
  printenv
}

run_frontend() {
  uv run streamlit run src/app.py
}

run_backend() {
  uv run python3 src/main.py
}

reset_venv_local() {
  sudo rm -rf .venv
  echo "... deleted old virtual environment ..."
  python3 -m venv .venv
  echo "... created new virtual environment ..."
  source .venv/bin/activate
  echo "... activated new virtual environment ..."
  uv sync --frozen
  source .env
}

deploy() {
  echo "... fetching project variables ..."
  NAME="$(uv run python3 -c "import toml; print(toml.load('pyproject.toml')['project']['name'])")"
  VERSION="$(uv run python3 -c "import toml; print(toml.load('pyproject.toml')['project']['version'])")"
  DATETIME=$(uv run date +"%y-%m-%d-%H%M%S")
  IMAGE_TAG="${SERVICE_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/docker/${NAME}:${VERSION}-${DATETIME}"

  echo "... building docker image for service ..."
  uv run gcloud auth configure-docker "${SERVICE_REGION}-docker.pkg.dev"
  uv run docker build --platform linux/amd64 -f "./Dockerfile.app" -t "${IMAGE_TAG}" .

  echo "... pushing image to artifact registry ..."
  uv run docker push "${IMAGE_TAG}"

  echo "... deploying image to cloud run ..."
  uv run gcloud run deploy "${NAME}" \
    --project "${GCP_PROJECT_ID}" \
    --image "${IMAGE_TAG}" \
    --platform managed \
    --timeout "${SERVICE_TIMEOUT}" \
    --memory "${SERVICE_MEMORY}" \
    --service-account "${CLOUD_RUN_SERVICE_ACCOUNT}" \
    --region "${SERVICE_REGION}"

}

release() {
  CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
  if [ "$CURRENT_BRANCH" = "main" ]; then
    DATETIME=$(date +"%Y%d%m-%H%M%S")
    git tag -am "release(trigger)-$DATETIME" "release(trigger)-$DATETIME" -f && git push origin --tags -f
  else
    echo "You need to checkout the 'main' branch to run a release."
    echo "Current branch is: $CURRENT_BRANCH"
  fi
}

create_identity_token() {
  uv run gcloud auth print-identity-token
}

authenticate() {
  uv run gcloud auth application-default login
}

# END tasks
# //////////////////////////////////////////////////////////////////////////////

help() {
  echo "Usage: ./Taskfile.sh [task]"
  echo
  echo "Available tasks:"
  echo "  print_env_variables           Print all environment variables."
  echo "  run_application               Run the application locally."
  echo "  reset_venv_local              Reset the local virtual environment."
  echo "  deploy                        Deploy application to Google Cloud Run."
  echo "  release                       Create a new release tag and push to origin."
  echo "  authenticate                  Authenticate to Google Cloud."
  echo "  create_identity_token         Create an identity token for external request authentication."
  echo
  echo "If no task is provided, the default is to run the application."
}

# Check if the provided argument matches any of the functions
if declare -f "$1" > /dev/null; then
  "$@"  # If the function exists, run it with any additional arguments
else
  echo "Error: Unknown task '$1'"
  echo
  help  # Show help if the task is not recognized
fi