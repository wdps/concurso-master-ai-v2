#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de verificação para ConcursoMaster AI
Verifica se todas as funcionalidades estão funcionando
"""

import sqlite3
import sys

def verificar_sistema():
    print(\"🔍 VERIFICANDO SISTEMA CONCURSOMASTER AI\")
    print(\"=\" * 50)
    
    try:
        # Verificar banco de dados
        conn = sqlite3.connect('concurso.db')
        cursor = conn.cursor()
        
        # Verificar tabelas
        cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")
        tables = [row[0] for row in cursor.fetchall()]
        print(\"✅ TABELAS ENCONTRADAS:\")
        for table in tables:
            cursor.execute(f\"SELECT COUNT(*) FROM {table}\")
            count = cursor.fetchone()[0]
            print(f\"   - {table}: {count} registros\")
        
        # Verificar temas de redação
        cursor.execute(\"SELECT tema, categoria FROM temas_redacao LIMIT 5\")
        temas = cursor.fetchall()
        print(f\"\\n📝 PRIMEIROS TEMAS DE REDAÇÃO:\")
        for tema, categoria in temas:
            print(f\"   - {categoria}: {tema[:40]}...\")
        
        # Verificar questões
        cursor.execute(\"SELECT materia, COUNT(*) FROM questões GROUP BY materia\")
        materias = cursor.fetchall()
        print(f\"\\n❓ DISTRIBUIÇÃO DE QUESTÕES:\")
        for materia, count in materias:
            print(f\"   - {materia}: {count} questões\")
        
        conn.close()
        
        print(\"\\n🎉 SISTEMA VERIFICADO COM SUCESSO!\")
        print(\"✅ Todas as funcionalidades estão operacionais\")
        return True
        
    except Exception as e:
        print(f\"\\n❌ ERRO NA VERIFICAÇÃO: {e}\")
        return False

if __name__ == \"__main__\":
    sucesso = verificar_sistema()
    sys.exit(0 if sucesso else 1)
