#!/bin/bash

# Configure deployment environment
echo "Setting up production environment..."
npm install --production
npx create-react-app my-app --use-npm
cd my-app
npm run build
aws s3 cp build/ s3://my-bucket/user-feedback-system/ --recursive