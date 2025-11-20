import json
import urllib.request
import urllib.error
from typing import Dict, List, Any, Set, Tuple
import sys
import os
from collections import deque

class NPMAnalyzer:
    """Анализатор зависимостей npm пакетов"""
    
    NPM_REGISTRY_URL = "https://registry.npmjs.org"
    
    def __init__(self, config):
        self.config = config
        self.visited = set()
        self.cycle_detected = False
    
    def get_package_info(self, package_name: str) -> Dict[str, Any]:
        """Получение информации о пакете из npm registry"""
        url = f"{self.NPM_REGISTRY_URL}/{package_name}"
        
        try:
            with urllib.request.urlopen(url) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    return data
                else:
                    raise Exception(f"HTTP {response.status}: {response.reason}")
                    
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise Exception(f"Пакет '{package_name}' не найден в npm registry")
            else:
                raise Exception(f"Ошибка при запросе к npm registry: {e}")
        except urllib.error.URLError as e:
            raise Exception(f"Ошибка сети: {e}")
        except Exception as e:
            raise Exception(f"Неизвестная ошибка: {e}")
    
    def extract_dependencies(self, package_info: Dict[str, Any]) -> Dict[str, str]:
        """Извлечение прямых зависимостей из информации о пакете"""
        dependencies = {}
        
        # Получаем последнюю версию
        latest_version = package_info.get('dist-tags', {}).get('latest')
        if not latest_version:
            versions = package_info.get('versions', {})
            if versions:
                latest_version = list(versions.keys())[-1]
            else:
                return dependencies
        
        version_info = package_info.get('versions', {}).get(latest_version, {})
        
        # Извлекаем только runtime зависимости (без dev и peer для упрощения)
        deps = version_info.get('dependencies', {})
        
        return deps
    
    def should_skip_package(self, package_name: str) -> bool:
        """Проверка, нужно ли пропустить пакет по фильтру"""
        filter_substring = self.config.get('filter_substring', '').strip()
        if filter_substring and filter_substring in package_name:
            return True
        return False
    
    def dfs_build_dependency_graph(self, start_package: str) -> Dict[str, List[str]]:
        """Построение графа зависимостей с помощью DFS без рекурсии"""
        graph = {}
        stack = deque([(start_package, 0)])  # (package_name, current_depth)
        max_depth = self.config.get('max_depth', 3)
        
        while stack:
            current_package, depth = stack.pop()
            
            # Пропускаем пакеты по фильтру
            if self.should_skip_package(current_package):
                continue
            
            # Если достигли максимальной глубины, не идем дальше
            if depth >= max_depth:
                if current_package not in graph:
                    graph[current_package] = []
                continue
            
            # Если пакет уже посещен, отмечаем цикл и пропускаем
            if current_package in graph:
                self.cycle_detected = True
                continue
            
            try:
                # Получаем информацию о пакете
                package_info = self.get_package_info(current_package)
                dependencies = self.extract_dependencies(package_info)
                
                # Добавляем зависимости в граф
                graph[current_package] = []
                for dep_name in dependencies.keys():
                    if not self.should_skip_package(dep_name):
                        graph[current_package].append(dep_name)
                        # Добавляем зависимость в стек для дальнейшего анализа
                        if dep_name not in graph:
                            stack.append((dep_name, depth + 1))
                
            except Exception as e:
                print(f"⚠️  Ошибка при анализе пакета {current_package}: {e}")
                graph[current_package] = []
        
        return graph
    
    def load_test_repository(self, file_path: str) -> Dict[str, List[str]]:
        """Загрузка тестового репозитория из файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                test_data = json.load(f)
            return test_data
        except Exception as e:
            raise Exception(f"Ошибка загрузки тестового репозитория: {e}")
    
    def dfs_build_from_test_graph(self, start_package: str, test_graph: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Построение графа из тестовых данных с помощью DFS без рекурсии"""
        graph = {}
        stack = deque([(start_package, 0)])  # (package_name, current_depth)
        max_depth = self.config.get('max_depth', 3)
        
        while stack:
            current_package, depth = stack.pop()
            
            # Пропускаем пакеты по фильтру
            if self.should_skip_package(current_package):
                continue
            
            # Если достигли максимальной глубины, не идем дальше
            if depth >= max_depth:
                if current_package not in graph:
                    graph[current_package] = []
                continue
            
            # Если пакет уже посещен в графе, отмечаем цикл
            if current_package in graph:
                self.cycle_detected = True
                continue
            
            # Получаем зависимости из тестового графа
            if current_package in test_graph:
                dependencies = test_graph[current_package]
                
                # Добавляем зависимости в граф
                graph[current_package] = []
                for dep_name in dependencies:
                    if not self.should_skip_package(dep_name):
                        graph[current_package].append(dep_name)
                        # Добавляем зависимость в стек для дальнейшего анализа
                        if dep_name not in graph:
                            stack.append((dep_name, depth + 1))
            else:
                graph[current_package] = []
        
        return graph
    
    def analyze_dependencies(self) -> Dict[str, List[str]]:
        """Основной метод анализа зависимостей"""
        package_name = self.config.get('package_name')
        repo_url = self.config.get('repository_url')
        test_mode = self.config.get('test_repo_mode')
        
        if not package_name:
            raise Exception("Имя пакета не указано в конфигурации")
        
        print(f"Анализ зависимостей пакета: {package_name}")
        print(f"Режим: {test_mode}")
        print(f"Максимальная глубина: {self.config.get('max_depth')}")
        print(f"Фильтр: '{self.config.get('filter_substring', '')}'")
        print("=" * 60)
        
        # Сбрасываем флаг цикла
        self.cycle_detected = False
        
        if test_mode == "local" and repo_url.endswith('.json'):
            # Режим тестирования с файлом
            print("📁 Используется тестовый репозиторий")
            test_graph = self.load_test_repository(repo_url)
            graph = self.dfs_build_from_test_graph(package_name, test_graph)
        else:
            # Режим работы с реальным npm registry
            print("🌐 Используется npm registry")
            graph = self.dfs_build_dependency_graph(package_name)
        
        return graph
    
    def print_dependency_tree(self, graph: Dict[str, List[str]]):
        """Вывод дерева зависимостей в формате ASCII"""
        start_package = self.config.get('package_name')
        
        if self.should_skip_package(start_package):
            print("⛔ Корневой пакет отфильтрован")
            return
        
        print("\n🌳 Дерево зависимостей:")
        print("-" * 40)
        
        def print_node(package: str, depth: int, prefix: str = "", is_last: bool = True):
            """Рекурсивный вывод узла дерева"""
            if depth > self.config.get('max_depth', 3):
                return
                
            connector = "└── " if is_last else "├── "
            print(f"{prefix}{connector}{package}")
            
            if package in graph:
                children = graph[package]
                new_prefix = prefix + ("    " if is_last else "│   ")
                
                for i, child in enumerate(children):
                    is_last_child = i == len(children) - 1
                    print_node(child, depth + 1, new_prefix, is_last_child)
        
        print_node(start_package, 0)
        
        if self.cycle_detected:
            print("\n⚠️  Обнаружены циклические зависимости!")
        
        print(f"\n📊 Статистика:")
        print(f"   Всего пакетов: {len(graph)}")
        print(f"   Циклические зависимости: {'Да' if self.cycle_detected else 'Нет'}")

