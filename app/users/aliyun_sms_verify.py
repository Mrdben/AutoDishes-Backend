# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.
import os
import sys
import json

from alibabacloud_dypnsapi20170525.client import Client as Dypnsapi20170525Client
from alibabacloud_credentials.client import Client as CredentialClient
from alibabacloud_credentials.models import Config as CredentialConfig
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dypnsapi20170525 import models as dypnsapi_20170525_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient

class Aliyun_SMS_Verify:
    def __init__(self):
        pass
        
    Template_Map = {
        'register': '100001',
        'password': '100003',
        'phone': '100002',
        'forgot': '100003',
        'delete': '100001'
    }
    
    @staticmethod
    def create_client() -> Dypnsapi20170525Client:
        """
        使用凭据初始化账号Client
        @return: Client
        @throws Exception
        """
        # 工程代码建议使用更安全的无AK方式，凭据配置方式请参见：https://help.aliyun.com/document_detail/378659.html。
        credential = CredentialClient()
        config = open_api_models.Config(
            credential=credential
        )
        # Endpoint 请参考 https://api.aliyun.com/product/Dypnsapi
        config.endpoint = f'dypnsapi.aliyuncs.com'
        return Dypnsapi20170525Client(config)

    @staticmethod
    def send_request(
        phone_number: str,
        scene: str
    ) -> dict:
        client = Aliyun_SMS_Verify.create_client()
        template_code = Aliyun_SMS_Verify.convert_template(scene)
        send_sms_verify_code_request = dypnsapi_20170525_models.SendSmsVerifyCodeRequest(
            phone_number = phone_number,
            sign_name = '速通互联验证码',
            template_code = template_code,
            template_param = '{"code":"##code##","min":"5"}',
            code_length = 6,
            valid_time = 300,
            interval = 60,
            code_type = 1,
            return_verify_code = False
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = client.send_sms_verify_code_with_options(send_sms_verify_code_request, runtime)
            return {"success": resp.body.success,
                    "message": resp.body.message,
                    "code": 200}
        except Exception as error:
            return {"success": False,
                    "message": (getattr(error, 'data', None) or {}).get("Message", None),
                    "code": getattr(error, 'statusCode', 400)}
            
    @staticmethod
    def verfiy_request(
        phone_number: str,
        verify_code: str
    ) -> dict:
        client = Aliyun_SMS_Verify.create_client()
        check_sms_verify_code_request = dypnsapi_20170525_models.CheckSmsVerifyCodeRequest(
            phone_number = phone_number,
            verify_code = verify_code
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = client.check_sms_verify_code_with_options(check_sms_verify_code_request, runtime)
            return {"success": resp.body.success,
                    "message": resp.body.message,
                    "code": 200}            
        except Exception as error:
            return {"success": False,
                    "message": (getattr(error, 'data', None) or {}).get("Message", None),
                    "code": getattr(error, 'statusCode', 400)}

    @staticmethod
    def convert_template(scene: str) -> str:
        return Aliyun_SMS_Verify.Template_Map.get(scene, '100001')
    
if __name__ == '__main__':
    #print(Aliyun_SMS_Verify.send_request('13910356629','phone'))
    print(Aliyun_SMS_Verify.verfiy_request('13910356629','089567'))
