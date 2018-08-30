echo "Removing ~/.antigen"
rm -rf ~/.antigen

echo "Starting to install antigen into ~/.antigen"
echo ""
curl -L git.io/antigen > antigen.zsh
echo ""
echo "antigen installed"