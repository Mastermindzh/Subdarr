FROM ubuntu

# Update OS
RUN sed -i 's/# \(.*multiverse$\)/\1/g' /etc/apt/sources.list
RUN apt-get update && apt-get -y upgrade

# Install docker requirements
RUN apt-get install -y build-essential libssl-dev libffi-dev python-dev python-pip

# Add local files to container
ADD . /app

# Set cwd 
ENV HOME /app
WORKDIR /app

# upgrade pip to the latest version
RUN pip install --upgrade pip

# Install requirements
RUN pip install -r requirements.txt

EXPOSE 5500

CMD ["python", "app.py"]