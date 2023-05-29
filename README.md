# Github Babylon Action Cosmo Tech Solution - DEV

This repository contains the instructions on how to deploy a brewery solution based on the Cosmo Tech Platform.

## Pre-requisite

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
        deploy:
            - api_url
            - api_scope
            - csm_platform_app_id
            - csm_principal_app_id
            - csm_platform_scope_id
            - csm_acr_registry_name
            - acr_registry_name
            - azure_subscription
            - azure_tenant_id
            - azure_client_id
            - babylon_principal_id
            - adx_cluster_name
            - adx_cluster_object_id
            - resource_group_name
            - resources_location
            - storage_account_name
            - azure_powerbi_group_id
        deploy:
            - api_url
            - resource_group_name
            - resources_location
            - csm_simulator_repository
            - simulator_repository
            - simulator_version


</br>

### Template workflow
---

```yaml
name: Brewery Solution 

env:
  AZURE_TENANT_ID: ${{ secrets.AZURE_TENANT_ID }}
  AZURE_CLIENT_ID: ${{ secrets.AZURE_CLIENT_ID }}
  AZURE_CLIENT_SECRET: ${{ secrets.AZURE_CLIENT_SECRET }}

on:
  push:
    branches: 
      - "babylon"
      
jobs:
  babylon-deploy:
    runs-on: ubuntu-latest
    env:
      email: nibaldo.donoso@cosmotech.com  
      username: nibaldo  
      dir: personal
      config_path: ./config
      repo_from: Cosmo-Tech/azure-sample-webapp
      repo_tag: v5.0.0
      repo_to: Cosmo-Tech/nibaldo_test
      repo_to_branch: deploy/testmarket
    steps:
      - uses: actions/checkout@v3

      - name: install babylon
        uses: babylon-actions/.github/actions/babylon@main
    
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
        uses: babylon-actions/.github/actions/config@main
        with:
          deploy: ${{ steps.deploy.outputs.result }}
          platform: ${{ steps.platform.outputs.result }}


      - name: deploy adx database and permissions
        uses: babylon-actions/.github/actions/adx@main

      - name: deploy adt instance and permissions
        uses: babylon-actions/.github/actions/adt@main

      - name: Retrieve babylon variables
        id: baby_adx_cluster_id
        run: |
          cd $dir
          adx_cluster_pi=$(babylon config get-variable platform "adx_cluster_object_id")
          echo "adx_cluster_pi=$adx_cluster_pi" >> GITHUB_OUTPUT

      - name: deploy eventhub namespaces and permissions
        uses: babylon-actions/.github/actions/eventhub@main
        with:
          adx_cluster_object_id: ${{ steps.baby_adx_cluster_id.outputs.adx_cluster_pi  }}


      - name: set pat in babylon for deploy
        uses: babylon-actions/.github/actions/pat@main
        with:
          pat: ${{ secrets.PAT }}
      
      - name: retrieve sample webapp
        uses: babylon-actions/.github/actions/retrieve@main
        with:
          repo_from: $repo_from
          repo_tag: $repo_tag
          repo_to: $repo_to
          repo_to_branch: $repo_to_branch
          username: $username
          email: $email
          pat: ${{ secrets.PAT }}

      - name: deploy webapp
        uses: babylon-actions/.github/actions/webapp@main
        with:
          powerbi: true
          azf: true

      - name: az login
        uses: azure/login@v1
        with:
          cred: ${{ secrets.AZ_CREDENTIALS }}

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
          echo "azfname=$(echo $org-$wk | tr [:upper:] [:lower:])" >> $GITHUB_OUTPUT
          echo "namespace=$(echo $org-$wk | tr [:upper:] [:lower:])" >> $GITHUB_OUTPUT
          echo "adt=$(babylon config get-variable deploy 'digital_twin_url')" >> $GITHUB_OUTPUT
          echo "adx=$(babylon config get-variable deploy 'adx_database_name')" >> $GITHUB_OUTPUT
          echo "cadt=$(babylon config get-variable deploy 'adt_connector_id')" >> $GITHUB_OUTPUT
          echo "sadt=$(babylon config get-variable deploy 'storage_connector_id')" >> $GITHUB_OUTPUT
          echo "hostname=$(babylon config get-variable deploy 'webapp_static_domain')" >> $GITHUB_OUTPUT
          echo "dadt=$(babylon config get-variable deploy 'adt_dataset_id')" >> $GITHUB_OUTPUT
          echo "wpi=$(babylon config get-variable deploy 'webapp_principal_id')" >> $GITHUB_OUTPUT

      - name: get azf key
        id: azf
        uses: sergeysova/jq-action@v2
        with:
          cmd: az functionapp keys list -g $rg -n ${{ steps.baby_vars.outputs.azfname }} --query masterKey | jq -r ''
      - name: set azf key
        run: |
          cd $dir
          babylon cofig set-variable secrets azf.key ${{ steps.azf.outputs.result }}

      - name: get event hub key
        id: hub
        uses: sergeysova/jq-action@v2
        env:
          rg: ${{ steps.baby_vars.outputs.rg }}
          namespace: ${{ steps.baby_vars.outputs.namespace }}
          keyname: RootManageSharedAccessKey
        with:
          cmd: az eventhubs namespace authorization-rule keys list -g $rg --namespace-name $namespace --name $keyname --query primaryKey | jq -r ''
      - name: set event hub key
        run: |
          cd $dir
          babylon config set-variable secrets eventhub.key ${{ steps.hub.outputs.result }}

      - name: create adt connector
        uses: babylon-actions/.github/actions/connector@main
        with:
          type: adt
          name: "Brewery Baby Connector ADT test"

      - name: create connector storage
        uses: babylon-actions/.github/actions/connector@main
        with:
          type: storage
          name: "Brewery Baby connector STORAGE"

      - name: create dataset adt
        uses: babylon-actions/.github/actions/dataset@main
        with:
          type: adt
          name: "Brewery Baby dataset ADT"

      - name: Retrieve babylon variables
        id: baby_wpi
        run: |
          cd $dir
          echo "wpi=$(babylon config get-variable deploy 'webapp_principal_id')" >> $GITHUB_OUTPUT

      - name: add adt permission to webapp
        uses: babylon-actions/.github/actions/permission@main
        with:
          pi: ${{ steps.baby_wpi.outputs.wpi }}
          pt: App
          ri: Microsoft.DigitalTwins/digitalTwinsInstances
          rt: App

      - name: create solution brewery
        uses: babylon-actions/.github/actions/solution@main

      - name: create workspace brewery
        uses: babylon-actions/.github/actions/workspace@main
        with:
          name: Brewery Baby Workspace
          email: $email

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
        csm_acr_registry_name: source
        acr_registry_name: destination
    deploy file:
        csm_simulator_repository: source
        simulator_repository: destination
        simulator_version: <x.y.z>

>run

```bash
babylon azure acr pull -r <source>.azurecr.io
babylon azure acr push -r <dest>.azurecr.io
```

</br>

## solution object
---

>configuration

    deploy file:
        organization_id: O-gZYpnd27G7
        api_url: https://dev.api.cosmotech.com/v2
        simulator_repository: brewery_simulator
        simulator_version: 0.0.26

    platform file:
        api_url: "https://dev.api.cosmotech.com/v2"
        api_scope: "http://dev.api.cosmotech.com/.default"
        azure_subscription: <Subscription Id>
        azure_tenant_id: <Tenant Id>

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

>configuration (example)

    deploy_file:
        organization_id: <ORGANIZATION_ID>
        workspace_key: <WORKSPACE_KEY>

    platform file:
        resource_group_name: phoenixdev
        resources_location: westus2

>run

```bash
babylon azure adt instance create -s
babylon azure adt model upload dtdl/
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

