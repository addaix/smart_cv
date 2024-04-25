FROM python:3.9-slim

# Copiez les fichiers locaux dans le conteneur
WORKDIR /app
COPY ./smart_cv/* /app
RUN mkdir -p /root/.config/smart_cv/configs
COPY ./smart_cv/data/defaults/* /root/.config/smart_cv/configs/

# Installez les dépendances
RUN pip install git+https://github.com/i2mint/dol
RUN pip install git+https://github.com/i2mint/config2py
RUN pip install git+https://github.com/meshed
RUN pip install streamlit

# Exposez le port pour Streamlit
EXPOSE 8501

# Commande pour exécuter l'application Streamlit
CMD streamlit run st_interface.py
