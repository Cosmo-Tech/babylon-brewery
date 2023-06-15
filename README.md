# Babylon Actions 
(dev ref: babylon branch: ndon/deploy_test)

</br>

This repository contains the instructions on how to deploy a Asset solution based on the Cosmo Tech Platform.

## Prerequisite

* ### Setup Github Repository
---
</br>

1. Create an app registration for babylon with required permissions
2. Generate PAT Github (repo/workflows) and add it on github repository secrets
2. Add below keys on github repository secrets

    * ```AZURE_TENANT_ID```
    * ```AZURE_CLIENT_ID```
    * ```AZURE_CLIENT_SECRET```
    * ```PAT```

3. Set credentials ```AZ CLI``` on github repository secrets
    >AZ_CREDENTIALS
    ```json
    {
      "clientId": "<GUID>",
      "clientSecret": "<STRING>",
      "subscriptionId": "<GUID>",
      "tenantId": "<GUID>"
    }
    ```

</br>


* ### Config folder
---

</br>

> Complete your configuration files with required keys.

    configuration required:
        platform:
            api_url: 
            api_scope: 
            csm_platform_app_id: 
            csm_object_platform_id: 
            csm_platform_scope_id: 
            azure_subscription: 
            azure_tenant_id: 
            babylon_client_id: 
            babylon_principal_id: 
            adx_cluster_name: 
            adx_cluster_object_id: 
            resource_group_name: 
            csm_acr_registry_name: 
            acr_registry_name: 
            resources_location: 
            storage_account_name: 
            powerbi_api_scope: https://analysis.windows.net/powerbi/api/.default
            azure_powerbi_group_id: 
            azure_team_id: 
        deploy:
            workspace_key: 
            api_url: 
            resource_group_name: 
            resources_location: 
            csm_simulator_repository: 
            simulator_repository: 
            simulator_version: 
            deployment_name: 
            webapp_location: 
            webapp_organization_url: https://cosmotech.com
            twincache_graphid: 
            powerbi_api_scope: https://analysis.windows.net/powerbi/api/.default

</br>

### Template workflow
---