def create_test_repositories():
    """Создание тестовых репозиториев для демонстрации"""
    
    # Тест 1: Простой граф без циклов
    test1 = {
        "A": ["B", "C"],
        "B": ["D", "E"],
        "C": ["F"],
        "D": [],
        "E": ["G"],
        "F": [],
        "G": []
    }
    
    with open('test_simple.json', 'w') as f:
        json.dump(test1, f, indent=2)
    
    # Тест 2: Граф с циклическими зависимостями
    test2 = {
        "A": ["B"],
        "B": ["C"],
        "C": ["A", "D"],  # Цикл A->B->C->A
        "D": ["E"],
        "E": []
    }
    
    with open('test_cycle.json', 'w') as f:
        json.dump(test2, f, indent=2)
    
    # Тест 3: Сложный граф с фильтрацией
    test3 = {
        "APP": ["UI", "UTILS", "NETWORK"],
        "UI": ["COMPONENTS", "STYLES"],
        "UTILS": ["HELPERS", "VALIDATORS"],
        "NETWORK": ["HTTP", "WEBSOCKET"],
        "COMPONENTS": ["BUTTON", "INPUT"],
        "STYLES": ["COLORS"],
        "HELPERS": ["STRING_UTILS"],
        "VALIDATORS": ["EMAIL_VALIDATOR"],
        "HTTP": [],
        "WEBSOCKET": [],
        "BUTTON": [],
        "INPUT": [],
        "COLORS": [],
        "STRING_UTILS": [],
        "EMAIL_VALIDATOR": []
    }
    
    with open('test_complex.json', 'w') as f:
        json.dump(test3, f, indent=2)
    
    print("✅ Созданы тестовые репозитории:")
    print("   - test_simple.json (простой граф)")
    print("   - test_cycle.json (граф с циклом)")
    print("   - test_complex.json (сложный граф)")

