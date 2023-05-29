# Babylon Actions 

This repository contains all the necessary actions and instructions on how to deploy a solution based on the Cosmo Tech Platform using the latest version of Babylon (v4).

## Project Tree
This is how the project is structured, presenting all the actions and the macro `apply`action for the from-scratch deployment or macro`destroy` action for destroy all the main resources created by the Babylon apply command.

```bash
.
├── .github
│   └── actions
│       ├── acr_pull
│       │   └── action.yml
│       ├── acr_push
│       │   └── action.yml
│       ├── apply
│       │   └── action.yml
│       ├── apply_dataset
│       │   └── action.yml
│       ├── apply_organization
│       │   └── action.yml
│       ├── apply_solution
│       │   └── action.yml
│       ├── apply_workspace
│       │   └── action.yml
│       ├── destroy
│       │   └── action.yaml
│       ├── install_babylon
│       │   └── action.yml
│       └── namespace
│           └── action.yml
├── .gitignore
├── LICENSE.md
└── README.md
```
## Template workflow
This is an example of the template illustrating how you can use these actions in your workflows for deploying your Cosmo-Tech solution.

```yaml
name: CI/CD Solution 

env:
  BABYLON_SERVICE: ${{ vars.BABYLON_SERVICE }}
  BABYLON_TOKEN: ${{ secrets.BABYLON_TOKEN }}
  BABYLON_ORG_NAME: ${{ vars.BABYLON_ORG_NAME }}

on:
  workflow_dispatch:
  push:
    branches:
      - main
jobs:
  solution-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: 🎯 Checkout Code Source 
        uses: actions/checkout@v3

      - name: 🛠 Install Babylon v4
        uses: Cosmo-Tech/babylon-actions/.github/actions/install_babylon@v4
        with:
          branch: main
        
      - name: 🛠 Set namespace Babylon v4
        uses: Cosmo-Tech/babylon-actions/.github/actions/namespace@v4
        with:
          CONTEXT_ID: demo
          PLATFORM_ID: dev
          STATE_ID: demostateid
      
      - name : 📥 Pull solution image from Azure container registry
        uses: Cosmo-Tech/babylon-actions/.github/actions/acr_pull@v4
        with:
          platform: dev
          docker_simulator_image: brewery_for_continuous
          docker_simulator_version: latest
      
      - name : 🐳 Push solution image to Azure container registry on different Cosmo-Tech platforms
        uses: Cosmo-Tech/babylon-actions/.github/actions/acr_push@v4
        with:
          platforms: "perf, staging"
          docker_simulator_image: brewery_for_continuous
          docker_simulator_version: latest

      - name: 🏢 Deploy Cosmo Tech solution
        uses: Cosmo-Tech/babylon-actions/.github/actions/apply@v4
        with: 
          directory_project: project  

      - name: 🏢 Destroy Cosmo Tech solution
        uses: Cosmo-Tech/babylon-actions/.github/actions/destroy@v4
        with: 
          confirmation : false    
```
Actions
---
> References
- [https://cosmo-tech.github.io/Babylon-End-User-Doc/latest/](https://cosmo-tech.github.io/Babylon-End-User-Doc/latest)

## 1- Install Babylon (Install_babylon action)
This action will be responsible for installing Babylon v4: 

>run

```yaml
- name: install babylon packages
  run: |
    git clone -b ${{ inputs.branch }} https://github.com/Cosmo-Tech/Babylon.git babylon;cd babylon
    pip install . --quiet
  shell: bash
```
## 2- Initialize Babylon (namespace action)
This action will be responsible for initializing Babylon v4 and creating the `namespace.yaml` file containing the context and platform configuration.
It takes the following parameters provided by the integrator, such as:
- `CONTEXT_ID`: a name chosen by the integrator.
- `PLATFORM_ID`: a platform ID such as dev, staging, perf, etc.
- `STATE_ID`: a state to identify your deployment.

>run

```yaml
- name: setup namesapce babylon
  run: |
      babylon namespace use -c ${{ inputs.CONTEXT_ID }} -p ${{ inputs.PLATFORM_ID }} -s ${{ inputs.STATE_ID }}
  shell: bash
```
## 3- Pull solution image from Azure container registry (acr_pull action)
This action will be responsible for pulling the image Cosmo-Tech solution from the Cosmo-Tech platform specified by the integrator after a modulor makes it available in the ACR ( Azure container registry ) of the specified platform. It takes the following parameters:
- `platform` : The platform from which you want to perform the pull action.
- `docker_simulator_image` : The repository of images you want to pull from.
- `docker_simulator_version` : The version of the Docker image solution you want to pull.

>run

```yaml
- name: Pull simulator image from Azure Container Registry 
  run: |
      babylon azure acr pull --image ${{ inputs.docker_simulator_image }}:${{ inputs.docker_simulator_version }}
  shell: bash
```

## 4- Push solution image to Azure container registry (acr_push action)

This action will be responsible for pushing the image Cosmo-Tech solution to the all Cosmo-Tech platforms specified by the integrator. It takes the following parameters:
- `platforms` : The platforms to which you want to perform the push action.
- `docker_simulator_image` : The repository of images you want to push from.
- `docker_simulator_version` : The version of the Docker image solution you want to push.

>run

```yaml
- name: Push simulator image to Azure Container Registry
  run: |
      IFS=',' read -ra platforms_array <<< "${{ inputs.platforms }}"
      for platform in "${platforms_array[@]}"; do
        cleaned_platform=$(echo "$platform" | sed 's/ *//g')
        babylon azure acr push --image ${{ inputs.docker_simulator_image }}:${{ inputs.docker_simulator_version }} -p $cleaned_platform
      done
  shell: bash
```

## 5- Deploy the solution using a macro command apply Babylon v4
This action will be responsible to deploy the Cosmo-Tech solution from scratch with all the necessary resources. You just need to specify to this action the directory that contains all deployment files describing the specifications of the deployment.<br>
<span style="color: red;">Note</span> : This action takes as a parameter the name of the directory provided by the integrator.
>run

```yaml
- name: Babylon apply command
  env:
    directory: ${{ github.workspace }}/${{ inputs.directory_project }}
  run: |
    babylon apply $directory/
  shell: bash
```
## 6- Destroy the Cosmo Tech solution using a macro command destroy Babylon v4
This action will destroy all the main resources created by the Babylon apply command.<br>
<span style="color: red;">Note</span> : This action takes as a parameter the confirmation to destroy the solution.

>run

```yaml
- name: Babylon destroy command
  if: ${{ inputs.confirmation == 'true'}}
  run: |
    babylon destroy
  shell: bash
```

## Unitary Babylon action

Next to the Macro action, there's an apply for individual actions. You can say it's for the user who wants to deploy each API object separately, for example, deploying just an organization or a solution etc. This is the opposite of Macro apply command, which deploys all resources.

>Actions

### 1- Create or update an Organization (API Object)

This action will create or update an organization with a default name, depending on the `organization.yaml` file located in the repository where the user runs the workflows.

>run

```yaml
- name: Create or update organization object
  env:
    path_organization: ${{ github.workspace }}/organizations/organization.yaml
  run: |
    babylon api organizations apply --payload-file $path_organization
  shell: bash
```
### 2- Create or update a Solution (API Object)

This action will create or update a solution that depends on the `solution.yaml` file located in the repository where the user runs the workflows.

>run

```yaml
- name: Create or update solution object
  env:
    path_solution: ${{ github.workspace }}/solutions/solution.yaml
  run: |
     babylon api solutions apply --payload-file $path_solution
  shell: bash
```
### 3- Create or update a Workspace (API Object)

This action will create or update a workspace that depends on the `workspace.yaml` file located in the repository where the user runs the workflows.

>run

```yaml
- name: Create or update workspace object
  env:
    path_workspace: ${{ github.workspace }}/workspaces/workspace.yaml
  run: |
      babylon api workspaces apply --payload-file $path_workspace
  shell: bash
```