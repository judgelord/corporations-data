#!/bin/bash

# Installation script for corporations-data project dependencies
# Run this script to install all required Python packages

echo "Installing Python packages from requirements.txt..."
pip install -r requirements.txt

echo ""
echo "Downloading NLTK stopwords data..."
python3 -c "import nltk; nltk.download('stopwords'); nltk.download('punkt')"

echo ""
echo "Downloading spaCy language model (en_core_web_lg)..."
echo "Note: This is a large download (~560MB)"
python3 -m spacy download en_core_web_lg

echo ""
echo "Installation complete!"
echo ""
echo "If you encounter any errors with specific packages, try installing them individually:"
echo "  - For pyxdameraulevenshtein issues: pip install pyxdameraulevenshtein"
echo "  - For apsw issues: pip install apsw"
echo "  - For pyreadr issues (requires gcc): brew install gcc && pip install pyreadr"
