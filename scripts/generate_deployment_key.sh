#!/bin/bash
# Script to generate an OpenSSH format key for GitHub Actions

# Generate a fresh ED25519 key (matches what's on your server)
ssh-keygen -t ed25519 -f deployment_key -N "" -C "github-actions-deploy"

echo ""
echo "========== PUBLIC KEY - ADD TO SERVER =========="
echo "Run this command on your server:"
echo ""
echo "echo '$(cat deployment_key.pub)' >> ~/.ssh/authorized_keys"
echo ""
echo "========== PRIVATE KEY - ADD TO GITHUB =========="
echo "Copy everything below this line and add it as the DEPLOYMENT_PRIVATE_KEY secret in GitHub:"
echo ""
cat deployment_key
echo ""
echo "========== VERIFICATION =========="
echo ""
echo "Key type: $(ssh-keygen -l -f deployment_key)"
