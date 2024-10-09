# Centralized Hub Home Automation

In the rapid envolving landscape of the digital technology, the IoT show transformative potential for other sector in Malaysia. however with that growignn of IoT, there is not all people aware of IoT existence or practical application. Implementation on IoT based technology can be seen in the Malaysia where the start to introduce The Smart City Framework Malaysia (MSCF) as the step for Implementing IoT which give motivation me try to understand or try how IoT works. Malaysians, espically in sabah have the choices to become the early adopter for IoT implementation but the choice of trying IoT is limited. Because of the choice limitation, IoT likely vendor locked, scattered, and pricey to own one. Even finding a good IoT product is only available at the Peninsular Malaysia. The Project stockholder is mainly for the hobbyist , IoT store, Internet Service Provider and IT store so that they can implement IoT on their own home. This Project aim to develop a low cost, lightweight IoT infrastructure which operates using MQTT as the communication Protocol. after designing the project, its will need to develop a centralized system for communication between IoT devices using Raspberry Pi as the Server and ESP as the IoT client. After Develop the system, the project need to evaluate the general functionality of the IoT system by doing usability testing and black box such as automation and remote functions  


ps : idk what i wrote but that the introduction

## Usage

local usage, local network, closed network = more secure right (can't avoid tailgating tbh), this project is small scope soo there is noting that i can do atm

## DockerFile 

i consider to intergrate with docker but sadly not able to do it, needed MacVlan (on future if i remember)
``` 
# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application into the container
COPY . .

# Expose the port the app runs on
EXPOSE 5000
EXPOSE 8080

# Define the command to run the application
CMD ["python", "app.py"]

```

## additional note

why i still here? just to suffer