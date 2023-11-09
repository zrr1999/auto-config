import json
import os
import typer
from sys import stdout
from typing import Sequence
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import (
    TencentCloudSDKException,
)
from tencentcloud.dnspod.v20210323 import dnspod_client, models
from loguru import logger


class Client:
    def __init__(self, domain: str, config_path="~/.config/autoconfig") -> None:
        config_path = os.path.expanduser(config_path)
        config_path = os.path.expandvars(config_path)
        secret_path = f"{config_path}/token/tencentcloud.json"
        if os.path.exists(secret_path):
            with open(secret_path) as f:
                token: dict = json.load(f)
        else:
            secret_id = typer.prompt("Please input your tencentcloud secret id")
            secret_key = typer.prompt("Please input your tencentcloud secret key")
            token = {
                "TENCENTCLOUD_SECRET_ID": secret_id,
                "TENCENTCLOUD_SECRET_KEY": secret_key,
            }
            with open(secret_path, "w") as f:
                json.dump(token, f)
            logger.info(f"Secret saved to {secret_path}")

        cred = credential.Credential(
            token.get("TENCENTCLOUD_SECRET_ID"), token.get("TENCENTCLOUD_SECRET_KEY")
        )

        self.client = dnspod_client.DnspodClient(cred, "")
        self.domain = domain

    def list_record(self) -> list[models.RecordListItem]:
        try:
            req = models.DescribeRecordListRequest()
            params = {"Domain": self.domain}
            req.from_json_string(json.dumps(params))

            resp = self.client.DescribeRecordList(req)
            logger.debug(resp.to_json_string())
            assert isinstance(resp.RecordList, list)
            return resp.RecordList

        except TencentCloudSDKException as err:
            logger.warning(err)
            return []

    def create_record(self, sub_domain: str | list[str], value: str, record_type: str):
        sub_domain = (
            ".".join(sub_domain) if isinstance(sub_domain, list) else sub_domain
        )
        try:
            req = models.CreateRecordRequest()
            params = {
                "Domain": self.domain,
                "SubDomain": sub_domain,
                "RecordType": record_type,
                "RecordLine": "默认",
                "Value": value,
            }
            req.from_json_string(json.dumps(params))

            resp = self.client.CreateRecord(req)
            logger.debug(resp.to_json_string())

        except TencentCloudSDKException as err:
            logger.warning(err)

    def modify_record(
        self, record_id: str, sub_domain: str | list[str], value: str, record_type: str
    ):
        sub_domain = (
            ".".join(sub_domain) if isinstance(sub_domain, list) else sub_domain
        )
        try:
            req = models.ModifyRecordRequest()
            params = {
                "RecordId": record_id,
                "Domain": self.domain,
                "SubDomain": sub_domain,
                "RecordType": record_type,
                "RecordLine": "默认",
                "Value": value,
            }
            req.from_json_string(json.dumps(params))

            resp = self.client.ModifyRecord(req)
            logger.debug(resp.to_json_string())

        except TencentCloudSDKException as err:
            logger.warning(f"{sub_domain}: {err}")

    def update_records(self, new_records: Sequence[tuple[str, str, str]]):
        records = self.list_record()
        record_ids = {}
        for record in records:
            match json.loads(record.to_json_string()):
                case {
                    "RecordId": RecordId,
                    "Name": Name,
                    "Type": Type,
                    **kwargs,
                }:
                    record_ids[Name] = RecordId
                    logger.debug(f"Type: {Type}, Name: {Name}, {kwargs}")
        for record in new_records:
            name, record_type, value = record
            if (record_id := record_ids.get(name)) is None:
                self.create_record(name, value, record_type)
            else:
                self.modify_record(record_id, name, value, record_type)


def update_records_from_json(
    path: str = "~/.config/autoconfig/dns.json", *, log_level="INFO"
):
    logger.remove()
    logger.add(stdout, level=log_level)
    path = os.path.expanduser(path)
    path = os.path.expandvars(path)
    with open(path) as f:
        config = json.load(f)
    client = Client(config["domain"])
    client.update_records(config["records"])
