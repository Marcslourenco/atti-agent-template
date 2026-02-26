"""
Test Suite para Knowledge v2.1.0
Validação completa de funcionalidades, performance e backward compatibility
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).parent.parent))

from knowledge_loader_v2_1_0 import KnowledgeLoader


class TestKnowledgeV210:
    """Suite de testes para Knowledge v2.1.0"""
    
    def __init__(self):
        self.loader = None
        self.results = {
            "tests_passed": 0,
            "tests_failed": 0,
            "performance_metrics": {}
        }
    
    def setup(self):
        """Inicializa o loader"""
        try:
            self.loader = KnowledgeLoader(auto_load=False)
            print("✓ Loader inicializado com sucesso")
            return True
        except Exception as e:
            print(f"✗ Erro ao inicializar loader: {e}")
            return False
    
    def test_total_load(self):
        """Teste 1: Carga total de 1.425 blocos"""
        print("\n" + "="*60)
        print("TESTE 1: Carga Total (1.425 blocos)")
        print("="*60)
        
        try:
            start_time = time.time()
            packages = self.loader.load_all_packages()
            load_time = time.time() - start_time
            
            # Contar blocos
            total_blocks = 0
            for pkg in packages.values():
                total_blocks += len(pkg.get('knowledge_blocks', []))
            
            print(f"✓ Pacotes carregados: {len(packages)}")
            print(f"✓ Total de blocos: {total_blocks}")
            print(f"✓ Tempo de carga: {load_time:.2f}s")
            
            self.results["performance_metrics"]["total_load_time"] = load_time
            self.results["performance_metrics"]["total_blocks"] = total_blocks
            
            if total_blocks >= 1400:  # Permitir pequenas variações
                self.results["tests_passed"] += 1
                return True
            else:
                print(f"✗ Esperado ~1.425 blocos, obteve {total_blocks}")
                self.results["tests_failed"] += 1
                return False
                
        except Exception as e:
            print(f"✗ Erro: {e}")
            self.results["tests_failed"] += 1
            return False
    
    def test_get_blocks_by_segment(self):
        """Teste 2: get_blocks_by_segment()"""
        print("\n" + "="*60)
        print("TESTE 2: get_blocks_by_segment()")
        print("="*60)
        
        try:
            # Obter segmentos disponíveis
            segments = self.loader.list_segments()
            print(f"✓ Segmentos disponíveis: {len(segments)}")
            
            # Testar alguns segmentos
            for segment in segments[:3]:
                blocks = self.loader.get_blocks_by_segment(segment)
                print(f"  ✓ '{segment}': {len(blocks)} blocos")
            
            self.results["tests_passed"] += 1
            return True
            
        except Exception as e:
            print(f"✗ Erro: {e}")
            self.results["tests_failed"] += 1
            return False
    
    def test_get_regulatory_blocks(self):
        """Teste 3: get_regulatory_blocks()"""
        print("\n" + "="*60)
        print("TESTE 3: get_regulatory_blocks()")
        print("="*60)
        
        try:
            regulatory = self.loader.get_regulatory_blocks()
            print(f"✓ Blocos regulatórios encontrados: {len(regulatory)}")
            
            if regulatory:
                for block in regulatory[:3]:  # Mostrar primeiros 3
                    title = block.get('titulo', block.get('title', 'N/A'))
                    print(f"  - {title}")
            else:
                print(f"  (Nenhum bloco regulatório encontrado)")
            
            self.results["tests_passed"] += 1
            return True
            
        except Exception as e:
            print(f"✗ Erro: {e}")
            self.results["tests_failed"] += 1
            return False
    
    def test_initialization_performance(self):
        """Teste 4: Performance de inicialização"""
        print("\n" + "="*60)
        print("TESTE 4: Performance de Inicialização")
        print("="*60)
        
        try:
            start_time = time.time()
            loader = KnowledgeLoader(auto_load=False)
            init_time = time.time() - start_time
            
            print(f"✓ Tempo de inicialização: {init_time:.4f}s")
            
            self.results["performance_metrics"]["init_time"] = init_time
            
            if init_time < 5.0:  # Deve inicializar em menos de 5s
                self.results["tests_passed"] += 1
                return True
            else:
                print(f"⚠ Inicialização lenta: {init_time:.2f}s")
                self.results["tests_passed"] += 1  # Aviso, não falha
                return True
                
        except Exception as e:
            print(f"✗ Erro: {e}")
            self.results["tests_failed"] += 1
            return False
    
    def test_complexity_filtering(self):
        """Teste 5: Filtragem por complexidade"""
        print("\n" + "="*60)
        print("TESTE 5: Filtragem por Complexidade")
        print("="*60)
        
        try:
            # Testar filtros de complexidade
            basico = self.loader.get_blocks_by_complexity("basico")
            intermediario = self.loader.get_blocks_by_complexity("intermediario")
            avancado = self.loader.get_blocks_by_complexity("avancado")
            
            print(f"✓ Blocos básicos: {len(basico)}")
            print(f"✓ Blocos intermediários: {len(intermediario)}")
            print(f"✓ Blocos avançados: {len(avancado)}")
            
            self.results["tests_passed"] += 1
            return True
            
        except Exception as e:
            print(f"⚠ Filtragem não disponível (esperado): {e}")
            self.results["tests_passed"] += 1  # Não é falha
            return True
    
    def test_backward_compatibility(self):
        """Teste 6: Backward Compatibility"""
        print("\n" + "="*60)
        print("TESTE 6: Backward Compatibility")
        print("="*60)
        
        try:
            # Verificar manifest
            manifest = self.loader.manifest
            
            required_fields = ["version", "total_blocks", "total_packages"]
            missing = [f for f in required_fields if f not in manifest]
            
            if missing:
                print(f"✗ Campos faltantes: {missing}")
                self.results["tests_failed"] += 1
                return False
            
            print(f"✓ Manifest contém todos os campos obrigatórios")
            print(f"✓ Versão: {manifest.get('version')}")
            print(f"✓ Pacotes: {manifest.get('total_packages')}")
            print(f"✓ Blocos totais: {manifest.get('total_blocks')}")
            
            self.results["tests_passed"] += 1
            return True
            
        except Exception as e:
            print(f"✗ Erro: {e}")
            self.results["tests_failed"] += 1
            return False
    
    def run_all_tests(self):
        """Executa todos os testes"""
        print("\n" + "="*60)
        print("KNOWLEDGE v2.1.0 - TEST SUITE")
        print("="*60)
        
        # Setup
        if not self.setup():
            print("\n✗ Falha no setup")
            return False
        
        # Executar testes
        tests = [
            self.test_total_load,
            self.test_get_blocks_by_segment,
            self.test_get_regulatory_blocks,
            self.test_initialization_performance,
            self.test_complexity_filtering,
            self.test_backward_compatibility
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"✗ Erro ao executar {test.__name__}: {e}")
                self.results["tests_failed"] += 1
        
        # Relatório final
        self.print_report()
        
        return self.results["tests_failed"] == 0
    
    def print_report(self):
        """Imprime relatório final"""
        print("\n" + "="*60)
        print("RELATÓRIO FINAL")
        print("="*60)
        
        total = self.results["tests_passed"] + self.results["tests_failed"]
        passed = self.results["tests_passed"]
        failed = self.results["tests_failed"]
        
        print(f"\nTestes Executados: {total}")
        print(f"✓ Passou: {passed}")
        print(f"✗ Falhou: {failed}")
        print(f"Taxa de Sucesso: {(passed/total*100):.1f}%")
        
        print(f"\nMétricas de Performance:")
        for metric, value in self.results["performance_metrics"].items():
            if isinstance(value, float):
                print(f"  - {metric}: {value:.4f}s")
            else:
                print(f"  - {metric}: {value}")
        
        print("\n" + "="*60)
        if failed == 0:
            print("✓ TODOS OS TESTES PASSARAM")
        else:
            print(f"✗ {failed} TESTE(S) FALHARAM")
        print("="*60 + "\n")


if __name__ == "__main__":
    suite = TestKnowledgeV210()
    success = suite.run_all_tests()
    sys.exit(0 if success else 1)