```yaml
name: Asset Solution Test

env:
  AZURE_TENANT_ID: ${{ secrets.AZURE_TENANT_ID }}
  AZURE_CLIENT_ID: ${{ secrets.AZURE_CLIENT_ID }}
  AZURE_CLIENT_SECRET: ${{ secrets.AZURE_CLIENT_SECRET }}

on:
  push:
    branches:
      - asset

jobs:
  asset-deploy:
    runs-on: ubuntu-latest
    env:
      dir: personal
      config_path: ./config
    steps:
      - uses: actions/checkout@v3

      - name: install babylon
        uses: Cosmo-Tech/babylon-actions/.github/actions/babylon@asset
        with: 
          branch: ndon/deploy_test
    
      - id: deploy
        name: retrieve deploy keys from local folder
        uses: mikefarah/yq@master
        with:
          cmd: yq -o=json $config_path/deploy.yaml
      - id: platform
        name: retrieve platform keys from local folder
        uses: mikefarah/yq@master
        with:
          cmd: yq -o=json $config_path/platform.yaml
    
      - name: setup babylon config
        uses: Cosmo-Tech/babylon-actions/.github/actions/config@asset
        with:
          deploy: ${{ steps.deploy.outputs.result }}
          platform: ${{ steps.platform.outputs.result }}

      - name: create a new organization
        uses: Cosmo-Tech/babylon-actions/.github/actions/organization@asset
        with:
          name: "Asset Org Cosmo Tech"
          email: <EMAIL>
          role: admin

      - name: create container storage by default
        uses: Cosmo-Tech/babylon-actions/.github/actions/storage@asset
        
      - name: get azure team id
        id: azureteam
        run: |
          cd $dir
          azure_team_id=$(babylon config get-variable platform 'azure_team_id')
          echo "azure_team_id=$azure_team_id" >> $GITHUB_OUTPUT

      - name: deploy adx database and permissions
        uses: Cosmo-Tech/babylon-actions/.github/actions/adx@asset
        with:
          team_id: ${{ steps.azureteam.outputs.azure_team_id }}

      - name: deploy adt instance and permissions
        continue-on-error: true
        uses: Cosmo-Tech/babylon-actions/.github/actions/adt@asset
        with:
          team_id: ${{ steps.azureteam.outputs.azure_team_id }}

      - name: deploy eventhub namespaces and permissions
        uses: Cosmo-Tech/babylon-actions/.github/actions/eventhub@asset
        with:
          team_id: ${{ steps.azureteam.outputs.azure_team_id }}

      - name: set pat in babylon for deploy
        uses: Cosmo-Tech/babylon-actions/.github/actions/pat@asset
        with:
          pat: ${{ secrets.PAT }}
      
      - name: retrieve sample webapp
        continue-on-error: true
        uses: Cosmo-Tech/babylon-actions/.github/actions/retrieve@asset
        with:
          repo_from: Cosmo-Tech/azure-asset-dev-webapp
          repo_tag: <ORIGIN>/<BRANCH>
          repo_to: <OWNER>/<REPO_NAME>
          repo_to_branch: <BRANCH>
          username: <USERNAME>
          email: <EMAIL>
          pat: ${{ secrets.PAT }}

      - name: Retrieve babylon variables
        id: baby_vars
        run: |
          cd $dir
          rg=$(babylon config get-variable deploy 'resource_group_name')
          org=$(babylon config get-variable deploy 'organization_id')
          wk=$(babylon config get-variable deploy 'workspace_key')
          echo "rg=$rg" >> $GITHUB_OUTPUT
          echo "org=$org" >> $GITHUB_OUTPUT
          echo "wk=$wk" >> $GITHUB_OUTPUT
          echo "adxdatabasename=$(echo $org-$wk | tr [:upper:] [:lower:])" >> $GITHUB_OUTPUT
          echo "azfname=$(echo $org-$wk | tr [:upper:] [:lower:])" >> $GITHUB_OUTPUT
          echo "namespace=$(echo $org-$wk | tr [:upper:] [:lower:])" >> $GITHUB_OUTPUT
          echo "adt=$(babylon config get-variable deploy 'digital_twin_url')" >> $GITHUB_OUTPUT
          echo "adx=$(babylon config get-variable deploy 'adx_database_name')" >> $GITHUB_OUTPUT
          echo "cadt=$(babylon config get-variable deploy 'adt_connector_id')" >> $GITHUB_OUTPUT
          echo "sadt=$(babylon config get-variable deploy 'storage_connector_id')" >> $GITHUB_OUTPUT
          echo "hostname=$(babylon config get-variable deploy 'webapp_static_domain')" >> $GITHUB_OUTPUT
          echo "dadt=$(babylon config get-variable deploy 'adt_dataset_id')" >> $GITHUB_OUTPUT
          echo "wpi=$(babylon config get-variable deploy 'webapp_principal_id')" >> $GITHUB_OUTPUT
      

      - name: deploy webapp
        continue-on-error: true
        uses: Cosmo-Tech/babylon-actions/.github/actions/webapp@asset
        with:
          powerbi: false
          azf: true

      - name: az login
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZ_CREDENTIALS }}

      - name: retrieve azf key
        id: azf
        env:
          rg: ${{ steps.baby_vars.outputs.rg }}
          azfname: ${{ steps.baby_vars.outputs.azfname }}        
        run: |
          azf_key=$(az functionapp keys list -g $rg -n $azfname --query masterKey)
          echo "azf_key=$azf_key" >> $GITHUB_OUTPUT

      - name: set azf key
        run: |
          cd $dir
          babylon config set-variable secrets azf.key ${{ steps.azf.outputs.azf_key }}

      - name: retrieve hub keys
        id: hub
        env:
          rg: ${{ steps.baby_vars.outputs.rg }}
          namespace: ${{ steps.baby_vars.outputs.namespace }}
          keyname: RootManageSharedAccessKey
        run: |
          hub_key=$(az eventhubs namespace authorization-rule keys list -g $rg --namespace-name $namespace --name $keyname --query primaryKey)
          echo "hub_key=$hub_key" >> $GITHUB_OUTPUT 

      - name: set event hub key
        run: |
          cd $dir
          babylon config set-variable secrets eventhub.key ${{ steps.hub.outputs.hub_key }}

      - name: create twin connector
        uses: Cosmo-Tech/babylon-actions/.github/actions/connector@asset
        with:
          type: twin
          name: "Asset Baby Connector Twin"

      - name: create adt connector
        uses: Cosmo-Tech/babylon-actions/.github/actions/connector@asset
        with:
          type: adt
          name: "Asset Baby Connector ADT"

      - name: create connector storage
        uses: Cosmo-Tech/babylon-actions/.github/actions/connector@asset
        with:
          type: storage
          name: "Asset Baby connector STORAGE"

      - name: create dataset adt
        uses: Cosmo-Tech/babylon-actions/.github/actions/dataset@asset
        with:
          type: adt
          name: "Asset Baby dataset ADT"

      - name: create dataset twin
        uses: Cosmo-Tech/babylon-actions/.github/actions/dataset@asset
        with:
          type: twin
          name: "Asset Baby dataset Twin"

      - name: Retrieve babylon variables
        id: baby_wpi
        run: |
          cd $dir
          echo "wpi=$(babylon config get-variable deploy 'webapp_principal_id')" >> $GITHUB_OUTPUT

      - name: add adt permission to webapp
        uses: Cosmo-Tech/babylon-actions/.github/actions/permission@asset
        with:
          pi: ${{ steps.baby_wpi.outputs.wpi }}
          ri: Microsoft.DigitalTwins/digitalTwinsInstances

      - name: create solution Asset
        uses: Cosmo-Tech/babylon-actions/.github/actions/solution@asset
        with:
          name: "Asset Solution Test"

      - name: create workspace Asset
        uses: Cosmo-Tech/babylon-actions/.github/actions/workspace@asset
        with:
          name: Asset Baby Workspace
          email: <EMAIL>

      - name: set key api
        run: |
          cd $dir
          babylon api workspace setkey

```


