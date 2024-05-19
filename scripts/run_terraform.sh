#!/usr/bin/env bash
export TF_INPUT=0

if [ -f scripts/local.env ]; then
  echo "-- LOADED Local Environment Variables"
  . scripts/local.env
else
  echo "-- EXPECTING Environment Variables "
fi

terraform -chdir=deployment/cloud/aws plan