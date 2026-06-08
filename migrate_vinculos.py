#!/usr/bin/env python3
"""
Script de Migração: Converter grupo_lancamento para formulario_vinculos

Este script migra dados existentes da estrutura antiga (grupo_lancamento)
para a nova estrutura de vínculos (formulario_vinculos) com boas práticas.

Uso:
    python migrate_vinculos.py

"""

from db import get_connection
import sys
from datetime import datetime

def analisar_dados_atuais():
    """Analisar dados atuais da tabela formulario"""
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        print("\n" + "="*70)
        print("📊 ANÁLISE DOS DADOS ATUAIS")
        print("="*70)
        
        # Contar lançamentos com grupo_lancamento
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT grupo_lancamento) as grupos_unicos,
                SUM(CASE WHEN grupo_lancamento IS NOT NULL THEN 1 ELSE 0 END) as com_grupo,
                SUM(CASE WHEN multiplos_lancamentos = 1 THEN 1 ELSE 0 END) as multiplos_flag
            FROM formulario
        """)
        
        stats = cursor.fetchone()
        print(f"\n📋 Estatísticas Gerais:")
        print(f"   • Total de lançamentos: {stats['total']}")
        print(f"   • Com grupo_lancamento: {stats['com_grupo']} ({stats['com_grupo']/stats['total']*100:.1f}%)")
        print(f"   • Grupos únicos: {stats['grupos_unicos']}")
        print(f"   • Com multiplos_lancamentos=1: {stats['multiplos_flag']}")
        
        # Detalhar grupos
        cursor.execute("""
            SELECT 
                grupo_lancamento,
                COUNT(*) as total_lancamentos,
                SUM(valor) as valor_total,
                GROUP_CONCAT(id SEPARATOR ', ') as ids
            FROM formulario
            WHERE grupo_lancamento IS NOT NULL
            GROUP BY grupo_lancamento
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """)
        
        grupos = cursor.fetchall()
        print(f"\n🔗 Top 10 Grupos (por tamanho):")
        for i, grupo in enumerate(grupos, 1):
            print(f"   {i}. Grupo '{grupo['grupo_lancamento']}':")
            print(f"      - Lançamentos: {grupo['total_lancamentos']}")
            print(f"      - Valor total: R$ {grupo['valor_total']}")
            print(f"      - IDs: {grupo['ids']}")
        
        cursor.close()
        return stats
        
    except Exception as e:
        print(f"❌ Erro ao analisar dados: {e}")
        return None
    finally:
        conn.close()

def verificar_vinculos_existentes():
    """Verificar se já existem vínculos"""
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT COUNT(*) as total FROM formulario_vinculos")
        result = cursor.fetchone()
        total = result['total']
        
        print(f"\n⚠️  Vínculos existentes: {total}")
        
        if total > 0:
            cursor.execute("""
                SELECT 
                    tipo_vinculo,
                    COUNT(*) as total,
                    SUM(CASE WHEN ativo = 1 THEN 1 ELSE 0 END) as ativos
                FROM formulario_vinculos
                GROUP BY tipo_vinculo
            """)
            
            print("\n   Por tipo:")
            for row in cursor.fetchall():
                print(f"   • {row['tipo_vinculo']}: {row['total']} (ativos: {row['ativos']})")
        
        cursor.close()
        return total
        
    except Exception as e:
        print(f"❌ Erro ao verificar vínculos: {e}")
        return -1
    finally:
        conn.close()

def migrar_dados(simular=True):
    """
    Migrar dados de grupo_lancamento para formulario_vinculos
    
    Args:
        simular: Se True, apenas simula sem fazer alterações
    """
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        print("\n" + "="*70)
        if simular:
            print("🔍 SIMULAÇÃO DE MIGRAÇÃO (sem fazer alterações)")
        else:
            print("🚀 INICIANDO MIGRAÇÃO (alterações reais)")
        print("="*70)
        
        # 1. Buscar todos os grupos
        cursor.execute("""
            SELECT DISTINCT grupo_lancamento
            FROM formulario
            WHERE grupo_lancamento IS NOT NULL
            ORDER BY grupo_lancamento
        """)
        
        grupos = cursor.fetchall()
        print(f"\n📦 Total de grupos para migrar: {len(grupos)}")
        
        total_vinculos_criados = 0
        erros = []
        
        # 2. Para cada grupo, criar vínculos
        for idx, grupo in enumerate(grupos, 1):
            grupo_id = grupo['grupo_lancamento']
            
            # Buscar todos os lançamentos do grupo
            cursor.execute("""
                SELECT id, referente, valor
                FROM formulario
                WHERE grupo_lancamento = %s
                ORDER BY id ASC
            """, (grupo_id,))
            
            lancamentos = cursor.fetchall()
            num_lancamentos = len(lancamentos)
            
            print(f"\n   [{idx}/{len(grupos)}] Grupo '{grupo_id}' ({num_lancamentos} lançamentos)")
            
            # Vincular o primeiro a todos os outros
            if num_lancamentos >= 2:
                principal_id = lancamentos[0]['id']
                principal_ref = lancamentos[0]['referente']
                
                for lancamento in lancamentos[1:]:
                    vinculado_id = lancamento['id']
                    vinculado_ref = lancamento['referente']
                    
                    observacao = f"Migrado de grupo_lancamento: {grupo_id}"
                    
                    print(f"        ├─ Vincular {principal_id} ({principal_ref}) → {vinculado_id} ({vinculado_ref})")
                    
                    if not simular:
                        try:
                            # Inserir vínculo
                            insert_sql = """
                            INSERT INTO formulario_vinculos 
                            (formulario_id_principal, formulario_id_vinculado, tipo_vinculo, ativo, observacao)
                            VALUES (%s, %s, 'multiple_payment', 1, %s)
                            """
                            
                            cursor.execute(insert_sql, (principal_id, vinculado_id, observacao))
                            total_vinculos_criados += 1
                            
                        except Exception as e:
                            msg = f"Erro ao vincular {principal_id} → {vinculado_id}: {e}"
                            print(f"        ❌ {msg}")
                            erros.append(msg)
            else:
                print(f"        ⏭️  Ignorado (apenas 1 lançamento no grupo)")
        
        # 3. Fazer commit
        if not simular:
            conn.commit()
            print(f"\n✅ MIGRAÇÃO COMPLETADA!")
            print(f"   • Vínculos criados: {total_vinculos_criados}")
            if erros:
                print(f"   • Erros encontrados: {len(erros)}")
                for erro in erros[:5]:
                    print(f"     - {erro}")
        else:
            print(f"\n📊 RESULTADO DA SIMULAÇÃO:")
            print(f"   • Vínculos que seriam criados: {total_vinculos_criados}")
            if erros:
                print(f"   • Erros esperados: {len(erros)}")
        
        cursor.close()
        return total_vinculos_criados, erros
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro fatal durante migração: {e}")
        cursor.close()
        return 0, [str(e)]
    finally:
        conn.close()

def validar_migracao():
    """Validar integridade da migração"""
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        print("\n" + "="*70)
        print("✓ VALIDAÇÃO DA MIGRAÇÃO")
        print("="*70)
        
        # 1. Verificar vínculos órfãos
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM formulario_vinculos v
            LEFT JOIN formulario f1 ON v.formulario_id_principal = f1.id
            LEFT JOIN formulario f2 ON v.formulario_id_vinculado = f2.id
            WHERE f1.id IS NULL OR f2.id IS NULL
        """)
        
        orfaos = cursor.fetchone()['total']
        print(f"\n📍 Vínculos órfãos: {orfaos}")
        
        if orfaos > 0:
            print("   ⚠️  Existem vínculos com formulários deletados!")
        else:
            print("   ✅ Nenhum vínculo órfão")
        
        # 2. Verificar duplicatas
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM (
                SELECT 
                    LEAST(formulario_id_principal, formulario_id_vinculado) as id1,
                    GREATEST(formulario_id_principal, formulario_id_vinculado) as id2,
                    tipo_vinculo,
                    COUNT(*) as total_duplicatas
                FROM formulario_vinculos
                GROUP BY id1, id2, tipo_vinculo
                HAVING COUNT(*) > 1
            ) duplicatas
        """)
        
        dups = cursor.fetchone()['total']
        print(f"\n🔄 Vínculos duplicados: {dups}")
        
        if dups > 0:
            print("   ⚠️  Existem vínculos duplicados!")
        else:
            print("   ✅ Nenhum vínculo duplicado")
        
        # 3. Estatísticas finais
        cursor.execute("""
            SELECT 
                COUNT(*) as total_vinculos,
                SUM(CASE WHEN ativo = 1 THEN 1 ELSE 0 END) as ativos,
                COUNT(DISTINCT CASE WHEN ativo = 1 THEN formulario_id_principal END) as formularios_como_principal
            FROM formulario_vinculos
        """)
        
        stats = cursor.fetchone()
        print(f"\n📊 Estatísticas Finais:")
        print(f"   • Total de vínculos: {stats['total_vinculos']}")
        print(f"   • Vínculos ativos: {stats['ativos']}")
        print(f"   • Formulários como principal: {stats['formularios_como_principal']}")
        
        cursor.close()
        return orfaos == 0 and dups == 0
        
    except Exception as e:
        print(f"❌ Erro ao validar: {e}")
        cursor.close()
        return False
    finally:
        conn.close()

def main():
    """Função principal"""
    
    print("\n" + "="*70)
    print("🔄 FERRAMENTA DE MIGRAÇÃO: grupo_lancamento → formulario_vinculos")
    print("="*70)
    
    try:
        # 1. Analisar dados atuais
        stats = analisar_dados_atuais()
        
        if stats is None:
            print("\n❌ Não foi possível analisar os dados. Abortando.")
            return
        
        # 2. Verificar vínculos existentes
        vinculos_existentes = verificar_vinculos_existentes()
        
        if vinculos_existentes > 0:
            print("\n⚠️  JÁ EXISTEM VÍNCULOS! Continuar pode criar duplicatas.")
            print("   Recomendação: Executar em ambiente de testes primeiro.")
        
        # 3. Simular migração
        print("\n" + "-"*70)
        print("Etapa 1/3: Simulando migração (sem alterações)...")
        print("-"*70)
        
        vinculos_sim, erros_sim = migrar_dados(simular=True)
        
        # 4. Perguntar confirmação
        if vinculos_sim > 0:
            resposta = input(f"\n❓ Deseja executar a migração real criando {vinculos_sim} vínculos? (s/n): ").lower()
            
            if resposta == 's':
                print("\n" + "-"*70)
                print("Etapa 2/3: Executando migração real...")
                print("-"*70)
                
                vinculos_real, erros_real = migrar_dados(simular=False)
                
                if vinculos_real > 0:
                    print("\n" + "-"*70)
                    print("Etapa 3/3: Validando integridade...")
                    print("-"*70)
                    
                    valida = validar_migracao()
                    
                    if valida:
                        print("\n" + "="*70)
                        print("✅ MIGRAÇÃO REALIZADA COM SUCESSO!")
                        print("="*70)
                    else:
                        print("\n⚠️  Migração completada, mas há problemas de integridade.")
            else:
                print("\n⏭️  Migração cancelada pelo usuário.")
        else:
            print("\nℹ️  Nenhum dado para migrar.")
    
    except KeyboardInterrupt:
        print("\n\n⏸️  Operação cancelada pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
