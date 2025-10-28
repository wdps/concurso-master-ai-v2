import os
from flask import Flask, render_template, jsonify, request
import sqlite3
import json
import google.generativeai as genai
from datetime import datetime
import logging

app = Flask(__name__)

# Configuração para produção
PORT = int(os.environ.get('PORT', 5001))
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Sua configuração do Gemini e resto do código...
# [MANTER O RESTO DO SEU CÓDIGO AQUI]

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=DEBUG)