> References

* ### install babylon

    ```bash
    git clone -b <branch> https://github.com/Cosmo-Tech/Babylon.git; cd Babylon
    
    pip install -e .
    mkdir personal; cd personal
    ```

* ### set up working_dir

    ```bash
    echo 'export BABYLON_WORKING_DIRECTORY=.' >> ~/.bashrc
    echo 'export BABYLON_CONFIG_DIRECTORY=./config' >> ~/.bashrc
    source ~/.bashrc
    ```

* ### init commands (configuration)
    
    ```bash
    cd personal
    babylon config init
    babylon working-dir complete
    ```

</br>

Solution deployment
---

</br>

### Container image
- publish the solution container image to your platform azure container registry.

>configuration

    platform file:
        csm_acr_registry_name: <SOURCE>
        acr_registry_name: <DESTINATION>
    deploy file:
        csm_simulator_repository: <SOURCE>
        simulator_repository: <DESTINATION>
        simulator_version: <x.y.z>

>run

```bash
babylon azure acr pull -r <SOURCE>.azurecr.io
babylon azure acr push -r <DESTINATION>.azurecr.io
```

</br>

## solution object
---

>configuration

    deploy file:
        organization_id: <ORGANIZATION_ID>
        api_url: <API_URL>
        simulator_repository: <SIMULATOR>
        simulator_version: <VERSION>

    platform file:
        api_url: <API_URL>
        api_scope: <API_SCOPE>
        azure_subscription: <SUBSCRIPTION_ID>
        azure_tenant_id: <TENANT_ID>

    API: .payload_templates/api

>run

```bash
babylon api solution create 'Solution Baby Dev Solution' -i API/Solution.yaml --select
```

