import json
import argparse
import sys
import os
from typing import Dict, Any

class ConfigError(Exception):
    """Базовое исключение для ошибок конфигурации"""
    pass

class ConfigValidationError(ConfigError):
    """Ошибка валидации конфигурационных параметров"""
    pass

class ConfigFileError(ConfigError):
    """Ошибка работы с файлом конфигурации"""
    pass

class DependencyAnalyzerConfig:
    """Класс для работы с конфигурацией анализатора зависимостей"""
    
    # Значения по умолчанию
    DEFAULT_CONFIG = {
        "package_name": "",
        "repository_url": "",
        "test_repo_mode": "remote",
        "output_image": "dependency_graph.png",
        "ascii_tree_output": False,
        "max_depth": 3,
        "filter_substring": ""
    }
    
    VALID_TEST_MODES = {"remote", "local"}
    
    def __init__(self, config_file: str = None):
        self.config = self.DEFAULT_CONFIG.copy()
        self.config_file = config_file
        
        if config_file:
            self.load_config(config_file)
    
    def load_config(self, config_file: str) -> None:
        """Загрузка конфигурации из JSON файла"""
        try:
            if not os.path.exists(config_file):
                raise ConfigFileError(f"Конфигурационный файл не найден: {config_file}")
            
            with open(config_file, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
            
            # Обновляем только существующие ключи
            for key, value in loaded_config.items():
                if key in self.DEFAULT_CONFIG:
                    self.config[key] = value
            
            self.validate_config()
            
        except json.JSONDecodeError as e:
            raise ConfigFileError(f"Ошибка парсинга JSON: {e}")
        except PermissionError as e:
            raise ConfigFileError(f"Нет прав доступа к файлу: {e}")
        except Exception as e:
            raise ConfigFileError(f"Неизвестная ошибка при чтении файла: {e}")
    
    def validate_config(self) -> None:
        """Валидация конфигурационных параметров"""
        errors = []
        
        # Проверка имени пакета
        if not isinstance(self.config["package_name"], str):
            errors.append("Имя пакета должно быть строкой")
        
        # Проверка URL репозитория/пути
        if not isinstance(self.config["repository_url"], str):
            errors.append("URL репозитория/путь должен быть строкой")
        
        # Проверка режима работы
        if self.config["test_repo_mode"] not in self.VALID_TEST_MODES:
            errors.append(f"Неверный режим работы. Допустимые значения: {', '.join(self.VALID_TEST_MODES)}")
        
        # Проверка имени файла изображения
        if not isinstance(self.config["output_image"], str):
            errors.append("Имя файла изображения должно быть строкой")
        elif not self.config["output_image"].endswith(('.png', '.jpg', '.jpeg', '.svg')):
            errors.append("Файл изображения должен иметь расширение .png, .jpg, .jpeg или .svg")
        
        # Проверка флага ASCII-дерева
        if not isinstance(self.config["ascii_tree_output"], bool):
            errors.append("Режим ASCII-дерева должен быть булевым значением")
        
        # Проверка максимальной глубины
        if not isinstance(self.config["max_depth"], int):
            errors.append("Максимальная глубина должна быть целым числом")
        elif self.config["max_depth"] < 1:
            errors.append("Максимальная глубина должна быть положительным числом")
        
        # Проверка подстроки фильтрации
        if not isinstance(self.config["filter_substring"], str):
            errors.append("Подстрока фильтрации должна быть строкой")
        
        if errors:
            raise ConfigValidationError("; ".join(errors))
    
    def get(self, key: str) -> Any:
        """Получение значения параметра"""
        return self.config.get(key)
    
    def display_config(self) -> None:
        """Вывод всех параметров в формате ключ-значение"""
        print("Текущая конфигурация:")
        print("-" * 40)
        for key, value in self.config.items():
            print(f"{key}: {value}")
        print("-" * 40)

def create_sample_config() -> None:
    """Создание примера конфигурационного файла"""
    sample_config = {
        "package_name": "requests",
        "repository_url": "https://github.com/psf/requests",
        "test_repo_mode": "remote",
        "output_image": "requests_dependencies.png",
        "ascii_tree_output": True,
        "max_depth": 2,
        "filter_substring": "http"
    }
    
    with open('config_sample.json', 'w', encoding='utf-8') as f:
        json.dump(sample_config, f, indent=2, ensure_ascii=False)
    
    print("Создан пример конфигурационного файла: config_sample.json")

def main():
    parser = argparse.ArgumentParser(description='Анализатор зависимостей пакетов')
    parser.add_argument('--config', '-c', type=str, 
                       help='Путь к конфигурационному файлу JSON')
    parser.add_argument('--create-sample', action='store_true',
                       help='Создать пример конфигурационного файла')
    
    args = parser.parse_args()
    
    if args.create_sample:
        create_sample_config()
        return
    
    try:
        # Загрузка конфигурации
        config = DependencyAnalyzerConfig(args.config)
        
        # Вывод всех параметров (требование этапа 1)
        config.display_config()
        
        # Демонстрация получения отдельных параметров
        print("\nДемонстрация доступа к параметрам:")
        print(f"Анализируемый пакет: {config.get('package_name')}")
        print(f"Режим работы: {config.get('test_repo_mode')}")
        print(f"Максимальная глубина: {config.get('max_depth')}")
        
    except ConfigError as e:
        print(f"Ошибка конфигурации: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Неожиданная ошибка: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()