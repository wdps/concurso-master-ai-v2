import os
import sqlite3
from flask import Flask, render_template, jsonify, request, send_from_directory
import google.generativeai as genai
from datetime import datetime
import logging
import json

app = Flask(__name__)

# [TODO O SEU CÓDIGO ORIGINAL AQUI - COPIAR MANUALMENTE SE PRECISAR]

# Configuração para produção
PORT = int(os.environ.get('PORT', 5001))
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=DEBUG)
