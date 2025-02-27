#!/bin/bash
# This script helps set up a deployment key for GitHub Actions

# Generate a new SSH key pair
ssh-keygen -t rsa -b 4096 -f deploy_key -N ""

# Display the public key to add to the server
echo "========== PUBLIC KEY (add to server's authorized_keys) =========="
cat deploy_key.pub
echo ""
echo "Run this on your server:"
echo "echo '$(cat deploy_key.pub)' >> ~/.ssh/authorized_keys"
echo ""

# Display the private key to add as a GitHub secret
echo "========== PRIVATE KEY (add as GitHub secret DEPLOY_KEY) =========="
cat deploy_key
echo ""
echo "Copy the above private key (including BEGIN and END lines)"
echo "and add it as a GitHub secret named DEPLOY_KEY"

# Clean up (optional)
echo ""
echo "After adding the keys to GitHub and your server, you can delete the local files:"
echo "rm deploy_key deploy_key.pub"
