import json
import urllib.request
import urllib.error
from typing import Dict, List, Any
import sys
import os

class NPMAnalyzer:
    """Анализатор зависимостей npm пакетов"""
    
    NPM_REGISTRY_URL = "https://registry.npmjs.org"
    
    def __init__(self, config):
        self.config = config
    
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
            # Если нет latest, берем первую доступную версию
            versions = package_info.get('versions', {})
            if versions:
                latest_version = list(versions.keys())[-1]
            else:
                return dependencies
        
        # Получаем информацию о конкретной версии
        version_info = package_info.get('versions', {}).get(latest_version, {})
        
        # Извлекаем зависимости
        deps = version_info.get('dependencies', {})
        dev_deps = version_info.get('devDependencies', {})
        peer_deps = version_info.get('peerDependencies', {})
        
        # Объединяем все зависимости
        all_deps = {}
        all_deps.update(deps)
        all_deps.update(dev_deps)
        all_deps.update(peer_deps)
        
        return all_deps
    
    def analyze_dependencies(self) -> Dict[str, str]:
        """Основной метод анализа зависимостей"""
        package_name = self.config.get('package_name')
        
        if not package_name:
            raise Exception("Имя пакета не указано в конфигурации")
        
        print(f"Анализ зависимостей пакета: {package_name}")
        print("=" * 50)
        
        # Получаем информацию о пакете
        package_info = self.get_package_info(package_name)
        
        # Извлекаем зависимости
        dependencies = self.extract_dependencies(package_info)
        
        return dependencies

def main():
    """Основная функция приложения"""
    # Загрузка конфигурации (упрощенная версия для этапа 2)
    try:
        if len(sys.argv) > 1:
            config_file = sys.argv[1]
        else:
            config_file = 'config.json'
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
    except FileNotFoundError:
        print(f"Ошибка: Конфигурационный файл '{config_file}' не найден")
        print("Создайте config.json со следующим содержимым:")
        print(json.dumps({
            "package_name": "express",
            "repository_url": "https://github.com/expressjs/express",
            "test_repo_mode": "remote",
            "output_image": "dependencies.png",
            "ascii_tree_output": True,
            "max_depth": 1,
            "filter_substring": ""
        }, indent=2))
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Ошибка в формате JSON: {e}")
        sys.exit(1)
    
    # Вывод конфигурации (требование этапа 1)
    print("Конфигурация анализатора:")
    print("-" * 40)
    for key, value in config.items():
        print(f"{key}: {value}")
    print("-" * 40)
    print()
    
    # Анализ зависимостей
    try:
        analyzer = NPMAnalyzer(config)
        dependencies = analyzer.analyze_dependencies()
        
        # Вывод прямых зависимостей (требование этапа 2)
        if dependencies:
            print("Прямые зависимости пакета:")
            print("-" * 30)
            for dep_name, dep_version in dependencies.items():
                print(f"📦 {dep_name}: {dep_version}")
            
            print(f"\nВсего найдено зависимостей: {len(dependencies)}")
        else:
            print("⚠️  Пакет не имеет зависимостей")
            
    except Exception as e:
        print(f"❌ Ошибка при анализе зависимостей: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()