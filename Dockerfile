FROM python:3.9-slim

# Copiez les fichiers locaux dans le conteneur
WORKDIR /app
COPY . /app

# Installez les dépendances
RUN pip install git+https://github.com/i2mint/dol
RUN pip install git+https://github.com/i2mint/config2py
RUN pip install git+https://github.com/meshed

RUN pip install streamlit

RUN mkdir -p /root/.config/smart_cv/configs/
RUN touch /root/.config/smart_cv/configs/config.json

# Exposez le port pour Streamlit
EXPOSE 8501

# Commande pour exécuter l'application Streamlit
CMD streamlit run /app/smart_cv/st_interface.py
