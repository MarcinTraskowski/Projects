# Google Cloud VM Configuration with Terraform & Ansible

We need to log in to Google Cloud:

```bash
gcloud auth login
gcloud init
```

Then, run the following script to set up environment variables:

```bash
. ./setup.sh
```
To create a new service account, assign policy bindings, and generate a service account key, run the following commands (these variables are defined in setup.sh):

```bash
gcloud iam service-accounts create $SERVICE_NAME
gcloud projects add-iam-policy-binding $PROJECT_ID --member serviceAccount:$SERVICE_NAME@$PROJECT_ID.iam.gserviceaccount.com --role roles/editor
gcloud iam service-accounts keys create ./$SERVICE_NAME.json --iam-account $SERVICE_NAME@$PROJECT_ID.iam.gserviceaccount.com
```

Then, execute the following commands sequentially:

```bash
. metadata_script.sh
terraform apply
python3 parse-tf-state.py
ansible-playbook -i hosts install_packages.yml
ansible-playbook -i hosts config_ssh.yml
ansible-playbook -i hosts nfs.yml
```

These commands perform the following tasks in sequence:
- Generate SSH keys
- Provision virtual machines (VMs)
- Extract IP addresses from the `terraform.tfstate` file
- Install required packages
- Establish SSH connections between VMs
- Set up an NFS (Network File System) for a shared home directory