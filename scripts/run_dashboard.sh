#!/bin/bash
cd "$(dirname "$0")"/.. 
source venv/bin/activate
streamlit run scripts/06_dashboard.py
