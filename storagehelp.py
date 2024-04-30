# Helper to find all accessible subscriptions and storage accounts and change public network access from 'Enabled from all networks' to 'Enabled from selected virtual networks and IP addresses'

from azure.mgmt.storage import StorageManagementClient
from azure.identity import InteractiveBrowserCredential
from azure.mgmt.storage.models import NetworkRuleSet, DefaultAction
from azure.mgmt.resource import SubscriptionClient
from azure.storage.blob import BlobServiceClient
from datetime import datetime, timedelta

class Storage:
    def __init__(self, exclusive_subscription_list = None, exclusive_storage_accounts_to_be_fixed = None):
        self.credential = InteractiveBrowserCredential()
        self.subscription_client = SubscriptionClient(self.credential)
        self.exclusive_subscription_list = exclusive_subscription_list
        self.exclusive_storage_accounts_to_be_fixed = exclusive_storage_accounts_to_be_fixed

    def get_subscriptions(self):
        if self.exclusive_subscription_list and len(self.exclusive_subscription_list) > 0:
            return self.exclusive_subscription_list
        return [subscription.subscription_id for subscription in self.subscription_client.subscriptions.list()]

    def get_storage_accounts(self, storage_client):
        result = []
        storage_accounts = storage_client.storage_accounts.list()
        if self.exclusive_storage_accounts_to_be_fixed and len(self.exclusive_storage_accounts_to_be_fixed) > 0:
            for account in storage_accounts:
                if account.name in self.exclusive_storage_accounts_to_be_fixed:
                    result += [account]
        else:
            result = storage_accounts
        return result

    def deny_public_access_for_storage_accounts_in_subscriptions(self):
        for subscription_id in self.get_subscriptions():
            print(subscription_id)
            storage_client = StorageManagementClient(self.credential, subscription_id)
            self.deny_public_access(storage_client)

    def set_access_to_deny(self, storage_account, storage_client):
        network_rule_set = NetworkRuleSet(default_action=DefaultAction.deny)
        update_result = storage_client.storage_accounts.update(
            resource_group_name=storage_account.id.split('/')[4],
            account_name=storage_account.name,
            parameters={
                'network_rule_set': network_rule_set
            }
        )
        print(f"Update called for {storage_account.name}, response status: {update_result.provisioning_state}")

    def deny_public_access(self, storage_client):
        try:
            for account in self.get_storage_accounts(storage_client):
                self.set_access_to_deny(account, storage_client)
        except Exception as e:
            print(f"Error occurred: {e}")

    def find_unused_storage_accounts_in_all_subscriptions(self):
        for subscription_id in self.get_subscriptions():
            print(subscription_id)
            storage_client = StorageManagementClient(self.credential, subscription_id)
            for account in self.get_storage_accounts(storage_client):
                try:
                    self.find_if_storage_account_accessdate_is_old(account.name)
                except Exception as e:
                    raise e

    # Roles needed : Storage Blob Data Contributor or Storage Blob Data Reader
    def find_if_storage_account_accessdate_is_old(self, storage_account_name):
        print(storage_account_name)
        oldest_valid_date = datetime.utcnow() - timedelta(days=365)

        blob_service_client = BlobServiceClient(account_url=f"https://{storage_account_name}.blob.core.windows.net", credential=self.credential)
        container_list = blob_service_client.list_containers()
        for container in container_list:
            container_client = blob_service_client.get_container_client(container.name)
            for blob in container_client.list_blobs():
                blob_client = container_client.get_blob_client(blob)
                blob_properties = blob_client.get_blob_properties()
                if hasattr(blob_properties, 'last_accessed_on') and blob_properties.last_accessed_on:
                    if blob_properties.last_accessed_on < oldest_valid_date:
                        print(f"Blob {blob.name} in {container.name} was last accessed on {blob_properties.last_accessed_on}")


exclusive_subscription_list = ['0009fc4d-e310-4e40-8e63-c48a23e9cdc1']
exclusive_storage_accounts_to_be_fixed = ['agtemplatestorage']

# to process all subscriptions and storage accounts, give exclusive array as []
# exclusive_subscription_list = []
# exclusive_storage_accounts_to_be_fixed = []

a = Storage(exclusive_subscription_list, exclusive_storage_accounts_to_be_fixed)
a.deny_public_access_for_storage_accounts_in_subscriptions()
# a.find_unused_storage_accounts_in_all_subscriptions()


