from tenable.nessus import Nessus
import json
import requests
import os
from getpass import getuser, getpass
from subprocess import run
from typing import Optional
from pprint import pprint
def parse_config(file: str) -> dict:
    with open(file, encoding='utf=8') as file:
        return json.loads(file.read())

class NessusAPI():
    def __init__(self,
                 file: Optional[str] = None,
                 host: Optional[str] = None,
                 port: Optional[int] = None,
                 tokens: Optional[dict[str,str]] = None,
                 credentials: Optional[dict[str,str]] = None,
                 initialize: bool = False) -> None:
        config = None
        if file:
            config = parse_config(file)
            server_config = config['server']
            host = server_config['host']
            port = server_config['port']
            if not tokens:
                tokens = server_config.get('tokens')
            if not credentials:
                credentials = server_config.get('credentials')
        if tokens:
            self.Nessus = self.__login_token(host, port, tokens)
        elif credentials:
            self.Nessus = self.__login_user_passwd(host, port, credentials)
        else:
            raise KeyError("Credentials or Token not provided or missing in config file.")

        if config and initialize:    
            self._setup_import_policies(config.get('policies'))
            self._setup_scans(config.get('scans'))

    def logout(self):
        self.Nessus._deauthenticate()

    def __login_user_passwd(self, host: str, port: int, credentials: dict[str,str]) -> Nessus:
        return Nessus(
            url = f'https://{host}:{port}',
            username = (getuser("Username: ") if credentials.get('username', '*') == "*" else credentials['username']),
            password = (getpass("Password: ") if credentials.get('password', '*') == "*" else credentials['password'])
        )

    def __login_token(self, host: str, port: int, tokens: dict[str,str]) -> Nessus:
        raise NotImplementedError()

    def _setup_scans(self, scans: list[dict]) -> None:
        for scan in scans:
            self.create_scan(scan)

    def _setup_import_policies(self, policies: list[dict]) -> None:
        for policy in policies:
            self.import_policy(policy)

    def _get_policy_id_by_name(self, name: str) -> dict:
        policies = self.Nessus.policies.list()
        for p in policies:
            if p['name'] == name:
                # template_uuid, name, and id are the primary keys
                return p, 'policy'
        builtin_policies = self.Nessus.editor.template_list('policy')
        for p in builtin_policies:
            if p['name'] in name or p['title'] in name:
                # template_uuid, name, and id are the primary keys
                return p, 'template'

    def list_folders(self) -> list[dict]:
        return self.Nessus.folders.list()

    def list_scans(self, folder: Optional[int] = None) -> dict:
        return self.Nessus.scans.list(folder)

    def list_policies(self) -> dict:
        return self.Nessus.policies.list()


    def create_folder(self, name: str) -> int:
        return self.Nessus.folders.create(name)

    def create_scan(self, settings: dict) -> dict:
        scan_policy, scan_type = self._get_policy_id_by_name(settings['policy'])
        scan_folders = {folder['name']:folder['id'] for folder in self.list_folders()}
        scan_folder_id = scan_folders.get(settings['folder'])
        if not scan_folder_id:
            scan_folder_id = self.create_folder(settings['folder'])
        
        if scan_type == 'template':
            return self.Nessus.scans.create(uuid = scan_policy['uuid'], settings = {
                'name': settings['name'],
                'enabled': settings.get('enabled', False),
                'text_targets': ', '.join(settings['targets']),
                'folder_id': scan_folder_id,
            })

        elif scan_type == 'policy':
            return self.Nessus.scans.create(uuid = scan_policy['template_uuid'], settings = {
                'name': settings['name'],
                'enabled': settings.get('enabled', False),
                'text_targets': ', '.join(settings['targets']),
                'policy_id': scan_policy['id'],
                'folder_id': scan_folder_id,
            })
        else:
            raise ValueError(f"{scan_type}, {scan_policy}")

    def add_credentials(self, uuid: str, id: int, credentials: dict) -> None:
        response = requests.put(f'{self.Nessus._url}/policies/{id}', verify=False,
        json={"uuid":uuid,  **credentials},
        headers={"X-Cookie": self.Nessus._session.headers['X-Cookie'], "Content-Type": "application/json"})
        if response.status_code != 200:
            response.raise_for_status()

    def import_policy(self, policy: dict) -> dict:
        def __import_sshkeys(credentials: dict) -> dict:
            try:
                for idx, ssh_creds in enumerate(credentials["Host"]["SSH"]):
                    if ssh_creds['auth_method'] == 'public_key':
                        key_path = ssh_creds['private_key'].split(':')
                        if len(key_path) == 2: # scp key if not local
                            key_path = f"/tmp/{key_path[1]}_{ssh_creds['username']}_id_rsa"
                            cmd_result = run(f"echo '{ssh_creds['password']}' | scp -q -o StrictHostKeyChecking=no {ssh_creds['username']}@{ssh_creds['private_key']} {key_path}")
                            del ssh_creds['password'] # delete initial login password after use
                            os.remove(key_path) # delete downloaded key after use
                            if cmd_result.returncode:
                                raise OSError("Could not download SSH Private Key from ")
                        else:
                            key_path = key_path[0]
                        with open(key_path, 'rb') as keyfile:
                            credentials["Host"]["SSH"][idx]["private_key"] = self.Nessus.files.upload(keyfile)
            except KeyError: 
                pass
            return { "credentials": { "add": credentials } }

        imported_policy_id = None
        with open(policy['file'], 'rb') as policyfile:
            imported_policy_id = self.Nessus.policies.import_policy(policyfile)['id']
        imported_policy = self.Nessus.policies.details(imported_policy_id)
        imported_policy['settings']['name'] = policy['name']
        self.Nessus.policies.edit(imported_policy_id, **imported_policy)
        # import credentials last
        credentials = __import_sshkeys(policy['credentials'])
        self.add_credentials(imported_policy['uuid'], imported_policy_id, credentials)
        return imported_policy
    
    def run_scan(scan_name: str, folder_name: Optional[str] = None) -> None:
        pass

    def run_all_scans() -> None:
        pass

    def stop_scan(scan_name: str, folder_name: Optional[str] = None) -> None:
        pass

    def stop_all_scans() -> None:
        pass