>configuration (example)

    deploy_file:
        organization_id: <ORGANIZATION_ID>
        workspace_key: <WORKSPACE_KEY>

    platform file:
        adx_cluster_name: phoenixdev
        adx_cluster_object_id: <PRINCIPAL_ID>

>run

```bash
babylon azure adx database create -s
babylon azure adx script run-folder adx
```

</br>


## Power bi
---

>configuration

    platform file:
        azure_powerbi_group_id: <AZURE_GROUP_ID>


</br>

## Web app
---
Link: https://cosmo-tech.github.io/Babylon-End-User-Doc/2.0.0/commands/webapp_deploy/


>configuration

    deploy file:
        deployment_name: babybrewery
        webapp_location: westus2
        webapp_repository: <GITHUB_REPOSITORY_URL>
        webapp_repository_branch: main

    platform file:
        azure_powerbi_group_id: <AZURE_GROUP_ID>


>manual operation

    - create PAT with repo and workflow scopes
    - create a new repository (empty)

    help : https://cosmo-tech.github.io/Babylon-End-User-Doc/2.1.0/commands/webapp_deploy/

>run

```bash
babylon config set-variable secrets github.token <GITHUB_TOKEN>

git clone git@github.com:<GITHUB_REPOSITORY_URL> webapp_src; cd webapp_src
git remote add upstream git@github.com:Cosmo-Tech/azure-sample-webapp.git
git remote set-url upstream --push "NO"
git fetch upstream
git checkout -b main upstream v<x.y.z>-brewery
sudo rm -r .github/
git add .; git commit -m 'first commit'; git push origin main -f; cd ..
babylon webapp deploy
```

</br>

```bash
.
├── .payload_templates
│   ├── api
│   │   ├── connector.adt.yaml
│   │   ├── connector.storage.yaml
│   │   ├── dataset.adt.yaml
│   │   ├── dataset.storage.yaml
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
├── powerbi
│   └── Brewery_report.pbix
├── README.md
└── terraform_cloud
    ├── tfc_variables_create.yaml
    └── tfc_workspace_create.yaml
```