![](https://miro.medium.com/v2/resize:fit:2000/format:webp/1*90nuqeg3RNdK9S-KhFlIag.png)

## Image Breakdown

- **Driving Side (User Interface)**: 
   - This is the side where user actions take place, such as using a web or mobile interface. The **Adapter** on this side translates user inputs into commands that interact with the application’s core logic through the **Port**.

- **Driven Side (Infrastructure)**:
   - This side deals with external systems, such as databases, external services, or APIs. Here, the **Adapter** implements the necessary infrastructure logic, while the **Port** serves as the contract for how the application will interact with these external systems.

- **Interaction Flow**:
   - On the **Driving Side**, the user interacts with an **Adapter** (e.g., a web controller), which **uses** the **Port** to send a request to the **Application Service**.
   - The **Application Service** processes the request, possibly involving the **Domain** logic.
   - On the **Driven Side**, the **Application Service** **uses** the **Port** to communicate with an external system. The **Adapter** on this side **implements** the **Port** to interact with the external infrastructure (e.g., save data to a database).


# README for Hexagonal Python Projects

## Introduction

This Python project is built following the principles of **Hexagonal Architecture**, also known as the **Ports and Adapters** pattern. The architecture design separates the application's core logic (domain) from its external components (such as user interfaces, databases, and other infrastructure), promoting high modularity, testability, and maintainability. The attached image visually represents this architecture, which we will explain in detail below.

## Architectural Overview

The architecture is divided into two main sides:
1. **Driving Side**: This side initiates actions in the system (e.g., user interactions through a user interface).
2. **Driven Side**: This side is responsible for handling requests from the system, such as saving data to a database.

At the core of this architecture lies the **Domain**, which contains the business logic that is independent of external systems. 

Here’s a breakdown of the key components from the image:

### 1. **Domain**
   - The **Domain** is the heart of the application where the core business logic resides. It is isolated from the external components and contains all the rules and logic required for the application. This separation ensures that changes to external systems do not impact the business logic.

### 2. **Application Service**
   - The **Application Service** layer sits between the Domain and external systems (e.g., user interfaces, infrastructure). This layer handles application-specific logic, orchestrating tasks and processes by interacting with the domain and other components.

### 3. **Ports**
   - **Ports** are interfaces that define the entry points for both the **Driving** and **Driven** sides of the application. They are like contracts that specify how the application core (Domain) communicates with the outside world. 
   - There are two types of Ports:
     - **Input Ports (Driving Side)**: These allow the external systems (e.g., user interfaces) to trigger actions in the application.
     - **Output Ports (Driven Side)**: These are used by the application to communicate with external systems, like databases, message queues, etc. These ports are names as "Repositories"

### 4. **Adapters**
   - **Adapters** implement the Ports and act as translators between the domain and external components. They convert the data and actions into a format that the external systems or the domain logic can understand. 
   - There are also two types of Adapters:
     - **Driving Adapters**: Implement the input ports and translate user requests into commands that the Application Service can process.
     - **Driven Adapters**: Implement the output ports and translate the responses from the application into a format that external systems can use, such as saving data to a database.

## Benefits of Hexagonal Architecture

1. **Modularity**: By separating the domain logic from external systems, changes in the user interface or database do not affect the business logic.
2. **Testability**: The core logic can be tested independently without needing the actual infrastructure, making unit testing more straightforward.
3. **Flexibility**: The architecture allows you to easily swap out external systems, such as replacing a database or integrating with a new API, without changing the core logic.
4. **Scalability**: Since the architecture encourages loosely coupled components, scaling different parts of the application becomes easier.

## Pre-installation steps

>  **Before** starting the installation, you need to have a Bitbucket token to install private repositories. Each repository requires its own AccessToken. **Ask an admin for those**.

Once you have the required tokens, "install" them in your terminal. 

**MAC:**
```bash
sudo nano ~/.zshrc
```
**LINUX**:
```bash
sudo nano ~/.bashrc
```
Add as many tokens as you need. I.e:
```bash
export COMMONS_ACCESS_TOKEN=<YOUR_TOKEN>
```
Save the file and check that the token has been installed successfully. Open a new tab in your terminal and:
```bash
echo $COMMONS_ACCESS_TOKEN
```
You should see your token's value.

Now, check ```install_private_repositories.sh```, comment the repositories that are not required to be installed and change
the name of the variables to match the ones that you added to your ```.zshrc```.

```install_private_repositories.sh``` will configure your system with the AccessTokens to allow your local poetry to install those packages via git.

**Finally**, run ```make install``` (which executes ```install_private_repositories.sh```)

## How to Use This Project

1. **Install dependencies**: Ensure that all necessary Python packages are installed using the following command:

```bash
uv venv
source .venv/bin/activate
 ```

2. **Configuration**: Modify the configuration files located in the `.docker/environments` directory to set up your database, API keys, or other external dependencies.

3. **Run the application**: Start the application by running the main Python scripts:

```bash
make run-both
```

## How to Deploy This Project

1. **Create a machine in your cloud provider**: Go to Digital Ocean or AWS and create a Droplet/EC2 to deploy the code.


2. **Create a local SSH key**: In your local machine, create an SSH key to connect to the machine that you created previously

```bash
ssh-keygen -t rsa
```
   
Once the keys are generated, copy your .pub file

```bash
cat ~/.ssh/<your_key>.pub |pbcopy
```
   
3. **Link your local machine to the cloud machine**: In order to establish an SSH connection you need to register your public key in the authorized keys of you cloud machine. Once the machine is created in your cloud provider, establish a connection using the Console UI of your cloud provider and register your local public key in the remote host.

```bash
sudo nano ~/.ssh/authorized_keys
```

Paste your .pub file and save

4. **Enable Bitbucket pipelines in your repo**: Bitbucket -> Enter your repository -> Pipelines -> Turn on the switch


5. **Generate an SSH key for Bitbucket**: Go to Bitbucket -> <your_repo> -> Repository Settings -> SSH Keys -> Follow the instructions that Bitbucket prints in your screen
>  **You may need admin permissions in order to access to "Repository Settings".**

6. **Register env vars for your repository**: Go to Bitbucket -> <your_repo> -> Repository Settings -> Repository variables 
You need 3 core variables to put `bitbucket-pipelines.yml` to work.
   1. **SSH_USER**: root
   2. **STAGING_SERVER_IP**: the public IP of the host used for development
   3. **PRODUCTION_SERVER_IP**: the public IP of the host used for production
   4. **COMMONS_ACCESS_TOKEN**: a token to be used by the pipeline to install this private repository. This is different from the one for your local machine

> Point 6.iv. applies for every private repository that is going to be installed in the project

>**TODO: Step 7 must be changed from SSH key to AccessToken configuration**
7. **Configure the remote host to enable git clone**: You need to generate an SSH key in the remote host and register the .pub file in the repository on Bitbucket in order to give permissions to the machine to clone the repository
    1. **Connect to the remote host via SSH or using the Console UI of your cloud provider**
    2. **Generate an SSH key in the remote host**: Repeat **step 2** in your remote host
    3. **Register the .pub file on Bitbucket's repository**: Go to Bitbucket -> <your_repo> -> Repository Settings -> Access keys -> Add key -> Paste your .pub content and save it.


8. **Adapt bitbucket-pipelines.yml**: Ensure that your file is properly configured according to your repo (**Read the YML file, please!**)

9. **Enjoy it**: Now, as long as you push to develop or main branches, your code will be continuously integrated and delivered to the host assigned to the branch where you made the push

#### Remember
>  **You may need admin permissions in order to access to "Repository Settings" so ask some admin to help you to configure the new deployable repository.** 

## Conclusion

This Python project leverages Hexagonal Architecture to promote clean, maintainable, and scalable code. By following this architectural pattern, you can ensure that your application remains flexible and robust, even as external systems and technologies evolve. The provided image serves as a visual guide to understanding the relationships and interactions between different components in the system.




