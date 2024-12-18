from dotenv import find_dotenv, load_dotenv
from proxmoxer import ProxmoxAPI
import time
import os
from enum import Enum
from faker import Faker
import random


class Delay(Enum):
    SHORT, MIDDLE, LONG = 0.5, 1, 1.5


class PVE:
    def __init__(self):
        """a class used for initializing proxmox-ve session

        Args:
            None

        Return:
            self: a session that initiated by
        """
        load_dotenv(find_dotenv(), override=True)
        if all(
            os.getenv(req_env)
            for req_env in [
                "PROXMOX_HOST",
                "PROXMOX_USER",
                "PROXMOX_PASS",
                "PROXMOX_NODE",
                "PROXMOX_TEMPLATE",
                "BL_VMIDS",
                "BL_NAMES",
            ]
        ):
            self.prox = ProxmoxAPI(
                host=os.getenv("PROXMOX_HOST"),
                user=os.getenv("PROXMOX_USER"),
                password=os.getenv("PROXMOX_PASS"),
                verify_ssl=False,
            )
            self.node = os.getenv("PROXMOX_NODE")
            self.blacklist_vmids = os.getenv("BL_VMIDS").split(",")
            self.blacklist_names = os.getenv("BL_NAMES").split(",")
            self.template = os.getenv("PROXMOX_TEMPLATE")
            print("::: Loaded all required env variables...")

    def _get_vmids(self):
        if self.prox:
            vmids = [vm["vmid"] for vm in self.prox.nodes(self.node).qemu.get()]
            return vmids

    # return template vm-id
    def _search_vmid(self, name):
        target_id = [
            vm["vmid"]
            for vm in self.prox.nodes(self.node).qemu.get()
            if vm["name"] == name
        ]
        if target_id:
            return target_id[0]
        else:
            return False

    # generate new vmid
    def _gen_vmid(self):
        if self.blacklist_vmids:
            if vmids := [
                vm["vmid"] for vm in self.prox.nodes(self.node).qemu.get()
            ]:
                gen_id = max(vmids) + 1
                while gen_id in self.blacklist_vmids:
                    gen_id += 1

                return gen_id
            else:
                return 100  # initial vmid value
        else:
            return False

    # start, stop and delete all VMs except VMs having blacklist_names
    def action_vms(self, action):
        if self.blacklist_names:
            blacklist_names_ids = [
                self._search_vmid(x) for x in self.blacklist_names
            ]

            for vm in self.prox.nodes(self.node).qemu.get():
                if vm["vmid"] not in blacklist_names_ids:
                    print(f"{action.title()} {vm['vmid']} ...")
                    if action in ("start", "stop"):
                        self.prox.nodes(self.node).qemu(vm["vmid"]).status.post(
                            action
                        )

                    elif action == "delete":
                        self.prox.nodes(self.node).qemu(vm["vmid"]).delete()
                    time.sleep(Delay.SHORT.value)

    def create_clone(self, num=0, pool="kubeops"):
        fake = Faker()
        fake_name = fake.name().split(" ")[0]
        target_id = self._search_vmid(self.template)
        for i in range(1, num + 1):
            new_id = self._gen_vmid()
            vmname = f"rke2-{fake_name}-{i}"

            if target_id and new_id:
                self.prox.nodes(self.node).qemu(target_id).clone.create(
                    newid=new_id, name=vmname, pool=pool
                )

    def _get_vmip(self, id):
        if (
            vmip := self.prox.nodes(self.node)
            .qemu(id)
            .agent.get("network-get-interfaces")["result"][1]["ip-addresses"][
                0
            ]["ip-address"]
        ):
            return vmip
        else:
            return False

    def status_vm(self, status="running"):
        if self.prox:
            running_vms = []
            if status in ("running", "stopped"):
                for vm in self.prox.nodes(self.node).qemu.get():
                    if (
                        vm["status"] == status
                        and vm["vmid"] not in self.blacklist_vmids
                    ):
                        running_vms.append(
                            f"{vm['name']}({vm['vmid']}) is {status}"
                        )

            return running_vms


if __name__ == "__main__":
    if p := PVE():
        p._get_vms()
