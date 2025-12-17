#!/bin/bash
# Script to install dependencies in conda nlp environment and run the motif extraction

echo "Activating conda nlp environment and installing dependencies..."

# Install pdfplumber in conda nlp environment
conda run -n nlp pip install pdfplumber

# Run the extraction script
echo "Running motif extraction from PDF..."
conda run -n nlp python3 scripts/extract_motifs_from_pdf.py
