# Babylon Actions 

This repository contains all the necessary actions and instructions on how to deploy an Asset solution based on the Cosmo Tech Platform using the latest version of Babylon.

## Prerequisite

### Template workflow
---
This is an example template illustrating how we can use these actions in our workflows for deploying our solution. You can find more details about these workflows in this repository : [https://github.com/Cosmo-Tech/asset-azure-deployment](https://github.com/Cosmo-Tech/asset-azure-deployment/blob/master/README.md)

```yaml
name: Asset Solution Deploy

env:
  BABYLON_SERVICE: ${{ vars.BABYLON_SERVICE }}
  BABYLON_TOKEN: ${{ secrets.BABYLON_TOKEN }}
  BABYLON_ORG_NAME: ${{ vars.BABYLON_ORG_NAME }} 
  BABYLON_ENCODING_KEY: ${{ secrets.BABYLON_ENCODING_KEY_PERF }}
  GITHUB_PAT: ${{ secrets.PAT }}

on:
  workflow_dispatch:
    inputs:
      context_id:
        description: 'Select CONTEXT_ID'
        required: true
        default: 'asset'
        type: string
        enum:
          - 'asset'
          - 'performance_mona-dev'
      platform_id:
        description: 'Select PLATFORM_ID'
        required: true
        default: 'dev'
        type: string
        enum:
          - 'dev'
          - 'perf'
          - 'staging'
  push:
    branches:
      - master
  pull_request:
    branches:
      - master 
jobs:
  asset-deploy:
    runs-on: ubuntu-latest
    env:
      dir: personal
      config_path: ./config
      CONTEXT_ID: ${{ github.event.inputs.context_id || 'performance_mona-dev' }}
      PLATFORM_ID: ${{ github.event.inputs.platform_id || 'perf' }}
    steps:
      - name: 🎯 Checkout Code
        uses: actions/checkout@v3

      - name: 🛠 Install Babylon
        uses: Cosmo-Tech/babylon-actions/.github/actions/babylon@asset

      - name: ⚙️ Setup Basic Configuration
        uses: Cosmo-Tech/babylon-actions/.github/actions/set-variables@asset
        with: 
          email: example@cosmotech.com
          user_principal_id: 
          workspace_key: 
          team_id: 
          simulator_image_docker: 
          simulator_version: 
          uri_artifact_zip: 
          deployment_name: 
          location: 
          repo_to: 
          branch_to: 
          organization: Cosmo-Tech
          api_url: https://perf.api.cosmotech.com/v2 
          api : ""
          item: ""
          
      - name: 🏢 Create a New Organization
        uses: Cosmo-Tech/babylon-actions/.github/actions/organization@asset
        with:
          name: "RTE"
          email: example@cosmotech.com
          role: admin

      - name: 📦 Create Container Storage by Default
        uses: Cosmo-Tech/babylon-actions/.github/actions/storage@asset

      - name: 🚀 Deploy ADX Database and Permissions
        uses: Cosmo-Tech/babylon-actions/.github/actions/adx@asset

      - name: 🚀 Deploy Eventhub Namespaces and Permissions
        uses: Cosmo-Tech/babylon-actions/.github/actions/eventhub@asset
        with:
          name: "Asset_Eventhub_Deploy"

      - name: 🔐 Azure Login
        uses: Azure/login@v1
        with:
          creds: '{"clientId":"${{ vars.CLIENT_ID }}","clientSecret":"${{ secrets.CLIENT_SECRET }}","subscriptionId":"${{ vars.SUBSCRIPTION_ID }}","tenantId":"${{ vars.TENANT_ID }}"}'
            
      - name: 🔐 Authentication Eventhub Configuration
        uses: Cosmo-Tech/babylon-actions/.github/actions/eventkey@asset
        with:
          resource_group: phoenixperf

      - name : 🔍 Generate Workspace Name
        id : GWN
        run : |
            WNDASH=$(date "+%Y-%m-%d_%H:%M:%S")_$(head /dev/urandom | tr -dc 'a-zA-Z0-9' | head -c 3)
            echo "WNDASH=$WNDASH" >> $GITHUB_OUTPUT
            WNSENA=$(date "+%Y-%m-%d_%H:%M:%S")_$(head /dev/urandom | tr -dc 'a-zA-Z0-9' | head -c 3)
            echo "WNSENA=$WNSENA" >> $GITHUB_OUTPUT

      - name : 📊 Deploy Workspace PowerBI 
        uses : Cosmo-Tech/babylon-actions/.github/actions/powerbi@asset
        with:
          workspace_name_dashboard: rte-pilote-delivery-perf_${{ steps.GWN.outputs.WNDASH }}
          workspace_name_scenario: rte-pilote-delivery-perf_${{ steps.GWN.outputs.WNSENA }}

      - name: 📥 Retrieve Sample WebApp
        uses: Cosmo-Tech/babylon-actions/.github/actions/retrieve@asset
        with:
          repo_from: Cosmo-Tech/webapp-asset-demo
          branch_from: upstream/deployment/delivery-rte-performance
          repo_to: Cosmo-Tech/azure-webapp-asset-qa
          branch_to: dev/asset 
          username: user
          email: example@cosmotech.com
      
      - name: 🔄 Increment Deployment Name Field
        id: idnf
        run: |
            cd ${{ env.dir }}
            deployment_name=$(babylon config get -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }} webapp deployment_name)
            random_string=$(head /dev/urandom | tr -dc 'a-zA-Z0-9' | head -c 3)
            new_deployment_name=${deployment_name}_${random_string}
            babylon config set -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }} webapp deployment_name $new_deployment_name

      - name: 🚀 Deploy WebApp
        uses: Cosmo-Tech/babylon-actions/.github/actions/webapp@asset
            
      # - name: 📥 Retrieve Azure Function Key
      #   uses: Cosmo-Tech/babylon-actions/.github/actions/azurefunctionkey@asset
      #   with:
      #     resource_group: phoenixperf

      - name: 📦 Create Connector Storage
        uses: Cosmo-Tech/babylon-actions/.github/actions/connector@asset
        with:
          type: storage
          version: 1.1.2
          name: "Asset_Connector_AZURE_STORAGE"

      - name : 📄 Copy The Templates to The Babylon Env
        run: |
            if [ "${{ env.PLATFORM_ID }}" == "dev" ]; then
              cp $config_path/dev/dataset.storage.yaml ${{ env.dir }}/.payload/${{ env.CONTEXT_ID }}.dev.dataset.storage.yaml
              cp $config_path/dev/solution.yaml ${{ env.dir }}/.payload/${{ env.CONTEXT_ID }}.dev.solution.yaml
            elif [ "${{ env.PLATFORM_ID }}" == "perf" ]; then
              cp $config_path/perf/dataset.storage.yaml ${{ env.dir }}/.payload/${{ env.CONTEXT_ID }}.perf.dataset.storage.yaml
              cp $config_path/perf/solution.yaml ${{ env.dir }}/.payload/${{ env.CONTEXT_ID }}.perf.solution.yaml
            elif [ "${{ env.PLATFORM_ID }}" == "staging" ]; then
              cp $config_path/staging/dataset.storage.yaml ${{ env.dir }}/.payload/${{ env.CONTEXT_ID }}.staging.dataset.storage.yaml
              cp $config_path/staging/solution.yaml ${{ env.dir }}/.payload/${{ env.CONTEXT_ID }}.staging.solution.yaml
            else
              echo "Unsupported PLATFORM_ID: ${{ env.PLATFORM_ID }}"
              exit 1 
            fi

      - name: 📦 Create Dataset Storage
        uses: Cosmo-Tech/babylon-actions/.github/actions/dataset@asset
        with:
          type: storage
          name: "Asset_Baby_dataset_STORAGE" 
            
      - name: 📦 Create Solution Asset
        uses: Cosmo-Tech/babylon-actions/.github/actions/solution@asset
        with:
          name: WP03-Overhead_lines_b

      - name: 🏢 Create Workspace Asset
        uses: Cosmo-Tech/babylon-actions/.github/actions/workspace@asset
        with:
          name: WP03-Overhead_lines_b
          email: example@cosmotech.com
          role: admin

      - name: 📤 Upload CSV File Asset
        uses: Cosmo-Tech/babylon-actions/.github/actions/upload_dataset@asset
      
      - name: 📤 Upload Handlers Zip
        uses: Cosmo-Tech/babylon-actions/.github/actions/upload_handlers@asset
        with: 
          item: WP03_RunTemplate

```
Actions
---
> References

- [https://cosmo-tech.github.io/Babylon-End-User-Doc/3.1.0/guides/](https://cosmo-tech.github.io/Babylon-End-User-Doc/3.1.0/guides/)

- [https://github.com/Cosmo-Tech/asset-azure-deployment](https://github.com/Cosmo-Tech/asset-azure-deployment/blob/master/README.md)

### Install Babylon
---
This action will install `Babylon` with all requirements, and the init command will create all configuration files. For more details, check this link: [https://cosmo-tech.github.io/Babylon-End-User-Doc/3.1.0/guides/](https://cosmo-tech.github.io/Babylon-End-User-Doc/3.1.0/guides/getting_started/)
```bash
git clone https://github.com/Cosmo-Tech/Babylon.git babylon;cd babylon
pip install -e . --quiet
```
### init commands (configuration)
    
```bash
mkdir personal
cd personal
babylon config init -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }}
```

### Set up the configuration (set-varaibles action)
---

This action sets up all the necessary variables for deploying our solution, such as:
  -  `email`
  -  `user_principal_id`
  -  `workspace_key`
  -  `team_id`
  -  `simulator_repository`
  -  `simulator_version`
  -  `function_artifact_url` 
  -  `deployment_name` 
  -  `location` 
  -  `organization` 
  -  `repository` 
  -  `run_templates` 
  -  `api url` 

>run

```bash
babylon config set azure email "${{ inputs.email }}" -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }}

babylon config set azure user_principal_id "${{ inputs.user_principal_id }}" -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }}

babylon config set api workspace_key "${{ inputs.workspace_key }}" -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }}

babylon config set powerbi dashboard_view -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }}

babylon config set powerbi scenario_view -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }}

babylon config set azure team_id "${{ inputs.team_id }}" -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }}

babylon config set acr simulator_repository "${{ inputs.simulator_image_docker }}" -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }}

babylon config set acr simulator_version "${{ inputs.simulator_version }}" -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }}

babylon config set azure function_artifact_url "${{ inputs.uri_artifact_zip }}" -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }}

babylon config set webapp deployment_name "${{ inputs.deployment_name }}" -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }}

babylon config set webapp location "${{ inputs.location }}" -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }}

babylon config set github branch "${{ inputs.branch_to }}" -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }}

babylon config set github organization "${{ inputs.organization }}" -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }}

babylon config set github repository "${{ inputs.repo_to }}" -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }}

babylon config set api run_templates -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }} --item ${{ inputs.item }}

babylon config set -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }} api url ${{ inputs.api_url }}
```

## Create an Organization (organization action)

This action will create an organization with a default name, such as `o-mmv8evy0x69`.

>run

```bash
babylon api organizations payload create -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }}

babylon api organizations create "${{ inputs.name }}" -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }}

babylon api organizations security add -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }} --email ${{ inputs.email }} --role ${{ inputs.role }}
```

## Create a Blob Storage (storage action)

This action will create a Blob storage container with the same name as the organization to store the dataset.

>run

```bash
organization_id=$(babylon config get -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }} api organization_id)

babylon azure storage container create $organization_id -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }}

babylon azure iam set -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }} --resource-type "Microsoft.Storage/storageAccounts" --role-id %azure%storage_blob_reader --principal-id %azure%team_id --principal-type Group --resource-name %azure%storage_account_name

babylon azure iam set -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }} --resource-type "Microsoft.Storage/storageAccounts" --role-id %azure%storage_blob_reader --principal-id %platform%principal_id --resource-name %azure%storage_account_name
```

### Azure Data Explorer database (adx action) 
---

The `ADX action` creates an adx databese it depends on the `file.kql` that is located in the `adx` directory. The adx directory contains three subdirectories, this is how it is structured:

```bash
.
├── adx
│   ├── dev
│   │   └── Create.kql
│   ├── perf
│   │   └── 00-Initialisation_ASSET.kql
│   └── staging
```

>run

```bash
- name: Azure Data Explorer deployment
  env:
    ADX: ${{ github.action_path }}/../../../adx/${{ env.PLATFORM_ID }}
    run: |
       babylon azure adx database create -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }}

       babylon azure adx permission set -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }} --principal-type User --role Admin %azure%user_principal_id  
       
       babylon azure adx permission set -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }} --principal-type Group --role Admin %azure%team_id
       
       babylon azure adx permission set -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }} --principal-type App --role Admin %platform%principal_id
      
       babylon azure adx script run-folder $ADX -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }}
```

## Create a EventHub (eventhub action)

This action will create an Event Hub with all necessary permissions, consumer groups, and data connections : `ProbesMeasures`, `ScenarioMetadata`, `SimulationTotalFacts`, and `ScenarioRunMetadata`.

## Authentication Eventhub configuration (eventkey action)

This action will retrieve an Event Hub shared access key and save this secret in the vault.

>run

```bash
eventkey=$(az eventhubs namespace authorization-rule keys list -g ${{ inputs.resource_group }} --namespace-name $database_name --name RootManageSharedAccessKey --query primaryKey)

babylon hvac set project eventhub $eventkey -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }}
```

## PowerBI Deploy Workspace (powerbi action)

This action will deploy a Power BI workspace. It depends on the Power BI report and scenarios located in the `powerbi` directory. The powerbi directory contains two subdirectories, `dashboard` and `scenario`. This is how it is structured:

```bash
├── powerbi
│   ├── dashboard
│   │   ├── dev
│   │   │   └── asset_dev_dashboard.pbix
│   │   ├── perf
│   │   │   ├── RTEAzure-PowerBiDatasetView.pbix
│   │   │   ├── RTEAzure-PowerBiSimulationBudgetAnalysis.pbix
│   │   │   ├── RTEAzure-PowerBiSimulationEquipmentAnalysis.pbix
│   │   │   ├── RTEAzure-PowerBiSimulationOPEXCAPEXAnalysis.pbix
│   │   │   ├── RTEAzure-PowerBiSimulationScenarioComparison.pbix
│   │   │   └── RTEAzure-PowerBiSimulationScenariosOverview.pbix
│   │   └── staging
│   └── scenario
│       ├── dev
│       │   └── Asset_Staging_Demo_Dashboard_Baseline.pbix
│       ├── perf
│       │   └── RTEAzure-PowerBiScenarioView.pbix
│       └── staging
```

>run

```bash
- name: PowerBI deployment
  env:
    powerbi_dashboard_view: ${{ github.action_path }}/../../../powerbi/dashboard/${{ env.PLATFORM_ID }}
    
    powerbi_scenario_view: ${{ github.action_path }}/../../../powerbi/scenario/${{ env.PLATFORM_ID }}
  run: |
    cd ${{ inputs.folder }}
    
    babylon powerbi workspace deploy "${{ inputs.workspace_name_dashboard }}" -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }} --type dashboard_view --folder $powerbi_dashboard_view/ --override --parameter Database %adx%database_name --parameter Kusto %adx%cluster_uri
    
    babylon powerbi workspace deploy "${{ inputs.workspace_name_scenario }}" -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }} --type scenario_view --folder $powerbi_scenario_view/ --override --parameter Database %adx%database_name --parameter Kusto %adx%cluster_uri
```

## Retrieve a Simple Web App (retrieve action)

This action will retrieve a simple web app. This process requires a GitHub repository with the destination branch already created. Follow these steps:
- create a new repository in Github
- configure your branch <BRANCH> with code source 

> run

```bash
git config --global pull.rebase true
git config --global init.defaultBranch main
git config --global user.name <USERNAME>
git config --global user.email <EMAIL>
cd <BABYLON_WORKING_DIR> ; mkdir webapp; cd webapp
git init
echo "# empty_webapp" >> README.md
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin https://Cosmo-Tech:<PAT>@github.com/<REPO_SOURCE>.git
git remote add upstream https://oauth2:<PAT>@github.com/<REPO_DESTINATION>.git
git remote set-url upstream --push "NO"
git fetch --all
git checkout -B <BRANCH_REPO_DESTINATION> <TAG_REPO_SOURCE>
rm -r .github/
git add .; git commit -m 'first commit'
git push origin <BRANCH_REPO_DESTINATION> -f
```

## Web App Deploy (webapp action)

This action will use the macro command to create a static web app and configure it with the source code for the web app.

This includes:
- Creating and configuring an Azure Static WebApp resource
- Creating and configuring an Azure Active Directory App Registration
- Configuring the WebApp source code
- Adding access to the PowerBI Workspace

>run

```bash
babylon webapp deploy -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }} 
  
babylon powerbi workspace user add -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }} %app%principal_id App Admin

babylon azure iam set -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }} --resource-type Microsoft.EventHub/Namespaces --role-id%azure%eventhub_built_data_sender --principal-id %app%principal_id 
```
`Note` : In this case, we deploy our web app without Azure Functions, and if you need Azure Functions, you should add this option to the command :
>run
```bash
babylon webapp deploy -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }} --with-azf
```

## Create a Connector (connector action)

This action will create a connector depending on the specified type, such as `storage`, `adt`, or `twin` connector and version.

>run

```bash
babylon api connectors payload create -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }} --type $type

babylon api connectors create "$name" -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }} --type $type --version $version 
```

## Create a Dataset (dataset action)

This action will create a dataset depending on the specified type, such as `storage`, `adt`, or `twin` dataset. It will also update the payload file by adding the correct path to all CSV files using the `sed` command.

>run

```bash
babylon api datasets create "$name" -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }} --type $type --output .payload/${{ env.CONTEXT_ID }}.${{ env.PLATFORM_ID }}.dataset.storage.yaml 

dataset_id=$(babylon config get -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }} api dataset.storage_id)

sed -i "s/%DATASET%/$dataset_id/g" .payload/${{ env.CONTEXT_ID }}.${{ env.PLATFORM_ID }}.dataset.storage.yaml

babylon api datasets update -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }} --file .payload/${{ env.CONTEXT_ID }}.${{ env.PLATFORM_ID }}.dataset.storage.yaml --type $type $dataset_id
```

## Create a Solution (solution action)

This action will create a solution.

```bash
babylon api solutions create "${{ inputs.name }}" -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }}
```

## Create a Workspace (workspace action)

This action will create a workspace, add the specified user as an admin in this workspace, and register the Event Hub key in the workspace.

```bash
babylon api workspaces payload create -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }}

babylon api workspaces create "${{ inputs.name }}" -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }}

babylon api workspaces security add -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }} --email ${{ inputs.email }} --role ${{ inputs.role }}

babylon api workspaces send-key -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }}
```

### Upload all CSV files (upload_dataset action)
---

The `upload_dataset` action uploads all CSV files to a blob container. It depends on all CSV files that are zipped in the `dataset` directory. The dataset directory contains three subdirectories. This is how it is structured:

```bash
├── dataset
│   ├── dev
│   │   └── AZURE_REF_DATASETS.zip
│   ├── perf
│   │   └── AZURE_REF_DATASETS.zip
│   └── staging
```

>run

```bash
- name: Upload dataset
  env:
    DATASET: ${{ github.action_path }}/../../../dataset/${{ env.PLATFORM_ID }}
  run: |
    cd ${{ inputs.folder }}
    unzip $DATASET/AZURE_REF_DATASETS.zip
    
    babylon azure storage container upload -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }} --folder ./AZURE_REF_DATASETS
```

### Upload handlers (upload_handlers action)
---

3 handlers are executed in `cloud` mode, meaning outside the Docker image of the simulator: `parameter handler`, `prerun`, and `postrun`. They need to be deployed on the platform. The `upload_handlers` depends on parameter handler, prerun, and postrun, that are zipped in the `handlers` directory. The handlers directory contains three subdirectories. This is how it is structured:

```bash
├── handlers
│   ├── dev
│   ├── perf
│   │   ├── parameters_handler.zip
│   │   ├── postrun.zip
│   │   └── prerun.zip
│   └── staging
```

>run

```bash
- name: Upload handlers
  env:
    HANDLERS: ${{ github.action_path }}/../../../handlers/${{ env.PLATFORM_ID }}
  run: |
    cd ${{ inputs.folder }}
    babylon api solutions handler upload --run-template ${{ inputs.item }} -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }} parameters_handler $HANDLERS/parameters_handler.zip
    
    babylon api solutions handler upload --run-template ${{ inputs.item }} -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }} prerun $HANDLERS/prerun.zip
    
    babylon api solutions handler upload --run-template ${{ inputs.item }} -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }} postrun $HANDLERS/postrun.zip
```

### Retrieve azure function key (eventkey action)
---

This action is used to retrieve the Azure Function key. 
`Note`: that it can only be used if we deploy our web app with Azure Functions. In this case, when the function key is required, we can use this action to retrieve it and save it in the vault.

>run

```bash
database_name=$(babylon config get -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }} adx database_name) 

eventkey=$(az eventhubs namespace authorization-rule keys list -g ${{ inputs.resource_group }} --namespace-name $database_name --name RootManageSharedAccessKey --query primaryKey)

babylon hvac set project eventhub $eventkey -c ${{ env.CONTEXT_ID }} -p ${{ env.PLATFORM_ID }}
```

### Project Tree
---
This is how the project is structured, presenting all the actions and directories to provide an overview.

```bash
.
├── adx
│   ├── dev
│   │   └── Create.kql
│   ├── perf
│   │   └── 00-Initialisation_ASSET.kql
│   └── staging
├── dataset
│   ├── dev
│   │   └── AZURE_REF_DATASETS.zip
│   ├── perf
│   │   └── AZURE_REF_DATASETS.zip
│   └── staging
├── .github
│   └── actions
│       ├── Access_control
│       │   └── action.yml
│       ├── adx
│       │   └── action.yml
│       ├── azurefunctionkey
│       │   └── action.yml
│       ├── babylon
│       │   └── action.yml
│       ├── connector
│       │   └── action.yml
│       ├── dataset
│       │   └── action.yml
│       ├── dispatch
│       │   ├── action.yml
│       │   └── dispatch.py
│       ├── eventhub
│       │   └── action.yml
│       ├── eventkey
│       │   └── action.yml
│       ├── organization
│       │   └── action.yml
│       ├── powerbi
│       │   └── action.yml
│       ├── retrieve
│       │   └── action.yml
│       ├── set-variables
│       │   └── action.yml
│       ├── solution
│       │   └── action.yml
│       ├── storage
│       │   └── action.yml
│       ├── upload_dataset
│       │   └── action.yml
│       ├── upload_handlers
│       │   └── action.yml
│       ├── webapp
│       │   └── action.yml
│       └── workspace
│           └── action.yml
├── handlers
│   ├── dev
│   ├── perf
│   │   ├── parameters_handler.zip
│   │   ├── postrun.zip
│   │   └── prerun.zip
│   └── staging
├── powerbi
│   ├── dashboard
│   │   ├── dev
│   │   │   └── asset_dev_dashboard.pbix
│   │   ├── perf
│   │   │   ├── RTEAzure-PowerBiDatasetView.pbix
│   │   │   ├── RTEAzure-PowerBiSimulationBudgetAnalysis.pbix
│   │   │   ├── RTEAzure-PowerBiSimulationEquipmentAnalysis.pbix
│   │   │   ├── RTEAzure-PowerBiSimulationOPEXCAPEXAnalysis.pbix
│   │   │   ├── RTEAzure-PowerBiSimulationScenarioComparison.pbix
│   │   │   └── RTEAzure-PowerBiSimulationScenariosOverview.pbix
│   │   └── staging
│   └── scenario
│       ├── dev
│       │   └── Asset_Staging_Demo_Dashboard_Baseline.pbix
│       ├── perf
│       │   └── RTEAzure-PowerBiScenarioView.pbix
│       └── staging
├── .gitignore
├── LICENSE.md
└── README.md
```
