#!/usr/bin/env python3
"""
Script de teste para validar o fluxo de dados entre Backend e Frontend
para a exportação de Obras no Dashboard
"""

import requests
import json
from typing import List, Dict, Any

# Configurações
API_URL = "http://91.98.132.210:5631"
ENDPOINTS = {
    "obras": f"{API_URL}/obras",
    "formularios": f"{API_URL}/formulario",
}

class DashboardDataValidator:
    """Valida o fluxo de dados do Dashboard"""
    
    def __init__(self, api_url: str):
        self.api_url = api_url
        self.obras: List[Dict[str, Any]] = []
        self.formularios: List[Dict[str, Any]] = []
        self.issues: List[str] = []
        self.warnings: List[str] = []
        self.successes: List[str] = []
    
    def fetch_obras(self) -> bool:
        """Busca a lista de obras"""
        try:
            response = requests.get(f"{self.api_url}/obras")
            if response.status_code == 200:
                self.obras = response.json()
                self.successes.append(f"✅ Obras carregadas: {len(self.obras)} registros")
                self._print_obras()
                return True
            else:
                self.issues.append(f"❌ Erro ao buscar obras: Status {response.status_code}")
                return False
        except Exception as e:
            self.issues.append(f"❌ Erro na requisição de obras: {str(e)}")
            return False
    
    def fetch_formularios(self) -> bool:
        """Busca a lista de formulários"""
        try:
            response = requests.get(f"{self.api_url}/formulario")
            if response.status_code == 200:
                self.formularios = response.json()
                self.successes.append(f"✅ Formulários carregados: {len(self.formularios)} registros")
                return True
            else:
                self.issues.append(f"❌ Erro ao buscar formulários: Status {response.status_code}")
                return False
        except Exception as e:
            self.issues.append(f"❌ Erro na requisição de formulários: {str(e)}")
            return False
    
    def validate_obra_mapping(self) -> None:
        """Valida o mapeamento entre formulários e obras"""
        if not self.formularios:
            self.warnings.append("⚠️ Nenhum formulário carregado para validar")
            return
        
        if not self.obras:
            self.issues.append("❌ Nenhuma obra carregada para validar mapeamento")
            return
        
        obra_ids = {int(o['id']) for o in self.obras}
        
        for form in self.formularios[:10]:  # Valida primeiro 10
            form_obra_id = form.get('obra')
            
            if form_obra_id is None:
                self.warnings.append(f"⚠️ Formulário {form['id']}: obra não preenchida")
                continue
            
            form_obra_id_int = int(form_obra_id) if isinstance(form_obra_id, str) else form_obra_id
            
            if form_obra_id_int in obra_ids:
                # Busca o nome da obra
                obra = next(o for o in self.obras if int(o['id']) == form_obra_id_int)
                self.successes.append(
                    f"✅ Formulário {form['id']}: obra '{obra['nome']}' encontrada (ID: {form_obra_id_int})"
                )
            else:
                self.issues.append(
                    f"❌ Formulário {form['id']}: obra ID {form_obra_id_int} NÃO encontrada"
                )
    
    def _print_obras(self) -> None:
        """Imprime as obras carregadas"""
        print("\n📋 OBRAS DISPONÍVEIS:")
        for obra in self.obras:
            print(f"  - ID: {obra['id']}, Nome: {obra['nome']}, Quem Paga: {obra.get('quem_paga', 'N/A')}")
    
    def print_report(self) -> None:
        """Imprime relatório completo"""
        print("\n" + "="*80)
        print("📊 RELATÓRIO DE VALIDAÇÃO DO DASHBOARD")
        print("="*80)
        
        if self.successes:
            print("\n✅ SUCESSOS:")
            for msg in self.successes:
                print(f"  {msg}")
        
        if self.warnings:
            print("\n⚠️ AVISOS:")
            for msg in self.warnings:
                print(f"  {msg}")
        
        if self.issues:
            print("\n❌ PROBLEMAS:")
            for msg in self.issues:
                print(f"  {msg}")
        
        print("\n" + "="*80)
        
        # Resumo
        if not self.issues:
            print("✅ TUDO OK! O dashboard deve funcionar corretamente.")
        else:
            print(f"❌ {len(self.issues)} problemas encontrados. Verifique os detalhes acima.")
        
        print("="*80 + "\n")
    
    def run_validation(self) -> bool:
        """Executa todas as validações"""
        print("\n🔍 Iniciando validação do Dashboard...")
        print(f"   API URL: {self.api_url}\n")
        
        # Etapa 1: Carregar dados
        print("📥 Etapa 1: Carregando dados...")
        self.fetch_obras()
        self.fetch_formularios()
        
        # Etapa 2: Validar mapeamento
        print("\n🔗 Etapa 2: Validando mapeamento de obras...")
        self.validate_obra_mapping()
        
        # Etapa 3: Exibir relatório
        print("\n📈 Etapa 3: Exibindo relatório...\n")
        self.print_report()
        
        return len(self.issues) == 0


def main():
    """Função principal"""
    validator = DashboardDataValidator(API_URL)
    success = validator.run_validation()
    
    # Retornar código de saída apropriado
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