</br>

## Workspace object
---

>configuration (example)

    deploy file:
        solution_id: <SOLUTION_ID>
        workspace_key: <WORKSPACE_KEY>
    
    API: .payload_templates/api

>run

```bash
babylon api workspace create 'The Baby Solution Dev Workspace' -i API/workspace.yaml --select
```

</br>


## Azure digital twins 
---

>configuration

    deploy_file:
        organization_id: <ORGANIZATION_ID>
        workspace_key: <WORKSPACE_KEY>

    platform file:
        resource_group_name: <RESOURCE_GROUP_NAME>
        resources_location: <RESOURCES_LOCATION>

>run

```bash
babylon azure adt instance create -s

<!-- permissions adt-->
<!-- Azure Digital Twins Data Owner: bcd981a7-7f74-457b-83e1-cceb9e632ffe -->
<!-- Azure Digital Twins Data Reader: d57506d4-4c8d-48b1-8587-93c323f6a5a3 -->
<!-- ObjectId / PrincipalId Platform: 87267e78-0cff-4bd7-a4c5-8a68727f8cb7 -->
<!-- if -pi -> default csm_object_platform_id -->
babylon azure permission set -rt Microsoft.DigitalTwins/digitalTwinsInstances -ri bcd981a7-7f74-457b-83e1-cceb9e632ffe
babylon azure permission set -rt Microsoft.DigitalTwins/digitalTwinsInstances -ri d57506d4-4c8d-48b1-8587-93c323f6a5a3

babylon azure adt model upload dtdl/

<!-- Principal Id WebApp -->
babylon azure permission set -rt Microsoft.DigitalTwins/digitalTwinsInstances -ri bcd981a7-7f74-457b-83e1-cceb9e632ffe --select-webapp
```

</br>


## Connector azure digital twins
---

>configuration

    API: .payload_templates/api

>run

```bash
babylon api connector create 'ADT Connector Babylon' -i API/connector.adt.yaml -t adt -s
```

</br>


## Connector azure storage
---

>configuration

    API: .payload_templates/api

>run

```bash
babylon api connector create 'Storage Connector Babylon' -i API/connector.storage.yaml -t storage -s
```

</br>


## Dataset azure digital twins
---

>configuration

    API: .payload_templates/api

>run

```bash
babylon api dataset create 'ADT Dataset Babylon' -i API/dataset.adt.yaml -t adt -s
```

</br>


## Azure data explorer cluster
---

>configuration

    deploy_file:
        organization_id: <ORGANIZATION_ID>
        workspace_key: <WORKSPACE_KEY>

    platform file:
        adx_cluster_name: <ADX_CLUSTER_NAME>
        adx_cluster_object_id: <PRINCIPAL_ID>

>run

```bash
babylon azure adx database create -s
babylon azure adx script run-folder adx
<!-- permission cosmo platform ADX database : default csm_object_platform_id-->
babylon azure adx permission set -t App -r Admin

<!-- set key eventhub on workspace -->
rg=$(babylon config get-variable deploy "resource_group_name")
org=$(babylon config get-variable deploy "organization_id")
wk=$(babylon config get-variable deploy "workspace_key")
namespace=$(echo $org-$wk | tr [:upper:] [:lower:])
babylon config set-variable secrets eventhub.key $(az eventhubs namespace authorization-rule keys list -g $rg --namespace-name $namespace --name <ROOT_KEY> --query primaryKey | jq -r '')
babylon api workspace setkey
```

</br>

## Azure Event Hub namespaces
---

>configuration

    API: .payload_templates/arm

>run

