import os
from app import create_app

# Détermine la configuration à utiliser (dev, test, prod)
config_name = os.environ.get('FLASK_ENV', 'default')
app = create_app(config_name)

if __name__ == '__main__':
    app.run()