# Use a Python base image
FROM python:3.9-slim


ENV NLTK_DATA=/usr/local/nltk_data
# Install required system dependencies for .NET runtime installation
RUN apt-get update && \
    apt-get install -y wget apt-transport-https software-properties-common && \
    wget https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb && \
    dpkg -i packages-microsoft-prod.deb && \
    rm packages-microsoft-prod.deb && \
    apt-get update && \
    apt-get install -y dotnet-runtime-6.0 && \
    apt-get clean



# Set the working directory inside the container
WORKDIR /app
ENV PYTHONPATH="/app"

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

RUN python -m nltk.downloader -d /usr/local/share/nltk_data all
RUN python -m nltk.downloader punkt
# Copy all files and folders into the container
COPY . /app
# Copy specific file to /tmp
COPY tmp/bridgetnew.mid /tmp/bridgetnew.mid

# Ensure executables have the correct permissions
RUN chmod +x /app/OpenUtau && chmod -R 777 /app

# Copy all non-Python files and directories from /app to /root/.local/share/OpenUtau/
RUN mkdir -p /root/.local/share/OpenUtau && \
    find /app -mindepth 1 -not -name '*.py' -exec cp -r {} /root/.local/share/OpenUtau/ \;


# for our nltk data folde


# Verify files are copied correctly
RUN ls -R /root/.local/share/OpenUtau

ENTRYPOINT ["python3", "-m", "awslambdaric"]
CMD ["script.lambda_handler"]
# CMD ["python3", "-u", "ec2_subprocess.py"]
