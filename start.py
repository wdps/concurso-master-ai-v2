#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script Python alternativo para inicialização
"""

import os
import subprocess
import sys

print("🚀 CONCURSOIA - Script de Inicialização Python")
print(f"📊 PORT: {os.environ.get('PORT', '5001')}")

# Executar o app.py
os.execvp("python", ["python", "app.py"])