```bash
babylon azure arm runtmp -f API/eventhub_deploy.json
<!-- Event Hub Namespaces permissions-->
<!-- Azure Event Hubs Data Receiver: a638d3c7-ab3a-418d-83e6-5f17a39d4fde -->
<!-- Azure Event Hubs Data Sender  : 2b629674-e913-4c01-ae53-ef4638d8f975 -->
<!-- Principal Id ADX Cluster -->
babylon azure permission set -rt Microsoft.EventHub/Namespaces -pi <ADX_CLUSTER_PRINCIPAL_ID> -ri a638d3c7-ab3a-418d-83e6-5f17a39d4fde
babylon azure permission set -rt Microsoft.EventHub/Namespaces -ri 2b629674-e913-4c01-ae53-ef4638d8f975

babylon azure adx connections create "ProbesMeasures" JSON -tn "ProbesMeasures" 
babylon azure adx connections create "ScenarioMetaData" CSV -tn "ScenarioMetadata" 
babylon azure adx connections create "ScenarioRun" JSON -tn "SimulationTotalFacts" 
babylon azure adx connections create "ScenarioRunMetaData" CSV -tn "ScenarioRunMetadata"
```

## Power bi
---

>configuration

    platform file:
        azure_powerbi_group_id: <AZURE_GROUP_ID>

>run

```bash
babylon powerbi deploy-workspace <WORKSPACE_NAME> -f <POWERBI_REPORT_PATH> -p ADX_DATABASE <DATABASE_NAME> -p ADX_CLUSTER <CLUSTER_NAME>
```

</br>

## Web app
---
Link: https://cosmo-tech.github.io/Babylon-End-User-Doc/2.0.0/commands/webapp_deploy/


>configuration

    deploy file:
        deployment_name: <DEPLOYMENT_NAME>
        webapp_location: <RESOURCE_LOCATION>
        webapp_repository: <GITHUB_REPOSITORY_URL>
        webapp_repository_branch: <BRANCH>

    platform file:
        azure_powerbi_group_id: <AZURE_GROUP_ID>


> manual operation

    - create PAT with repo and workflow scopes
    help : https://cosmo-tech.github.io/Babylon-End-User-Doc/2.1.0/commands/webapp_deploy/
   
```bash
<!-- on webapp_repository_branch -->
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
   
>run

```bash
babylon config set-variable secrets github.token <GITHUB_TOKEN>
babylon webapp deploy --enbale-powerbi --enable-azfunc --azf_path <AZURE_FUNCTION_DEPLOY_PATH>
```

</br>

```bash
├── .github
│   └── actions
│       ├── adt
│       │   └── action.yml
│       ├── adx
│       │   └── action.yml
│       ├── babylon
│       │   └── action.yml
│       ├── config
│       │   ├── action.yml
│       │   └── set_babylon_config.py
│       ├── connector
│       │   └── action.yml
│       ├── dataset
│       │   └── action.yml
│       ├── dispatch
│       │   ├── action.yml
│       │   └── dispatch.py
│       ├── eventhub
│       │   └── action.yml
│       ├── organization
│       │   └── action.yml
│       ├── pat
│       │   └── action.yml
│       ├── permission
│       │   └── action.yml
│       ├── powerbi
│       │   └── action.yml
│       ├── retrieve
│       │   └── action.yml
│       ├── solution
│       │   └── action.yml
│       ├── storage
│       │   └── action.yml
│       ├── webapp
│       │   └── action.yml
│       └── workspace
│           └── action.yml
├── .gitignore
├── .payload_templates
│   ├── api
│   │   ├── connector.adt.yaml
│   │   ├── connector.storage.yaml
│   │   ├── connector.twin.yaml
│   │   ├── dataset.adt.yaml
│   │   ├── dataset.storage.yaml
│   │   ├── dataset.twin.yaml
│   │   ├── organization.yaml
│   │   ├── send_key.yaml
│   │   ├── solution.yaml
│   │   └── workspace.yaml
│   ├── arm
│   │   ├── azf_deploy.json
│   │   └── eventhub_deploy.json
│   ├── tfc
│   │   ├── workspace_create.json
│   │   └── workspace_run.json
│   └── webapp
│       ├── app_insight.json
│       ├── app_registration.json
│       ├── webapp_config.json
│       ├── webapp_details.json
│       └── webapp_settings.json
└── README.md

```
