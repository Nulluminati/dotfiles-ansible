#!/bin/bash

fastapi_url="https://fastapi-dls.local.kift.dev/-/client-token"

# Check if nvidia-smi is available
if ! command -v nvidia-smi &> /dev/null
then
  echo "nvidia-smi not found, exiting"
  exit 1
fi

# Check for expired license
nvidia-smi -q | grep "License Status" | grep -q "Expired"

if [ $? -eq 0 ]; then
  echo "NVIDIA License Expired, attempting renewal"
  curl -L -X GET \
    $fastapi_url -o \
    /etc/nvidia/ClientConfigToken/client_configuration_token_$(date '+%d-%m-%Y-%H-%M-%S').tok
  systemctl restart nvidia-gridd
else
  echo "NVIDIA License is valid"
fi
