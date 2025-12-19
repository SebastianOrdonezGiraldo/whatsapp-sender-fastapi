#!/usr/bin/env python3
"""Script para crear la estructura completa del proyecto whatsapp-sender-fastapi."""

import os
from pathlib import Path


def create_structure():
    """Crea toda la estructura de carpetas y archivos del proyecto."""
    
    structure = {
        "app": {
            "__init__.py": '"""WhatsApp Sender FastAPI Backend."""',
            "main.py":  "",
            "api": {
                "__init__.py": "",
                "dependencies.py": "",
                "middleware.py": "",
                "v1": {
                    "__init__.py": "",
                    "router.py":  "",
                    "endpoints": {
                        "__init__.py":  "",
                        "campaigns.py": "",
                        "templates. py": "",
                        "messages.py": "",
                        "statistics.py": "",
                        "health.py": "",
                        "webhooks.py": "",
                    }
                }
            },
            "core": {
                "__init__.py": "",
                "config.py": "",
                "database.py": "",
                "redis.py": "",
                "security.py": "",
                "logging.py": "",
                "events.py": "",
                "exceptions.py": "",
            },
            "db":  {
                "__init__.py":  "",
                "base.py":  "",
                "session.py":  "",
                "repositories": {
                    "__init__.py": "",
                    "base.py":  "",
                    "campaign_repository.py": "",
                    "message_repository.py": "",
                    "template_repository. py": "",
                }
            },
            "models": {
                "__init__.py": "",
                "base.py": "",
                "campaign.py": "",
                "message.py": "",
                "template.py": "",
                "user.py": "",
            },
            "schemas": {
                "__init__.py": "",
                "base.py": "",
                "campaign.py": "",
                "message.py": "",
                "template.py": "",
                "csv_schema.py": "",
                "statistics. py": "",
                "responses. py": "",
            },
            "services": {
                "__init__.py": "",
                "base.py": "",
                "campaign_service.py": "",
                "csv_service.py": "",
                "cache_service.py": "",
                "statistics_service.py": "",
                "notification_service.py": "",
                "whatsapp": {
                    "__init__.py": "",
                    "client.py": "",
                    "message_builder. py": "",
                    "template_parser.py": "",
                    "validators.py": "",
                }
            },
            "workers": {
                "__init__. py": "",
                "queue. py": "",
                "tasks":  {
                    "__init__.py": "",
                    "campaign_tasks.py": "",
                    "message_tasks.py": "",
                    "cleanup_tasks. py": "",
                },
                "handlers": {
                    "__init__.py": "",
                    "campaign_handler.py": "",
                    "message_handler. py": "",
                }
            },
            "utils": {
                "__init__.py": "",
                "validators.py": "",
                "helpers.py": "",
                "constants.py": "",
                "enums.py": "",
                "decorators.py":  "",
                "retry.py":  "",
            },
            "domain": {
                "__init__.py": "",
                "entities": {
                    "__init__.py":  "",
                    "campaign_entity.py": "",
                },
                "value_objects": {
                    "__init__.py": "",
                    "phone_number. py": "",
                    "template_variable.py": "",
                },
                "events": {
                    "__init__. py": "",
                    "campaign_events.py": "",
                }
            }
        },
        "tests": {
            "__init__.py": "",
            "conftest.py": "",
            "factories.py": "",
            "unit": {
                "__init__.py": "",
                "services": {
                    "__init__. py": "",
                    "test_campaign_service.py": "",
                    "test_whatsapp_client.py": "",
                    "test_csv_service.py": "",
                },
                "repositories": {
                    "__init__.py": "",
                    "test_campaign_repository. py": "",
                },
                "utils": {
                    "__init__.py": "",
                    "test_validators.py": "",
                }
            },
            "integration": {
                "__init__.py": "",
                "api": {
                    "__init__. py": "",
                    "test_campaigns_api.py": "",
                    "test_templates_api.py": "",
                },
                "database": {
                    "__init__.py": "",
                    "test_repositories.py": "",
                },
                "workers": {
                    "__init__.py": "",
                    "test_campaign_tasks.py":  "",
                }
            },
            "e2e": {
                "__init__.py": "",
                "test_campaign_flow. py": "",
            },
            "fixtures": {
                "__init__.py": "",
                "sample.csv": "ID,Recipient-Phone-Number,body_1,body_2\n1,573001234567,John,Doe\n",
                "templates.json": "{}",
                "mock_responses.json": "{}",
            }
        },
        "migrations": {
            "versions": {
                ". gitkeep": "",
            },
            "env.py": "",
            "script.py.mako": "",
        },
        "scripts": {
            "init_db.py": "",
            "seed_data.py": "",
            "start_worker.sh": "#!/bin/bash\nrq worker --with-scheduler\n",
            "start_dev.sh": "#!/bin/bash\nuvicorn app.main:app --reload --host 0.0.0.0 --port 8000\n",
            "run_migrations.py":  "",
        },
        "docs": {
            "api": {
                "campaigns.md": "",
                "templates.md": "",
            },
            "architecture. md": "",
            "deployment. md": "",
            "contributing. md": "",
        },
        "data": {
            "uploads": {
                ".gitkeep": "",
            },
            "campaign_logs": {
                ". gitkeep": "",
            },
            "backups": {
                ".gitkeep": "",
            }
        },
        "logs": {
            ".gitkeep": "",
        },
        ".github": {
            "workflows": {
                "ci.yml": "",
                "tests.yml": "",
                "deploy.yml": "",
            }
        }
    }
    
    def create_tree(base_path, tree):
        """Recursivamente crea la estructura de archivos y carpetas."""
        for name, content in tree.items():
            path = base_path / name
            
            if isinstance(content, dict):
                path.mkdir(parents=True, exist_ok=True)
                print(f"📁 Created directory: {path}")
                create_tree(path, content)
            else:
                path.parent. mkdir(parents=True, exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"📄 Created file: {path}")
                
                if path.suffix == '.sh':
                    os.chmod(path, 0o755)
                    print(f"  ✓ Made executable: {path}")
    
    base_path = Path.cwd()
    print(f"\n🚀 Creating project structure in: {base_path}\n")
    create_tree(base_path, structure)
    print(f"\n✅ Project structure created successfully!\n")
    
    print("📊 Summary:")
    print("   - app/ (main application)")
    print("   - tests/ (unit, integration, e2e)")
    print("   - migrations/ (database migrations)")
    print("   - scripts/ (utility scripts)")
    print("   - docs/ (documentation)")
    print("   - data/ (uploads and logs)")
    print("\n🎯 Next steps:")
    print("   1. git add .")
    print("   2. git commit -m 'feat: create project structure'")
    print("   3. git push origin main")
    print("   4. Install dependencies: poetry install\n")


if __name__ == "__main__":
    try:
        create_structure()
    except Exception as e:
        print(f"\n❌ Error creating structure:  {e}")
        raise