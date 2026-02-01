#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para testar múltiplos lançamentos - DEBUG
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_multiple_obras():
    """Testa criação de lançamento com múltiplas obras"""
    
    print("\n" + "="*70)
    print("TESTE: Lançamento com Múltiplas Obras")
    print("="*70)
    
    # Dados para criar um lançamento múltiplo
    payload = {
        "data_lancamento": "2025-01-31",
        "solicitante": "joao",
        "titular": "titular_teste",
        "referente": "Teste Múltiplas Obras",
        "valor": 600.0,  # Valor total
        "obra": 1,  # Obra principal
        "data_pagamento": "2025-02-15",
        "forma_pagamento": "transfer",
        "cpf_cnpj": "12345678901234",
        "chave_pix": "",
        "data_competencia": "2025-02-28",
        "observacao": "Teste",
        "multiplos_lancamentos": 1,
        "obras_adicionais": [
            {"obra_id": 1, "valor": 400.0},
            {"obra_id": 2, "valor": 200.0}
        ]
    }
    
    print("\nPayload sendo enviado:")
    print(json.dumps(payload, indent=2))
    
    print("\n1. Enviando POST /formulario...")
    try:
        response = requests.post(
            f"{BASE_URL}/formulario",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\nStatus: {response.status_code}")
        print(f"Response: {response.text}\n")
        
        if response.status_code == 201:
            print("✅ Lançamento criado com sucesso!\n")
            
            # Aguardar um pouco e depois listar
            print("2. Listando lançamentos...")
            response = requests.get(f"{BASE_URL}/formulario")
            
            if response.status_code == 200:
                formularios = response.json()
                print(f"Total de lançamentos: {len(formularios)}\n")
                
                # Procurar pelo lançamento criado (últimas entradas)
                for form in formularios[:5]:  # Mostrar os 5 últimos
                    print(f"  ID: {form.get('id')}")
                    print(f"  Obra: {form.get('obra')}")
                    print(f"  Valor: R$ {form.get('valor', 0):.2f}")
                    print(f"  Grupo: {form.get('grupo_lancamento', 'SEM GRUPO')}")
                    
                    if form.get("obras_relacionadas"):
                        print(f"  Obras Relacionadas: {len(form.get('obras_relacionadas', []))}")
                        for obra in form.get("obras_relacionadas", []):
                            print(f"    - Obra {obra.get('obra')}: R$ {obra.get('valor', 0):.2f}")
                    print()
            else:
                print(f"❌ Erro ao listar: {response.status_code}")
        else:
            print(f"❌ Erro: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_multiple_obras()
