# Chip the Alabama Tech Community AI Agent
 
 This project uses uv as its package manager.
 
 ## Installing dependencies
 
 note you need to run uv sync if cursor / vscode are giving you errors about a missing python environment.
 ```bash
 uv sync
 ```
 
 ## Adding a new dependency
 
 ```bash
 uv add <dependency>
 ```
 
 ## Removing a dependency
 
 ```bash
 uv remove <dependency>
 ```
 
 ## Updating a dependency
 
 ```bash
 uv update <dependency>
 ```

 # Development
 Use the devcontainer for development. This will give you a fully configured environment with the correct python version and all the dependencies installed.

 To get started, open the project in VSCode/Cursor and click on the Open in Dev Container button via the command palette.
 
 ## Running the App / Debugger
 
 click on the Run and Debug icon in the left sidebar and select the api launch configuration.

 This is where you will be able to test the API locally with the /docs endpoint via swagger ui in the browser. Since the app is running in debug mode, any changes you make to the code will be reflected in the browser on refresh for the UI and on response for the API.

 ## On Commit signing

 This project is configured to not require commit signing. If you want to sign your commits run the following command in your local (non-devcontainer) terminal, fter you have commited your changes in the devcontainer.
 ```bash
 git commit --amend -S --no-edit
 ```
 This will update your last commit to be signed.


## Running tests

Click on the Tests icon in the left sidebar and select the pytest launch configuration.

# Moving to Production/Staging

TBD

## Starting the app on Railway in Production

Go to Railway and click on the Deploy button or push to the Main branch.