def main():
    """Основная функция приложения"""
    
    # Создаем тестовые репозитории
    create_test_repositories()
    
    # Загрузка конфигурации
    try:
        if len(sys.argv) > 1:
            config_file = sys.argv[1]
        else:
            config_file = 'config.json'
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
    except FileNotFoundError:
        print(f"❌ Конфигурационный файл '{config_file}' не найден")
        print("\n📝 Примеры конфигураций для тестирования:")
        
        examples = {
            "test_simple.json": {
                "package_name": "A",
                "repository_url": "test_simple.json",
                "test_repo_mode": "local",
                "output_image": "graph_simple.png",
                "ascii_tree_output": True,
                "max_depth": 3,
                "filter_substring": ""
            },
            "test_cycle.json": {
                "package_name": "A", 
                "repository_url": "test_cycle.json",
                "test_repo_mode": "local",
                "output_image": "graph_cycle.png",
                "ascii_tree_output": True,
                "max_depth": 5,
                "filter_substring": ""
            },
            "test_filter.json": {
                "package_name": "APP",
                "repository_url": "test_complex.json", 
                "test_repo_mode": "local",
                "output_image": "graph_filter.png",
                "ascii_tree_output": True,
                "max_depth": 3,
                "filter_substring": "STYLES"
            },
            "real_npm.json": {
                "package_name": "express",
                "repository_url": "https://github.com/expressjs/express",
                "test_repo_mode": "remote",
                "output_image": "graph_real.png",
                "ascii_tree_output": True,
                "max_depth": 2,
                "filter_substring": ""
            }
        }
        
        for name, example_config in examples.items():
            print(f"\n--- {name} ---")
            print(json.dumps(example_config, indent=2))
            
        sys.exit(1)
        
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка в формате JSON: {e}")
        sys.exit(1)
    
    # Вывод конфигурации
    print("🔧 Конфигурация анализатора:")
    print("-" * 50)
    for key, value in config.items():
        print(f"{key:20}: {value}")
    print()
    
    # Анализ зависимостей
    try:
        analyzer = NPMAnalyzer(config)
        dependency_graph = analyzer.analyze_dependencies()
        
        # Вывод графа
        print("\n📦 Граф зависимостей:")
        print("-" * 30)
        for package, deps in dependency_graph.items():
            deps_str = ", ".join(deps) if deps else "нет зависимостей"
            print(f"{package}: {deps_str}")
        
        # Вывод ASCII дерева если включено
        if config.get('ascii_tree_output', False):
            analyzer.print_dependency_tree(dependency_graph)
            
    except Exception as e:
        print(f"❌ Ошибка при анализе зависимостей: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()