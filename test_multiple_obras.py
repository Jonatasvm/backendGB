#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de teste para validar a funcionalidade de múltiplas obras
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_multiple_obras():
    """Testa criação e listagem de lançamento com múltiplas obras"""
    
    print("=" * 60)
    print("TESTE: Lançamento com Múltiplas Obras")
    print("=" * 60)
    
    # Dados para criar um lançamento múltiplo
    payload = {
        "data_lancamento": "2025-01-03",
        "solicitante": "joao",
        "titular": "titular_teste",
        "referente": "Referente Teste",
        "valor": 1000.00,  # Valor total
        "obra": 1,  # Obra principal
        "data_pagamento": "2025-01-15",
        "forma_pagamento": "transfer",
        "cpf_cnpj": "12345678901234",
        "chave_pix": "",
        "data_competencia": "2025-01-31",
        "observacao": "Lançamento teste com múltiplas obras",
        "multiplos_lancamentos": 1,
        "obras_adicionais": [
            {"obra_id": 2, "valor": 400.0},
            {"obra_id": 3, "valor": 600.0}
        ]
    }
    
    print("\n1. Criando lançamento com múltiplas obras...")
    print(json.dumps(payload, indent=2, default=str))
    
    try:
        response = requests.post(
            f"{BASE_URL}/formulario",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\nStatus: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            result = response.json()
            print("✅ Lançamento criado com sucesso!")
            
            # Aguardar um pouco e depois listar
            print("\n2. Listando lançamentos...")
            response = requests.get(f"{BASE_URL}/formulario")
            
            if response.status_code == 200:
                formularios = response.json()
                
                # Procurar pelo lançamento criado
                multi_launches = [f for f in formularios if f.get("multiplos_lancamentos") == 1]
                
                if multi_launches:
                    print(f"\n✅ Encontrados {len(multi_launches)} lançamento(s) múltiplo(s)")
                    
                    for launch in multi_launches:
                        print(f"\n   ID: {launch.get('id')}")
                        print(f"   Valor: R$ {launch.get('valor', 0):.2f}")
                        print(f"   Obra: {launch.get('obra')}")
                        print(f"   Grupo: {launch.get('grupo_lancamento', 'SEM GRUPO')}")
                        
                        if launch.get("obras_relacionadas"):
                            print(f"   Obras Relacionadas: {len(launch.get('obras_relacionadas', []))}")
                            for obra in launch.get("obras_relacionadas", []):
                                print(f"     - Obra {obra.get('obra')}: R$ {obra.get('valor', 0):.2f}")
                            
                            # Calcular total
                            total = float(launch.get('valor', 0))
                            for obra in launch.get("obras_relacionadas", []):
                                total += float(obra.get('valor', 0))
                            print(f"   TOTAL: R$ {total:.2f}")
                        else:
                            print("   ⚠️ Nenhuma obra relacionada encontrada")
                else:
                    print("❌ Nenhum lançamento múltiplo encontrado")
            else:
                print(f"❌ Erro ao listar: {response.status_code}")
        else:
            print("❌ Erro ao criar lançamento")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

if __name__ == "__main__":
    test_multiple_obras()
